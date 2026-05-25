"""Async turn orchestrator: classify, narrate-before-act, escalate when confidence is low.

`handle_turn` is the single entry point the ElevenLabs Conversation callbacks
(or a local scripted runner) invoke once per user turn. It enforces the prototype
headline property in code, not just prose: when an intent requires narration,
the `narration_emitted` event is written to the per-turn log before any tool
is invoked. Escalation is a separate branch that emits a structured
HandoffContext and skips narration entirely.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import httpx

from src.intents import Intent, classify, should_escalate
from src.latency import StageTimer
from src.logging_setup import log_turn
from src.tools import Cart, DeliveryETA, Order, ToolResult, fetch_cart, fetch_delivery_eta, fetch_order

# Graceful response when a tool call fails. Kept here (not in intents.json)
# because it is a runtime fallback, not a classifier output.
_TOOL_FAILURE_RESPONSE: str = (
    "Hmm, deu um probleminha aqui pra consultar isso pra você agora. "
    "Quer que eu te transfira pra um atendente?"
)


@dataclass(frozen=True)
class UserTurn:
    """One inbound turn from the user. `confidence` is the ASR confidence if available."""

    transcript: str
    confidence: float | None = None
    turn_id: str = ""


@dataclass(frozen=True)
class AgentTurn:
    """One outbound turn from the agent, with side-channel metadata for the log."""

    text: str
    escalated: bool = False
    tool_calls: list[str] = field(default_factory=list)
    latency_ms: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class HandoffContext:
    """Structured bundle delivered to the named human (default: Camila) on escalation."""

    conversation_history: list[dict]
    unresolved_intent: str
    reason: str
    to: str = "Camila"

    def to_dict(self) -> dict:
        """Plain-dict view so `log_turn` can serialize without custom encoders."""
        return asdict(self)


# Tool name -> async callable. Kept as a module constant so tests can monkeypatch.
_TOOL_REGISTRY = {
    "fetch_order": fetch_order,
    "fetch_delivery_eta": fetch_delivery_eta,
    "fetch_cart": fetch_cart,
}

# Tools that require at least one argument. Empty `tool_args` against these
# is reported as `missing_args` without dialing the network.
_TOOLS_REQUIRING_ARGS: set[str] = {"fetch_order", "fetch_delivery_eta", "fetch_cart"}


async def _call_tool(name: str | None, args: dict) -> ToolResult:
    """Dispatch one tool by name with extracted args. Network errors after retry
    surface as `transport_failed_after_retries`; non-2xx responses as `http_<code>`.
    """
    if name is None:
        return ToolResult(ok=False, error="no_tool_for_intent")

    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return ToolResult(ok=False, error=f"unknown_tool:{name}")

    if name in _TOOLS_REQUIRING_ARGS and not args:
        return ToolResult(ok=False, error="missing_args")

    try:
        data = await fn(**args)
    except httpx.HTTPStatusError as exc:
        return ToolResult(ok=False, error=f"http_{exc.response.status_code}")
    except httpx.TransportError:
        return ToolResult(ok=False, error="transport_failed_after_retries")
    except Exception as exc:  # noqa: BLE001  surface unexpected failures as structured ToolResult
        return ToolResult(ok=False, error=f"{type(exc).__name__}:{exc}")
    return ToolResult(ok=True, data=data)


def _summarize_tool_data(name: str, data: object) -> str | None:
    """Return a short PII-safe summary string for the `tool_returned` log event."""
    if isinstance(data, Order):
        tail = data.order_id[-4:] if data.order_id else "????"
        return f"order ***{tail} status={data.status}"
    if isinstance(data, DeliveryETA):
        return f"eta '{data.eta_text}'"
    if isinstance(data, Cart):
        return f"{len(data.items)} items, promo {data.promo_code}"
    return None


def _format_brl(value: float) -> str:
    """Format a float as a Brazilian-real amount for spoken-style text."""
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _response_from_tool_result(intent: Intent, result: ToolResult) -> str:
    """Build a customer-facing response from real tool output instead of a static template."""
    if not result.ok:
        if result.error == "missing_args":
            if intent.name == "order_status":
                return "Claro, eu consulto pra você. Me manda o número do pedido?"
            return "Consigo te ajudar, sim. Só preciso de mais uma informação pra consultar aqui."
        if result.error == "http_404":
            return (
                "Não encontrei esse pedido aqui. Confere o número pra mim? "
                "Se estiver tudo certo e mesmo assim não aparecer, eu te passo pra Camila agora."
            )
        return _TOOL_FAILURE_RESPONSE

    data = result.data
    if isinstance(data, Order):
        tail = data.order_id[-4:]
        total = _format_brl(data.total_brl)
        status_map = {
            "out_for_delivery": (
                f"Boa notícia: o pedido final {tail}, no valor de {total}, já saiu pra entrega. "
                "Quer que eu te avise quando o entregador estiver perto?"
            ),
            "processing": (
                f"Achei o pedido final {tail}. Ele ainda está em separação, no valor de {total}. "
                "Assim que sair pra entrega, eu posso te avisar por aqui."
            ),
            "delivered": (
                f"O pedido final {tail} aparece como entregue. "
                "Se você não recebeu, me fala que eu já te passo pra uma pessoa conferir isso com prioridade."
            ),
            "delayed": (
                f"O pedido final {tail} está com atraso registrado. Sinto muito por isso. "
                "Posso te transferir pra Camila agora com esse contexto pra ela verificar a melhor solução."
            ),
        }
        return status_map.get(
            data.status,
            f"Achei o pedido final {tail}. O status atual é {data.status}. Quer que eu te passe pra um atendente conferir os detalhes?",
        )

    if isinstance(data, DeliveryETA):
        if data.eta_text.lower().startswith("já entregue"):
            return "Esse pedido aparece como já entregue. Se não chegou aí pra você, eu te passo pra Camila conferir agora."
        return f"A previsão que aparece aqui é: {data.eta_text}. Quer que eu te avise se essa previsão mudar?"

    if isinstance(data, Cart):
        if data.items:
            first = data.items[0].get("name", "o primeiro item")
            more = len(data.items) - 1
            item_text = first if more == 0 else f"{first} e mais {more} item" + ("s" if more > 1 else "")
        else:
            item_text = "os itens do seu carrinho"
        if data.promo_code and data.promo_discount_pct:
            return (
                f"Ainda encontrei {item_text} no seu carrinho. "
                f"O cupom {data.promo_code} dá {data.promo_discount_pct}% de desconto. "
                "Quer que eu te mande o link pra finalizar?"
            )
        return f"Ainda encontrei {item_text} no seu carrinho. Quer que eu te mande o link pra finalizar?"

    return intent.response_template


def _escalation_reason(intent: Intent) -> str:
    """`low_confidence` for fallback / sub-threshold matches, `user_request` otherwise."""
    if intent.name == "fallback":
        return "low_confidence"
    if intent.name == "escalation_request":
        return "user_request"
    if intent.confidence < intent.threshold:
        return "low_confidence"
    return "user_request"


async def handle_turn(turn: UserTurn, history: list[dict] | None = None) -> AgentTurn:
    """Drive one turn end-to-end: classify, narrate, tool-call, respond, or escalate."""
    turn_id = turn.turn_id
    latency_ms: dict[str, float] = {}

    log_turn({"turn_id": turn_id, "event": "turn_start", "transcript": turn.transcript})

    with StageTimer("classify") as classify_timer:
        intent = classify(turn.transcript)
    latency_ms["classify"] = classify_timer.elapsed_seconds * 1000.0

    log_turn(
        {
            "turn_id": turn_id,
            "event": "classified",
            "intent": intent.name,
            "confidence": round(intent.confidence, 3),
            "threshold": intent.threshold,
            "tool": intent.tool,
            "tool_args": intent.tool_args,
        }
    )

    if should_escalate(intent):
        handoff = HandoffContext(
            conversation_history=history or [],
            unresolved_intent=intent.name,
            reason=_escalation_reason(intent),
        )
        log_turn(
            {
                "turn_id": turn_id,
                "event": "escalated",
                "handoff": handoff.to_dict(),
            }
        )
        agent_turn = AgentTurn(
            text=intent.response_template,
            escalated=True,
            tool_calls=[],
            latency_ms=latency_ms,
        )
        log_turn(
            {
                "turn_id": turn_id,
                "event": "turn_complete",
                "escalated": True,
                "latency_ms": latency_ms,
            }
        )
        return agent_turn

    if intent.narration_required and intent.narration_text:
        log_turn(
            {
                "turn_id": turn_id,
                "event": "narration_emitted",
                "text": intent.narration_text,
            }
        )

    log_turn(
        {
            "turn_id": turn_id,
            "event": "tool_called",
            "tool": intent.tool,
            "tool_args": intent.tool_args,
        }
    )
    with StageTimer("tool") as tool_timer:
        result = await _call_tool(intent.tool, intent.tool_args)
    latency_ms["tool"] = tool_timer.elapsed_seconds * 1000.0

    log_turn(
        {
            "turn_id": turn_id,
            "event": "tool_returned",
            "tool": intent.tool,
            "ok": result.ok,
            "error": result.error,
            "data_summary": _summarize_tool_data(intent.tool, result.data) if result.ok else None,
        }
    )

    # Build the customer-facing answer from the actual tool output. This keeps
    # the demo from becoming "tool-call theater": the mock backend materially
    # changes what the agent says.
    response_text = _response_from_tool_result(intent, result)

    log_turn(
        {
            "turn_id": turn_id,
            "event": "agent_response",
            "agent_response": response_text,
        }
    )

    tool_calls = [intent.tool] if intent.tool else []
    agent_turn = AgentTurn(
        text=response_text,
        escalated=False,
        tool_calls=tool_calls,
        latency_ms=latency_ms,
    )
    log_turn(
        {
            "turn_id": turn_id,
            "event": "turn_complete",
            "escalated": False,
            "latency_ms": latency_ms,
        }
    )
    return agent_turn

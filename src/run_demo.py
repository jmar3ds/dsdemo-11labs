"""Live ElevenAgents runner: wires our orchestrator's tool layer to the ElevenLabs agent.

`python -m src.run_demo` opens an authenticated WebSocket session against the
cloud agent identified by `ELEVENLABS_AGENT_ID`, streams microphone audio
through `DefaultAudioInterface`, and exposes three client tools the agent can
call: `lookup_order`, `lookup_delivery_eta`, `lookup_cart`. Each tool bridges
to the existing async `tools.py` functions and returns plain dicts so the
WebSocket can JSON-serialize the result.

Transcripts and agent responses are logged via `logging_setup.log_turn` so the
event timeline in `outputs/eleven-agents_demo/events.jsonl` stays coherent with what the
local orchestrator's `handle_turn` writes when invoked directly from tests.

The runner depends on `pyaudio` for live mic + speaker, but imports lazily so
unit tests and import-time verification work in environments without it.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Callable

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import ClientTools, Conversation

from src.config import REPO_ROOT
from src.latency import StageTimer
from src.logging_setup import log_turn
from src.tools import (
    Cart,
    DeliveryETA,
    Order,
    fetch_cart,
    fetch_delivery_eta,
    fetch_order,
)

# ElevenAgents client tool names. These must match the tool names declared on the
# agent in the ElevenLabs dashboard. The dashboard configuration provides the agent prompt + voice
# separately; the tool names are the contract.
TOOL_LOOKUP_ORDER: str = "lookup_order"
TOOL_LOOKUP_DELIVERY_ETA: str = "lookup_delivery_eta"
TOOL_LOOKUP_CART: str = "lookup_cart"

# Event names emitted by the cloud callbacks. Prefixed `eleven-agents_` so a reviewer
# scanning events.jsonl can distinguish cloud-truth transcripts from the
# orchestrator's own per-turn pipeline events (which use bare `agent_response`,
# `narration_emitted`, etc.).
EVENT_ELEVENAGENTS_USER_TRANSCRIPT: str = "eleven-agents_user_transcript"
EVENT_ELEVENAGENTS_AGENT_RESPONSE: str = "eleven-agents_agent_response"
EVENT_SESSION_START: str = "session_start"
EVENT_SESSION_END: str = "session_end"
EVENT_TOOL_BRIDGE_CALLED: str = "tool_bridge_called"
EVENT_TOOL_BRIDGE_RETURNED: str = "tool_bridge_returned"


@dataclass(frozen=True)
class DemoConfig:
    """Resolved environment configuration for the live demo run."""

    api_key: str
    agent_id: str
    requires_auth: bool = True


def load_demo_config() -> DemoConfig:
    """Read `.env` from the repo root and return a populated `DemoConfig`.

    Raises `RuntimeError` with a precise hint if either key is missing, so the
    failure is actionable rather than a deep stack trace from inside the SDK.
    """
    load_dotenv(dotenv_path=REPO_ROOT / ".env")
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    agent_id = os.environ.get("ELEVENLABS_AGENT_ID")
    if not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY missing from .env. "
            "Set it in dsdemo-11labs/.env before running `make demo`."
        )
    if not agent_id:
        raise RuntimeError(
            "ELEVENLABS_AGENT_ID missing from .env. "
            "Set it to the dashboard agent id (e.g. agent_xxxxxxxx)."
        )
    return DemoConfig(api_key=api_key, agent_id=agent_id)


def _to_jsonable(value: Any) -> Any:
    """Convert tools-layer dataclasses to plain dicts; pass other JSON-safe types through."""
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return value


async def _bridge_lookup_order(parameters: dict) -> dict:
    """ElevenAgents tool bridge: extract `order_id`, call `fetch_order`, return dict or error."""
    order_id = parameters.get("order_id")
    bridge_id = parameters.get("tool_call_id") or uuid.uuid4().hex
    log_turn(
        {
            "event": EVENT_TOOL_BRIDGE_CALLED,
            "tool": TOOL_LOOKUP_ORDER,
            "tool_call_id": bridge_id,
            "tool_args": {"order_id": order_id},
        }
    )
    if not order_id:
        result = {"ok": False, "error": "missing_args:order_id"}
    else:
        with StageTimer("tool_bridge_lookup_order") as timer:
            try:
                order: Order = await fetch_order(order_id=str(order_id))
                result = {"ok": True, "data": _to_jsonable(order)}
            except (
                Exception
            ) as exc:  # noqa: BLE001  surface tool errors as structured payload
                result = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
        log_turn(
            {
                "event": EVENT_TOOL_BRIDGE_RETURNED,
                "tool": TOOL_LOOKUP_ORDER,
                "tool_call_id": bridge_id,
                "ok": result.get("ok"),
                "latency_ms": {
                    "tool_bridge_lookup_order": timer.elapsed_seconds * 1000.0
                },
            }
        )
    return result


async def _bridge_lookup_delivery_eta(parameters: dict) -> dict:
    """ElevenAgents tool bridge: extract `order_id`, call `fetch_delivery_eta`."""
    order_id = parameters.get("order_id")
    bridge_id = parameters.get("tool_call_id") or uuid.uuid4().hex
    log_turn(
        {
            "event": EVENT_TOOL_BRIDGE_CALLED,
            "tool": TOOL_LOOKUP_DELIVERY_ETA,
            "tool_call_id": bridge_id,
            "tool_args": {"order_id": order_id},
        }
    )
    if not order_id:
        result = {"ok": False, "error": "missing_args:order_id"}
    else:
        with StageTimer("tool_bridge_lookup_delivery_eta") as timer:
            try:
                eta: DeliveryETA = await fetch_delivery_eta(order_id=str(order_id))
                result = {"ok": True, "data": _to_jsonable(eta)}
            except Exception as exc:  # noqa: BLE001  structured tool error
                result = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
        log_turn(
            {
                "event": EVENT_TOOL_BRIDGE_RETURNED,
                "tool": TOOL_LOOKUP_DELIVERY_ETA,
                "tool_call_id": bridge_id,
                "ok": result.get("ok"),
                "latency_ms": {
                    "tool_bridge_lookup_delivery_eta": timer.elapsed_seconds * 1000.0
                },
            }
        )
    return result


async def _bridge_lookup_cart(parameters: dict) -> dict:
    """ElevenAgents tool bridge: extract `customer_id`, call `fetch_cart`."""
    customer_id = parameters.get("customer_id")
    bridge_id = parameters.get("tool_call_id") or uuid.uuid4().hex
    log_turn(
        {
            "event": EVENT_TOOL_BRIDGE_CALLED,
            "tool": TOOL_LOOKUP_CART,
            "tool_call_id": bridge_id,
            "tool_args": {"customer_id": customer_id},
        }
    )
    if not customer_id:
        result = {"ok": False, "error": "missing_args:customer_id"}
    else:
        with StageTimer("tool_bridge_lookup_cart") as timer:
            try:
                cart: Cart = await fetch_cart(customer_id=str(customer_id))
                result = {"ok": True, "data": _to_jsonable(cart)}
            except Exception as exc:  # noqa: BLE001  structured tool error
                result = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
        log_turn(
            {
                "event": EVENT_TOOL_BRIDGE_RETURNED,
                "tool": TOOL_LOOKUP_CART,
                "tool_call_id": bridge_id,
                "ok": result.get("ok"),
                "latency_ms": {
                    "tool_bridge_lookup_cart": timer.elapsed_seconds * 1000.0
                },
            }
        )
    return result


@dataclass(frozen=True)
class CallbackHandles:
    """Bundle of callbacks the runner passes into the `Conversation` constructor."""

    on_user_transcript: Callable[[str], None]
    on_agent_response: Callable[[str], None]
    on_latency_measurement: Callable[[int], None]
    on_end_session: Callable[[], None]


def build_callbacks(session_id: str) -> CallbackHandles:
    """Construct the four runtime callbacks bound to a single session id."""

    def on_user_transcript(text: str) -> None:
        log_turn(
            {
                "session_id": session_id,
                "event": EVENT_ELEVENAGENTS_USER_TRANSCRIPT,
                "transcript": text,
            }
        )

    def on_agent_response(text: str) -> None:
        log_turn(
            {
                "session_id": session_id,
                "event": EVENT_ELEVENAGENTS_AGENT_RESPONSE,
                "agent_response": text,
            }
        )

    def on_latency_measurement(latency_ms: int) -> None:
        log_turn(
            {
                "session_id": session_id,
                "event": "eleven-agents_latency_measurement",
                "latency_ms": {"eleven-agents-agents_round_trip": float(latency_ms)},
            }
        )

    def on_end_session() -> None:
        log_turn(
            {
                "session_id": session_id,
                "event": EVENT_SESSION_END,
            }
        )

    return CallbackHandles(
        on_user_transcript=on_user_transcript,
        on_agent_response=on_agent_response,
        on_latency_measurement=on_latency_measurement,
        on_end_session=on_end_session,
    )


def build_client_tools() -> ClientTools:
    """Construct a `ClientTools` with the three Magalu bridge tools registered.

    The three handlers are async functions adapting our `tools.py` layer to
    the SDK's `(dict) -> Awaitable[Any]` contract. `is_async=True` instructs
    the SDK to `await` the handler rather than dispatching it to a thread.
    """
    client_tools = ClientTools()
    client_tools.register(TOOL_LOOKUP_ORDER, _bridge_lookup_order, is_async=True)
    client_tools.register(
        TOOL_LOOKUP_DELIVERY_ETA, _bridge_lookup_delivery_eta, is_async=True
    )
    client_tools.register(TOOL_LOOKUP_CART, _bridge_lookup_cart, is_async=True)
    return client_tools


def _build_audio_interface() -> Any:
    """Construct the default mic+speaker audio interface. Lazy import keeps
    headless environments (CI, import-time verification) from crashing when
    `pyaudio` is absent.
    """
    from elevenlabs.conversational_ai.default_audio_interface import (
        DefaultAudioInterface,
    )

    return DefaultAudioInterface()


@dataclass
class DemoSession:
    """In-process handle on the live ElevenAgents session. Holds the SDK Conversation
    plus the session id used to correlate log events.
    """

    session_id: str
    conversation: Conversation
    callbacks: CallbackHandles
    client_tools: ClientTools
    started: bool = field(default=False)


def build_session(config: DemoConfig) -> DemoSession:
    """Assemble the `Conversation` object with audio + client tools + callbacks.

    Does not start the WebSocket. `main` calls `conversation.start_session()`
    after wiring SIGINT.
    """
    session_id = uuid.uuid4().hex[:12]
    callbacks = build_callbacks(session_id)
    client_tools = build_client_tools()
    audio_interface = _build_audio_interface()
    client = ElevenLabs(api_key=config.api_key)
    conversation = Conversation(
        client=client,
        agent_id=config.agent_id,
        requires_auth=config.requires_auth,
        audio_interface=audio_interface,
        client_tools=client_tools,
        callback_agent_response=callbacks.on_agent_response,
        callback_user_transcript=callbacks.on_user_transcript,
        callback_latency_measurement=callbacks.on_latency_measurement,
        callback_end_session=callbacks.on_end_session,
    )
    return DemoSession(
        session_id=session_id,
        conversation=conversation,
        callbacks=callbacks,
        client_tools=client_tools,
    )


def _install_sigint_handler(session: DemoSession) -> None:
    """Translate Ctrl+C into a clean `end_session` so the SDK shuts down WS + audio.

    Without this, Ctrl+C raises `KeyboardInterrupt` inside `wait_for_session_end`
    and pyaudio sometimes leaves the mic stream hanging.
    """

    def _handler(signum: int, frame: Any) -> None:  # noqa: ARG001  signal API contract
        log_turn(
            {
                "session_id": session.session_id,
                "event": "sigint_received",
                "signal": signum,
            }
        )
        if session.started:
            session.conversation.end_session()

    signal.signal(signal.SIGINT, _handler)


def main() -> int:
    """Entry point invoked by `python -m src.run_demo` and the Makefile.

    Returns a process exit code so the shell sees 0 on a clean hangup and
    non-zero on a configuration failure.
    """
    try:
        config = load_demo_config()
    except RuntimeError as exc:
        print(f"[run_demo] configuration error: {exc}", file=sys.stderr)
        return 2

    session = build_session(config)
    _install_sigint_handler(session)

    log_turn(
        {
            "session_id": session.session_id,
            "event": EVENT_SESSION_START,
            "agent_id": config.agent_id,
        }
    )
    print(
        f"[run_demo] session {session.session_id} starting against agent {config.agent_id}"
    )
    print("[run_demo] speak after the connection opens. Ctrl+C to end.")

    session.conversation.start_session()
    session.started = True

    try:
        conversation_id = session.conversation.wait_for_session_end()
    except Exception as exc:  # noqa: BLE001  log and exit nonzero on transport failures
        log_turn(
            {
                "session_id": session.session_id,
                "event": "session_error",
                "error": f"{type(exc).__name__}:{exc}",
            }
        )
        return 1

    print(f"[run_demo] session ended. ElevenAgents conversation_id={conversation_id}")
    return 0


# Re-export the bridge functions so tests + tooling can import them directly
# without reaching into private names.
__all__ = [
    "DemoConfig",
    "DemoSession",
    "build_callbacks",
    "build_client_tools",
    "build_session",
    "load_demo_config",
    "main",
]


async def _smoke_invoke_all_bridges() -> dict:
    """Internal helper: call each tool bridge once against the running mock.

    Used by ad-hoc verification scripts; not part of the public API.
    """
    return {
        TOOL_LOOKUP_ORDER: await _bridge_lookup_order({"order_id": "54321"}),
        TOOL_LOOKUP_DELIVERY_ETA: await _bridge_lookup_delivery_eta(
            {"order_id": "54321"}
        ),
        TOOL_LOOKUP_CART: await _bridge_lookup_cart({"customer_id": "cust-demo"}),
    }


if __name__ == "__main__":
    raise SystemExit(main())

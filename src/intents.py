"""Rule-based intent classifier with confidence scoring against data/intents.json.

Maps a raw user transcript to an `Intent` carrying the matched intent name, a
deterministic 0.0-1.0 confidence score, the tool to invoke (if any), and the
narration / response templates. Confidence is `matched / total` keywords for
the intent, capped at 0.95 so rule-based matches never claim perfect certainty.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from src.config import REPO_ROOT

INTENTS_PATH: Path = REPO_ROOT / "data" / "intents.json"

# Cap for rule-based matches: a keyword classifier should never claim perfect
# certainty even on a full-keyword sweep. 0.95 leaves visible headroom for an
# ML upgrade later (Cat 11 of the Map, honest discipline).
_CONFIDENCE_CAP: float = 0.95

FALLBACK_RESPONSE: str = (
    "Hmm, não entendi muito bem o que você quis dizer. Pode me explicar de outro jeito? "
    "Ou se preferir, eu te passo pra um atendente humano agora mesmo."
)

# Contractions are expanded BEFORE accent stripping so the accented keys still
# match. Accent stripping after expansion handles "está" -> "esta" uniformly.
_CONTRACTIONS: dict[str, str] = {
    "tá": "está",
    "pra": "para",
    "pro": "para o",
    "cê": "você",
}

_INTENTS: dict[str, dict] | None = None

# Order IDs in PT-BR transcripts are spoken as digit runs; 4+ digits is the
# floor used by the PII redactor too, keeping the two layers aligned.
_ORDER_ID_RE: re.Pattern[str] = re.compile(r"\b\d{4,}\b")

# Phase 1 has no real customer identity layer; the ElevenAgents surface in Step 5
# will route customer IDs from the session metadata. Hardcoded placeholder
# is documented in ElevenAgents Step 4 deliverable B.
_DEMO_CUSTOMER_ID: str = "cust-demo"


@dataclass(frozen=True)
class Intent:
    """One classified intent: name, confidence, tool routing, narration, response, threshold."""

    name: str
    confidence: float
    tool: str | None
    response_template: str
    narration_required: bool
    narration_text: str | None
    threshold: float = 0.0
    tool_args: dict = field(default_factory=dict)


def _strip_accents(text: str) -> str:
    """Decompose to NFD and drop combining marks so accented chars match plain ones."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _normalize(text: str) -> str:
    """Lowercase, expand PT-BR contractions, then strip accents."""
    lowered = text.lower().strip()
    tokens = lowered.split()
    expanded = [_CONTRACTIONS.get(tok, tok) for tok in tokens]
    return _strip_accents(" ".join(expanded))


def load_intents() -> dict[str, dict]:
    """Read data/intents.json once and cache the result in `_INTENTS`."""
    global _INTENTS
    if _INTENTS is not None:
        return _INTENTS
    with INTENTS_PATH.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    _INTENTS = {
        name: spec for name, spec in payload.items() if not name.startswith("_")
    }
    return _INTENTS


def _extract_tool_args(intent_name: str, transcript: str) -> dict:
    """Pull per-intent tool arguments out of the raw transcript.

    `order_status` extracts the first 4+ digit run as `order_id`. Returns
    an empty dict when no digits are present, leaving the orchestrator to
    surface `missing_args`. `abandoned_cart_recovery` uses a hardcoded
    customer id until the ElevenAgents session layer supplies a real one.
    """
    if intent_name == "order_status":
        match = _ORDER_ID_RE.search(transcript)
        if match is None:
            return {}
        return {"order_id": match.group(0)}
    if intent_name == "abandoned_cart_recovery":
        return {"customer_id": _DEMO_CUSTOMER_ID}
    return {}


def _score(transcript_norm: str, keywords: list[str]) -> tuple[int, int]:
    """Return `(matched, total)` keyword counts against the normalized transcript."""
    if not keywords:
        return 0, 0
    matched = sum(1 for kw in keywords if _normalize(kw) in transcript_norm)
    return matched, len(keywords)


def classify(transcript: str) -> Intent:
    """Score `transcript` against the intent corpus and return the best match."""
    intents = load_intents()
    transcript_norm = _normalize(transcript)

    best_name: str | None = None
    best_spec: dict | None = None
    best_confidence: float = 0.0

    for name, spec in intents.items():
        matched, total = _score(transcript_norm, spec.get("keywords", []))
        if total == 0 or matched == 0:
            continue
        confidence = min(matched / total, _CONFIDENCE_CAP)
        threshold = float(spec.get("confidence_threshold", 0.75))
        # Escalation runs at a deliberately lower threshold (see intents.json):
        # high recall on "I want a human" is preferred over precision.
        if confidence >= threshold and confidence > best_confidence:
            best_name = name
            best_spec = spec
            best_confidence = confidence

    if best_spec is None or best_name is None:
        return Intent(
            name="fallback",
            confidence=0.0,
            tool=None,
            response_template=FALLBACK_RESPONSE,
            narration_required=False,
            narration_text=None,
            threshold=0.0,
            tool_args={},
        )

    return Intent(
        name=best_name,
        confidence=best_confidence,
        tool=best_spec.get("tool"),
        response_template=best_spec["response_template"],
        narration_required=bool(best_spec.get("narration_required", False)),
        narration_text=best_spec.get("narration_text"),
        threshold=float(best_spec.get("confidence_threshold", 0.75)),
        tool_args=_extract_tool_args(best_name, transcript),
    )


def should_escalate(intent: Intent) -> bool:
    """Escalate when the intent name is `escalation_request`/`fallback`, or confidence < threshold."""
    if intent.name in {"escalation_request", "fallback"}:
        return True
    return intent.confidence < intent.threshold

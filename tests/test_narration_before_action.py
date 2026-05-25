"""Property test: narration is emitted before any tool call, and escalation skips it.

These tests verify the ElevenAgents headline invariant against the structured per-turn
log, not against in-memory state. The log is the artifact a reviewer reads;
asserting on the log is the same evidence a reviewer would see in
`outputs/eleven-agents_demo/events.jsonl`.

`tmp_path` redirects the log file via `set_log_path`, so tests do not pollute
the real `outputs/eleven-agents_demo/events.jsonl` and stay isolated from each other.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.logging_setup import set_log_path
from src.orchestrator import UserTurn, handle_turn


def _read_events(path: Path) -> list[dict]:
    """Parse the JSONL log file into an ordered list of event dicts."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _index_of(events: list[dict], event_name: str) -> int:
    """Return the first index in `events` whose `event` field equals `event_name`, or -1."""
    for i, ev in enumerate(events):
        if ev.get("event") == event_name:
            return i
    return -1


@pytest.fixture
def event_log(tmp_path: Path) -> Path:
    """Redirect the events log to a per-test tmp file and restore the default after."""
    log_path = tmp_path / "events.jsonl"
    set_log_path(log_path)
    yield log_path
    set_log_path(None)


@pytest.mark.asyncio
async def test_narration_emitted_before_tool_call(event_log: Path) -> None:
    """For an `order_status` turn, the narration event precedes the tool_called event."""
    turn = UserTurn(transcript="Onde tá o meu pedido 54321?", turn_id="t-narrate")
    result = await handle_turn(turn)

    assert result.escalated is False, "order_status should not escalate"

    events = _read_events(event_log)
    narration_idx = _index_of(events, "narration_emitted")
    tool_idx = _index_of(events, "tool_called")

    assert narration_idx >= 0, "narration_emitted event was not written"
    assert tool_idx >= 0, "tool_called event was not written"
    assert narration_idx < tool_idx, (
        f"narration_emitted (idx={narration_idx}) must precede tool_called "
        f"(idx={tool_idx}) in event log order"
    )

    # Timestamps must also be monotonic. ISO-8601 with the same tz suffix
    # sorts lexicographically, so a plain string compare is sound.
    assert (
        events[narration_idx]["timestamp"] <= events[tool_idx]["timestamp"]
    ), "narration timestamp must be <= tool_called timestamp"


@pytest.mark.asyncio
async def test_escalation_skips_narration(event_log: Path) -> None:
    """For an escalation turn, an `escalated` event is written and no narration event appears."""
    turn = UserTurn(
        transcript="Quero falar com uma pessoa, por favor", turn_id="t-escalate"
    )
    result = await handle_turn(turn)

    assert result.escalated is True, "escalation_request must escalate"

    events = _read_events(event_log)
    assert _index_of(events, "escalated") >= 0, "escalated event was not written"
    assert (
        _index_of(events, "narration_emitted") == -1
    ), "narration_emitted must not appear on the escalation branch"
    assert (
        _index_of(events, "tool_called") == -1
    ), "tool_called must not appear on the escalation branch"


@pytest.mark.asyncio
async def test_handoff_context_carries_history_and_reason(event_log: Path) -> None:
    """The `escalated` event includes the HandoffContext with history, intent, reason, target."""
    history = [
        {"role": "user", "text": "oi"},
        {"role": "agent", "text": "oi, tudo bem?"},
    ]
    turn = UserTurn(transcript="Quero falar com uma pessoa", turn_id="t-handoff")
    await handle_turn(turn, history=history)

    events = _read_events(event_log)
    idx = _index_of(events, "escalated")
    assert idx >= 0, "escalated event must be present"

    handoff = events[idx].get("handoff")
    assert isinstance(handoff, dict), "handoff must be a serialized dict"
    assert handoff["unresolved_intent"] == "escalation_request"
    assert handoff["reason"] == "user_request"
    assert handoff["to"] == "Camila"
    assert handoff["conversation_history"] == history

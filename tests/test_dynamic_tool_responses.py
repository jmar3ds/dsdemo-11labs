"""The orchestrator should answer from tool output, not static templates."""

from __future__ import annotations

import pytest

import src.orchestrator as orch
from src.logging_setup import set_log_path
from src.orchestrator import UserTurn, handle_turn
from src.tools import Order


@pytest.fixture(autouse=True)
def isolated_log(tmp_path):
    set_log_path(tmp_path / "events.jsonl")
    yield
    set_log_path(None)


@pytest.mark.asyncio
async def test_order_status_response_uses_returned_status(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_order(order_id: str) -> Order:
        return Order(order_id=order_id, status="delayed", customer_name="Ana Souza", total_brl=287.90)

    monkeypatch.setitem(orch._TOOL_REGISTRY, "fetch_order", fake_fetch_order)

    result = await handle_turn(UserTurn(transcript="Onde tá o meu pedido 54321?", turn_id="t-dynamic"))

    assert result.escalated is False
    assert "atraso" in result.text.lower()
    assert "Camila" in result.text
    assert "Boa notícia" not in result.text


@pytest.mark.asyncio
async def test_missing_order_id_asks_for_number() -> None:
    result = await handle_turn(UserTurn(transcript="Onde tá o meu pedido?", turn_id="t-missing"))

    assert result.escalated is False
    assert "número do pedido" in result.text.lower()

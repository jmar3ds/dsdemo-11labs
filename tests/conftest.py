"""Shared pytest fixtures for the ElevenAgents test suite.

`sample_turns` provides parametrized cases of (transcript, expected_intent_name,
expected_should_escalate) for the rule-based classifier under tests/.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_turns() -> list[tuple[str, str, bool]]:
    """Canonical PT-BR transcripts paired with expected intent + escalation flag."""
    return [
        ("Onde tá o meu pedido 54321?", "order_status", False),
        ("Quero falar com uma pessoa, por favor", "escalation_request", True),
        ("Carrinho abandonado", "abandoned_cart_recovery", False),
        ("Não entendi nada disso aqui", "fallback", True),
        ("Pra onde foi minha encomenda?", "order_status", False),
        ("Acho que minha entrega tá atrasada", "order_status", False),
    ]

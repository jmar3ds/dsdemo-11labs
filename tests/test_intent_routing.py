"""Parametrized tests for the rule-based intent classifier.

Each case exercises one transcript through `classify` and asserts both the
returned intent name and the escalation flag (escalates when the intent is
`fallback`/`escalation_request`, or when confidence falls below threshold).
"""

from __future__ import annotations

import pytest

from src.intents import classify, should_escalate

CASES: list[tuple[str, str, bool]] = [
    ("Onde tá o meu pedido 54321?", "order_status", False),
    ("Quero falar com uma pessoa, por favor", "escalation_request", True),
    ("Carrinho abandonado", "abandoned_cart_recovery", False),
    ("Não entendi nada disso aqui", "fallback", True),
    ("Pra onde foi minha encomenda?", "order_status", False),
    ("Acho que minha entrega tá atrasada", "order_status", False),
]


@pytest.mark.parametrize("transcript, expected_name, expected_escalate", CASES)
def test_classify_routes_transcript(
    transcript: str, expected_name: str, expected_escalate: bool
) -> None:
    """Each transcript classifies to the expected intent with the expected escalation flag."""
    intent = classify(transcript)
    assert intent.name == expected_name, (
        f"transcript={transcript!r} expected intent={expected_name!r} "
        f"got={intent.name!r} confidence={intent.confidence:.3f} threshold={intent.threshold:.3f}"
    )
    assert should_escalate(intent) is expected_escalate, (
        f"transcript={transcript!r} intent={intent.name!r} "
        f"confidence={intent.confidence:.3f} threshold={intent.threshold:.3f} "
        f"expected_escalate={expected_escalate}"
    )


def test_sample_turns_fixture_matches_cases(sample_turns: list[tuple[str, str, bool]]) -> None:
    """The shared `sample_turns` fixture mirrors the parametrize source list."""
    assert sample_turns == CASES

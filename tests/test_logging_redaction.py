"""PII-redaction tests for Brazilian retail support logs."""

from __future__ import annotations

from src.logging_setup import redact_pii


def test_redacts_formatted_cpf_cnpj_phone_email_and_order_id() -> None:
    record = {
        "transcript": (
            "Meu CPF é 123.456.789-00, CNPJ 12.345.678/0001-99, "
            "telefone +55 11 99999-9999, email ana.souza@example.com, pedido 54321."
        ),
        "tool_args": {"order_id": "54321"},
    }

    redacted = redact_pii(record)
    text = redacted["transcript"]

    assert "123.456.789-00" not in text
    assert "12.345.678/0001-99" not in text
    assert "+55 11 99999-9999" not in text
    assert "ana.souza@example.com" not in text
    assert "pedido 54321" not in text
    assert "[cpf:***8900]" in text
    assert "[cnpj:***0199]" in text
    assert "[phone:***9999]" in text
    assert "[email:redacted]" in text
    assert redacted["tool_args"]["order_id"] == "***4321"

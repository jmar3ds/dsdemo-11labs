"""Transport-level retry tests for `src/tools.fetch_order`.

These tests use `respx` to intercept httpx requests at the transport layer
and exercise the three retry properties that matter for a reviewer:

1. Transient `httpx.ConnectError` is retried and a later success is returned.
2. After the retry budget is exhausted, the underlying transport error is
   re-raised (tenacity's `reraise=True`), not wrapped in `RetryError`.
3. A 404 `HTTPStatusError` is NOT retried: it propagates after one attempt.

Run from repo root: `python -m pytest tests/test_retry.py -v`.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from src.tools import BASE_URL, fetch_order


@pytest.mark.asyncio
async def test_retries_on_transport_error_then_succeeds() -> None:
    """First two attempts raise ConnectError, third returns 200; the order is returned."""
    order_payload = {
        "order_id": "54321",
        "status": "out_for_delivery",
        "customer_name": "Ana Souza",
        "total_brl": 287.90,
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        route = mock.get("/orders/54321").mock(
            side_effect=[
                httpx.ConnectError("conn refused"),
                httpx.ConnectError("conn refused"),
                httpx.Response(200, json=order_payload),
            ]
        )

        order = await fetch_order("54321")

        assert order.order_id == "54321"
        assert order.status == "out_for_delivery"
        assert order.customer_name == "Ana Souza"
        assert order.total_brl == pytest.approx(287.90)
        assert route.call_count == 3, (
            f"expected 3 attempts (2 retries on ConnectError + 1 success), got {route.call_count}"
        )


@pytest.mark.asyncio
async def test_gives_up_after_max_attempts() -> None:
    """All three attempts raise ConnectError; the underlying transport error propagates."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        route = mock.get("/orders/54321").mock(
            side_effect=httpx.ConnectError("conn refused"),
        )

        with pytest.raises(httpx.TransportError):
            await fetch_order("54321")

        assert route.call_count == 3, (
            f"retry budget should be exactly 3 attempts, got {route.call_count}"
        )


@pytest.mark.asyncio
async def test_404_is_not_retried() -> None:
    """A 404 status raises HTTPStatusError after exactly one attempt (not retried)."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        route = mock.get("/orders/nonexistent").mock(
            return_value=httpx.Response(404, json={"detail": "order_not_found:nonexistent"}),
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await fetch_order("nonexistent")

        assert exc_info.value.response.status_code == 404
        assert route.call_count == 1, (
            f"404 must not be retried; got {route.call_count} attempts"
        )

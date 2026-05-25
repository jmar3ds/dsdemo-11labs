"""Mocked Magalu tool layer: order lookup, ETA, and cart via httpx + tenacity retry.

Each tool calls the local FastAPI mock at `MOCK_BACKEND_URL` (default
`http://127.0.0.1:8000`) and returns a typed dataclass. Network-level failures
(`httpx.TransportError`) are retried up to three times with exponential
backoff; HTTP status errors (e.g. 404 order not found) are not retried and
propagate to the orchestrator as `httpx.HTTPStatusError` for structured
ToolResult mapping.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

BASE_URL: str = os.environ.get("MOCK_BACKEND_URL", "http://127.0.0.1:8000")
DEFAULT_TIMEOUT: httpx.Timeout = httpx.Timeout(5.0, connect=2.0)


@dataclass(frozen=True)
class Order:
    """One mock Magalu order, as returned by the order-status tool."""

    order_id: str
    status: str
    customer_name: str
    total_brl: float


@dataclass(frozen=True)
class DeliveryETA:
    """Delivery ETA result for one order, as returned by the ETA tool."""

    order_id: str
    eta_text: str
    confidence_window_hours: int | None


@dataclass(frozen=True)
class Cart:
    """One mock abandoned cart, as returned by the cart-recovery tool."""

    customer_id: str
    items: list[dict]
    promo_code: str | None
    promo_discount_pct: int | None


@dataclass(frozen=True)
class ToolResult:
    """Generic tool envelope: success carries `data`, failure carries `error`."""

    ok: bool
    data: object | None = None
    error: str | None = None


_RETRY_KWARGS = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=4.0),
    retry=retry_if_exception_type(httpx.TransportError),
    reraise=True,
)


@retry(**_RETRY_KWARGS)
async def fetch_order(order_id: str) -> Order:
    """Look up one order by id. Retried on transport errors, not on HTTP status errors."""
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(f"{BASE_URL}/orders/{order_id}")
        response.raise_for_status()
        data = response.json()
        return Order(
            order_id=data["order_id"],
            status=data["status"],
            customer_name=data["customer_name"],
            total_brl=float(data["total_brl"]),
        )


@retry(**_RETRY_KWARGS)
async def fetch_delivery_eta(order_id: str) -> DeliveryETA:
    """Look up the delivery ETA for one order. Retried on transport errors."""
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(f"{BASE_URL}/delivery_eta/{order_id}")
        response.raise_for_status()
        data = response.json()
        return DeliveryETA(
            order_id=data["order_id"],
            eta_text=data["eta_text"],
            confidence_window_hours=data.get("confidence_window_hours"),
        )


@retry(**_RETRY_KWARGS)
async def fetch_cart(customer_id: str) -> Cart:
    """Look up the customer's abandoned cart. Retried on transport errors."""
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(f"{BASE_URL}/carts/{customer_id}")
        response.raise_for_status()
        data = response.json()
        return Cart(
            customer_id=data["customer_id"],
            items=list(data.get("items", [])),
            promo_code=data.get("promo_code"),
            promo_discount_pct=data.get("promo_discount_pct"),
        )

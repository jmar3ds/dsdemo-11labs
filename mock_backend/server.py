"""Local FastAPI mock standing in for Magalu's customer + order services.

Used by ElevenAgents tools.py during the demo. Real production would point at Magalu's actual
endpoints. This server is deliberately deterministic: real-server flakiness is simulated
in tests via respx, not here. Run with: `python -m mock_backend.server` or `make mock`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
ORDERS_FILE: Path = REPO_ROOT / "data" / "mock_orders.json"

logger = logging.getLogger(__name__)
app = FastAPI(title="Magalu Mock Backend", version="0.1.0")


def _load_orders() -> dict[str, dict]:
    """Read the mock orders corpus once at startup."""
    with ORDERS_FILE.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("orders", {})


_ORDERS: dict[str, dict] = _load_orders()


def _eta_for(status: str) -> dict:
    """Compute a deterministic delivery ETA per order status."""
    now = datetime.now(tz=timezone.utc)
    if status == "out_for_delivery":
        return {
            "eta_text": "Hoje, entre 14h e 18h",
            "eta_iso": (now + timedelta(hours=4)).isoformat(),
            "confidence_window_hours": 4,
        }
    if status == "processing":
        return {
            "eta_text": "Saída pra entrega até quinta-feira",
            "eta_iso": (now + timedelta(days=2)).isoformat(),
            "confidence_window_hours": 24,
        }
    if status == "delivered":
        return {
            "eta_text": "Já entregue",
            "eta_iso": (now - timedelta(hours=12)).isoformat(),
            "confidence_window_hours": 0,
        }
    if status == "delayed":
        return {
            "eta_text": "Em apuração, te aviso assim que tiver previsão nova",
            "eta_iso": None,
            "confidence_window_hours": None,
        }
    return {
        "eta_text": "Sem previsão disponível",
        "eta_iso": None,
        "confidence_window_hours": None,
    }


@app.get("/health")
def health() -> dict:
    """Liveness probe for the demo runner."""
    return {"ok": True, "orders_loaded": len(_ORDERS)}


@app.get("/orders/{order_id}")
def get_order(order_id: str) -> dict:
    """Return the order envelope, or 404 if unknown."""
    order = _ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"order_not_found:{order_id}")
    return order


@app.get("/delivery_eta/{order_id}")
def get_delivery_eta(order_id: str) -> dict:
    """Return a delivery ETA envelope computed from the order's status."""
    order = _ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"order_not_found:{order_id}")
    eta = _eta_for(order["status"])
    return {"order_id": order_id, **eta}


@app.get("/carts/{customer_id}")
def get_cart(customer_id: str) -> dict:
    """Stub abandoned-cart payload. ElevenAgents Phase 1 uses a template-only response so this returns a fixed shape."""
    return {
        "customer_id": customer_id,
        "items": [
            {
                "sku": "samsung-galaxy-a55",
                "name": "Samsung Galaxy A55 5G",
                "price_brl": 2199.00,
            },
            {
                "sku": "fone-jbl-tune-510bt",
                "name": "Fone JBL Tune 510BT",
                "price_brl": 249.90,
            },
        ],
        "promo_code": "VOLTA5",
        "promo_expires_iso": (
            datetime.now(tz=timezone.utc) + timedelta(days=1)
        ).isoformat(),
        "promo_discount_pct": 5,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

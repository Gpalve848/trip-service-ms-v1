# app/service_clients.py
from typing import Optional, Dict, Any
import httpx
import uuid
from .config import RIDER_URL, DRIVER_URL, PAYMENT_URL, HTTP_TIMEOUT

def _join(base: str, *parts: str) -> str:
    """
    Safe URL join that prevents duplicate slashes and ensures single separators.
    Does not touch query strings.
    """
    s = base.rstrip("/")
    for p in parts:
        s += "/" + p.strip("/")
    return s

# --- Rider ---
async def get_rider(rider_id: str) -> Dict[str, Any]:
    # RIDER_URL expected like: http://host.minikube.internal:3001
    url = _join(RIDER_URL, "v1", "riders", rider_id)
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return {"ok": True, "body": r.json()}
        except httpx.HTTPStatusError as e:
            return {"ok": False, "error": f"status:{e.response.status_code}", "detail": e.response.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}

# --- Driver ---
# DRIVER_URL is expected to already include the API prefix, e.g.:
#   DRIVER_URL = "http://host.minikube.internal:8000/api/v1"
# so we only append resource paths below.

async def get_driver(driver_id: str) -> Dict[str, Any]:
    # Detail endpoint (note trailing slash for DRF)
    url = _join(DRIVER_URL, "drivers", f"{driver_id}") + "/"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return {"ok": True, "body": r.json()}
        except httpx.HTTPStatusError as e:
            return {"ok": False, "error": f"status:{e.response.status_code}", "detail": e.response.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}

async def get_driver_status(driver_id: str) -> Dict[str, Any]:
    # Status endpoint (also keep trailing slash)
    url = _join(DRIVER_URL, "drivers", f"{driver_id}", "status") + "/"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return {"ok": True, "body": r.json()}
        except httpx.HTTPStatusError as e:
            return {"ok": False, "error": f"status:{e.response.status_code}", "detail": e.response.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}

# --- Payment ---
async def create_payment(
    trip_id: int | str,
    amount: float,
    method: str = "CARD",
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calls Payment service to create/charge a payment.
    Ensures trip_id is sent as integer when possible (coerce numeric strings).
    """
    # coerce trip_id to int when possible
    final_trip_id: int | str
    try:
        if isinstance(trip_id, int):
            final_trip_id = trip_id
        elif isinstance(trip_id, str) and trip_id.isdigit():
            final_trip_id = int(trip_id)
        else:
            stripped = str(trip_id).strip()
            final_trip_id = int(stripped) if stripped.isdigit() else trip_id
    except Exception:
        final_trip_id = trip_id

    if idempotency_key is None:
        idempotency_key = f"trip-{final_trip_id}-{uuid.uuid4().hex[:8]}"

    url = _join(PAYMENT_URL, "payments")
    payload = {
        "idempotency_key": idempotency_key,
        "trip_id": final_trip_id,
        "method": method,
        "amount": amount,
        "metadata": {}
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            r = await client.post(url, json=payload)
            if r.status_code in (200, 201, 202):
                try:
                    return {"ok": True, "body": r.json(), "status": r.status_code}
                except Exception:
                    return {"ok": True, "body": {"raw": r.text}, "status": r.status_code}
            else:
                try:
                    return {"ok": False, "status": r.status_code, "body": r.json()}
                except Exception:
                    return {"ok": False, "status": r.status_code, "text": r.text}
        except Exception as e:
            return {"ok": False, "error": str(e)}

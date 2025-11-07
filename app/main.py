# app/main.py
import os
import datetime
import uuid
from typing import Optional, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, DateTime, Integer, JSON, Numeric

# ---------------------------
# Config / DB
# ---------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/tripdb")
database = Database(DATABASE_URL)
metadata = MetaData()

trips = Table(
    "trips",
    metadata,
    Column("id", String, primary_key=True),
    Column("seq_id", Integer, nullable=True),
    Column("rider_id", String, nullable=True),
    Column("driver_id", String, nullable=True),
    Column("status", String, nullable=True),
    Column("requested_at", DateTime, nullable=True),
    Column("accepted_at", DateTime, nullable=True),
    Column("started_at", DateTime, nullable=True),
    Column("completed_at", DateTime, nullable=True),
    Column("distance_meters", Float, nullable=True),
    Column("base_fare", Numeric, nullable=True),
    Column("surge_multiplier", Numeric, nullable=True),
    Column("fare_amount", Numeric, nullable=True),
    Column("payment_id", String, nullable=True),
    Column("correlation_id", String, nullable=True),
    Column("metadata", JSON, nullable=True),
)

# create tables locally if not present (safe for dev)
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

# ---------------------------
# External service base URLs
# ---------------------------
RIDER_URL = os.getenv("RIDER_URL", "http://127.0.0.1:3001")
DRIVER_URL = os.getenv("DRIVER_URL", "http://127.0.0.1:8000")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://127.0.0.1:8082")

HTTP_TIMEOUT = 10.0

# ---------------------------
# FastAPI app and schemas
# ---------------------------
app = FastAPI(title="Trip Service")

class TripCreate(BaseModel):
    rider_id: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    metadata: Optional[Dict[str, Any]] = None

class AssignDriver(BaseModel):
    driver_id: str

# ---------------------------
# Helper: call external service
# ---------------------------
async def http_call(method: str, url: str, json: Optional[Dict[str,Any]] = None) -> Dict[str,Any]:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        try:
            if method.upper() == "GET":
                r = await client.get(url)
            else:
                r = await client.post(url, json=json)
            try:
                body = r.json()
            except Exception:
                body = {"raw": r.text}
            return {"ok": r.status_code < 400, "status": r.status_code, "body": body}
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ---------------------------
# Startup / Shutdown
# ---------------------------
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# ---------------------------
# Routes
# ---------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat()}

@app.post("/v1/trips")
async def create_trip(payload: TripCreate):
    rider_resp = await http_call("GET", f"{RIDER_URL}/v1/riders/{payload.rider_id}")
    if not rider_resp["ok"]:
        raise HTTPException(status_code=400, detail=f"Rider service error: status:{rider_resp.get('status') or rider_resp.get('error')}")
    trip_id = uuid.uuid4().hex
    correlation_id = uuid.uuid4().hex
    now = datetime.datetime.utcnow()
    await database.execute(
        trips.insert().values(
            id=trip_id,
            rider_id=payload.rider_id,
            status="REQUESTED",
            requested_at=now,
            correlation_id=correlation_id,
            metadata=payload.metadata or {}
        )
    )
    return {
        "id": trip_id,
        "rider_id": payload.rider_id,
        "status": "REQUESTED",
        "requested_at": now.isoformat(),
        "correlation_id": correlation_id,
        "metadata": payload.metadata or {}
    }

@app.post("/v1/trips/{trip_id}/assign")
async def assign_driver(trip_id: str, data: AssignDriver):
    drv_resp = await http_call("GET", f"{DRIVER_URL}/api/v1/drivers/{data.driver_id}/status")
    if not drv_resp["ok"]:
        raise HTTPException(status_code=400, detail=f"Driver service unreachable: status:{drv_resp.get('status') or drv_resp.get('error')}")
    await database.execute(
        trips.update()
        .where(trips.c.id == trip_id)
        .values(driver_id=data.driver_id, status="ASSIGNED", accepted_at=datetime.datetime.utcnow())
    )
    return {"trip_id": trip_id, "status": "ASSIGNED"}

@app.post("/v1/trips/{trip_id}/accept")
async def accept_trip(trip_id: str):
    await database.execute(
        trips.update().where(trips.c.id == trip_id).values(status="ACCEPTED", accepted_at=datetime.datetime.utcnow())
    )
    return {"trip_id": trip_id, "status": "ACCEPTED"}

@app.post("/v1/trips/{trip_id}/start")
async def start_trip(trip_id: str):
    await database.execute(
        trips.update().where(trips.c.id == trip_id).values(status="ONGOING", started_at=datetime.datetime.utcnow())
    )
    return {"trip_id": trip_id, "status": "ONGOING"}

@app.post("/v1/trips/{trip_id}/complete")
async def complete_trip(trip_id: str):
    # fetch row and convert to dict immediately (fix for databases.Record .get not available)
    row = await database.fetch_one(trips.select().where(trips.c.id == trip_id))
    if not row:
        raise HTTPException(status_code=404, detail="Trip not found")

    q = dict(row)  # <-- convert to plain dict to allow q.get(...) safely

    if q.get("status") != "ONGOING":
        raise HTTPException(status_code=400, detail="Trip not in progress")

    # compute fare (fallback)
    fare = float(q.get("fare_amount") or 50.0)

    seq_id = q.get("seq_id")
    if seq_id is None:
        raise HTTPException(status_code=400, detail="Trip seq_id missing; cannot call payment service")

    # prepare payment payload (Payment collection expects POST /payments with integer trip_id)
    payment_payload = {
        "idempotency_key": f"trip-{seq_id}-{uuid.uuid4().hex[:8]}",
        "trip_id": int(seq_id),
        "method": "CARD",
        "amount": int(fare),
        "metadata": {"note": "auto-charge"}
    }

    payment_resp = await http_call("POST", f"{PAYMENT_URL}/payments", json=payment_payload)

    # extract payment id from returned body safely
    payment_id_val = None
    if payment_resp.get("ok") and isinstance(payment_resp.get("body"), dict):
        body = payment_resp["body"]
        payment_id_val = body.get("payment_id") or body.get("id") or body.get("paymentId") or None

    now = datetime.datetime.utcnow()
    if payment_id_val is not None:
        payment_id_str = str(payment_id_val)  # ensure string before DB write
        await database.execute(
            trips.update()
            .where(trips.c.id == trip_id)
            .values(status="COMPLETED", fare_amount=fare, completed_at=now, payment_id=payment_id_str)
        )
    else:
        await database.execute(
            trips.update()
            .where(trips.c.id == trip_id)
            .values(status="COMPLETED", fare_amount=fare, completed_at=now)
        )

    return {"trip_id": trip_id, "status": "COMPLETED", "fare": fare, "payment": payment_resp}

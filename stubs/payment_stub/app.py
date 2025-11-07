# stubs/payment_stub/app.py
from fastapi import FastAPI
from pydantic import BaseModel
import uuid

app = FastAPI(title="Payment Stub")

class Charge(BaseModel):
    trip_id: str
    amount: float
    rider_id: str
    correlation_id: str

payments = {}  # in-memory map trip_id -> payment_id

@app.post("/v1/payments/charge")
def charge(c: Charge):
    if c.trip_id in payments:
        return {"payment_id": payments[c.trip_id], "status": "ALREADY_CHARGED"}
    pid = str(uuid.uuid4())
    payments[c.trip_id] = pid
    return {"payment_id": pid, "status": "SUCCESS"}

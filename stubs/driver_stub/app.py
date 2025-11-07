# stubs/driver_stub/app.py
from fastapi import FastAPI
app = FastAPI(title="Driver Stub")

# simple status check
@app.get("/v1/drivers/{driver_id}/status")
def status(driver_id: str):
    # drivers with "inactive" in id are considered inactive
    is_active = "inactive" not in driver_id.lower()
    return {"driver_id": driver_id, "is_active": is_active, "location": {"lat": 12.97, "lng": 77.59}}

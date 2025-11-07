# stubs/rider_stub/app.py
from fastapi import FastAPI

app = FastAPI(title="Rider Stub")

# small in-memory riders database for development
RIDERS = {
    "1": {"id":"1", "name":"Alice", "phone":"9991112222", "default_payment_method":"card_123"},
    "8": {"id":"8", "name":"Bob", "phone":"8882223333", "default_payment_method":"card_456"},
    "9": {"id":"9", "name":"Charlie", "phone":"7773334444", "default_payment_method":"card_789"},
    "73": {"id":"73", "name":"Zoe", "phone":"7700001111", "default_payment_method":"card_999"},
    # add other IDs you saw in seed CSV as needed
}

@app.get("/v1/riders/{rider_id}")
def get_rider(rider_id: str):
    r = RIDERS.get(rider_id)
    if not r:
        return {"found": False, "rider_id": rider_id}
    return {"found": True, "rider": r}

@app.get("/v1/riders/{rider_id}/status")
def rider_status(rider_id: str):
    r = RIDERS.get(rider_id)
    if not r:
        return {"rider_id": rider_id, "exists": False}
    return {"rider_id": rider_id, "exists": True, "is_active": True}

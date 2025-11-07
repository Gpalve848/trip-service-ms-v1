# app/schemas.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TripCreate(BaseModel):
    rider_id: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TripOut(BaseModel):
    id: str
    rider_id: str
    driver_id: Optional[str] = None
    status: str
    requested_at: Optional[str] = None
    accepted_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    distance_meters: Optional[float] = None
    fare_amount: Optional[float] = None
    payment_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # expose seq_id for debugging/verification
    seq_id: Optional[int] = None

class AssignDriver(BaseModel):
    driver_id: str

# app/models.py
from sqlalchemy import (
    Table, Column, MetaData, String, Integer, Float, Numeric,
    DateTime, JSON, Boolean
)

metadata = MetaData()

trips = Table(
    "trips",
    metadata,
    Column("id", String, primary_key=True),
    Column("rider_id", String),
    Column("driver_id", String, nullable=True),
    Column("pickup_lat", Float, nullable=True),
    Column("pickup_lng", Float, nullable=True),
    Column("drop_lat", Float, nullable=True),
    Column("drop_lng", Float, nullable=True),
    Column("status", String),
    Column("requested_at", DateTime),
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
    # 🔴 important: include seq_id so selects return it
    Column("seq_id", Integer, nullable=True),
)

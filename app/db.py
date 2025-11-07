# app/db.py
import os
from databases import Database
from sqlalchemy import create_engine, MetaData

# Use DB host 'db' when running inside docker compose; localhost when running app locally.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/tripdb")

database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)
metadata = MetaData()

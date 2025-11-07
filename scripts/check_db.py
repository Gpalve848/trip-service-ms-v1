Set-Content -Path "scripts\check_db.py" -Value @"
import os
import sqlalchemy
from sqlalchemy import text

# Database connection URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/tripdb')
print('Using', DATABASE_URL)

# Create a connection engine
engine = sqlalchemy.create_engine(DATABASE_URL)

# Try connecting and running a simple query
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1')).fetchone()
        print('DB responded:', result)
except Exception as e:
    print('Database connection failed!')
    print('Error:', e)
"@

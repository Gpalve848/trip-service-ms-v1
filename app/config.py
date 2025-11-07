# app/config.py
import os

# Base URLs for real services (use host.docker.internal so container can reach host services)
# Update these if your services are bound to different host ports.
RIDER_URL = os.getenv("RIDER_URL", "http://host.docker.internal:3001")
DRIVER_URL = os.getenv("DRIVER_URL", "http://host.docker.internal:8000")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://host.docker.internal:8082")

# Driver API path version portion (driver collection used /api/v1/...)
DRIVER_API_VERSION = os.getenv("DRIVER_API_VERSION", "v1")

# Timeout for HTTP calls (seconds)
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "8.0"))

# Dockerfile for Trip service
FROM python:3.11-slim

# avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Copy requirements first to leverage layer cache
COPY requirements.txt /app/requirements.txt

# system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/requirements.txt

# copy app
COPY . /app

# ensure uvicorn listens on 0.0.0.0:8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

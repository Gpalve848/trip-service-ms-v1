# Trip Service — Full Setup & Deployment Guide (Local + Minikube Kubernetes)

This document provides a **complete step-by-step guide** for running the **Trip Service** along with its dependencies (Driver Service, Rider Service, Payment Service, Postgres) both:
1. ✅ **Locally using Docker containers**, and
2. ✅ **On Kubernetes using Minikube**

It includes everything from **cloning the repository**, **environment setup**, **building images**, **database preparation**, **service lifecycle testing**, and **Kubernetes deployment**.

---

# ✅ 1. Clone the Project

```bash
git clone <your-trip-service-repository-url>
cd trip-service
```

Ensure your structure looks like:
```
trip-service/
 ├── app/
 ├── Dockerfile
 ├── requirements.txt
 ├── k8s/
 └── README.md
```

---

# ✅ 2. Install Required Tools

### Install Docker
https://docs.docker.com/get-docker/

### Install Python (if needed for debugging)
https://www.python.org/downloads/

### Install Minikube
https://minikube.sigs.k8s.io/docs/start/

### Install Kubectl
https://kubernetes.io/docs/tasks/tools/

### Confirm installations
```bash
docker --version
kubectl version --client
minikube version
```

---

# ✅ 3. Environment Variables (Local Development)

Create a `.env` file:

```
DATABASE_URL=postgresql://postgres:postgres@trip-db:5432/tripdb
RIDER_URL=http://host.docker.internal:3001
DRIVER_URL=http://host.docker.internal:8000
DRIVER_API_VERSION=v1
PAYMENT_URL=http://host.docker.internal:8082
```

For Windows Docker Desktop, `host.docker.internal` works by default.

---

# ✅ 4. Start Dependencies Locally (Docker Containers)

Start **Rider**, **Driver**, and **Payment** services in separate terminals.

Start a Postgres container for trip-service:

```bash
docker run -d --name trip-db -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
```

---

# ✅ 5. Build and Run Trip Service Locally

## Build the Docker image:
```bash
docker build -t trip-service:latest .
```

## Run the Trip Service container:
```bash
docker run -d --name trip-service -p 8004:8000 --env-file .env trip-service:latest
```

## Verify health:
```bash
curl http://127.0.0.1:8004/health
```

---

# ✅ 6. Initialize Database (Local)

Execute SQL inside Postgres:

```bash
docker exec -it trip-db psql -U postgres -d tripdb
```

Run:
```
CREATE SEQUENCE IF NOT EXISTS trip_seq START WITH 1000;
ALTER TABLE trips ADD COLUMN IF NOT EXISTS seq_id INTEGER;
ALTER TABLE trips ALTER COLUMN seq_id SET DEFAULT nextval('trip_seq');
ALTER SEQUENCE trip_seq OWNED BY trips.seq_id;
CREATE UNIQUE INDEX IF NOT EXISTS trips_seq_id_idx ON trips(seq_id);
```

Exit:
```
\q
```

---

# ✅ 7. Test Full Trip Lifecycle (Local)

### 1. Create Trip:
```
curl -X POST "http://127.0.0.1:8004/v1/trips" -H "Content-Type: application/json" -d "{\"rider_id\": \"<RIDER_ID>\", \"pickup\": \"A\", \"dropoff\": \"B\", \"distance_km\": 5}"
```

### 2. Assign Driver
```
curl -X POST http://127.0.0.1:8004/v1/trips/<TRIP_ID>/assign -d '{"driver_id":"2"}' -H "Content-Type: application/json"
```

### 3. Accept
```
curl -X POST http://127.0.0.1:8004/v1/trips/<TRIP_ID>/accept -d '{"driver_id":"2"}'
```

### 4. Start
```
curl -X POST http://127.0.0.1:8004/v1/trips/<TRIP_ID>/start
```

### 5. Complete
```
curl -X POST http://127.0.0.1:8004/v1/trips/<TRIP_ID>/complete
```

Payment service generates idempotency key automatically.

---

# ✅ 8. Minikube Setup

Start Minikube:
```bash
minikube start --driver=docker --cpus=2 --memory=4096
```

Confirm cluster:
```bash
kubectl get nodes
```

---

# ✅ 9. Deploy Namespace

```bash
kubectl create namespace trip
```

---

# ✅ 10. Load Docker Image Into Minikube

Since Minikube uses its own Docker daemon:

```bash
minikube image build -t trip-service:1.1 .
```

Confirm:
```bash
minikube image ls | findstr trip-service
```

---

# ✅ 11. Apply Kubernetes Manifests

Inside the project folder:

```bash
kubectl apply -n trip -f k8s/
```

This deploys:
- Postgres
- Trip service
- ConfigMap
- Secrets (if any)
- Services (NodePort)

---

# ✅ 12. Verify Everything is Running

```bash
kubectl -n trip get pods
kubectl -n trip get svc
```

Example output:
```
trip-service-xxxxx    Running
postgres-xxxxx        Running
```

---

# ✅ 13. Check Environment Variables Inside Pod

```bash
POD=$(kubectl -n trip get pods -l app=trip-service -o jsonpath="{.items[0].metadata.name}")

kubectl -n trip exec $POD -- printenv DRIVER_URL RIDER_URL PAYMENT_URL
```

Should show:
```
http://host.minikube.internal:8000/api/v1
http://host.minikube.internal:3001
http://host.minikube.internal:8082
```

---

# ✅ 14. Forward Port for API Access

Expose Trip API locally:
```bash
kubectl -n trip port-forward svc/trip-service 18004:8000
```

Now access:
```
http://127.0.0.1:18004/health
http://127.0.0.1:18004/docs
```

---

# ✅ 15. Test Full Trip Lifecycle (Inside Kubernetes)

### 1. Create Trip
```bash
curl -X POST "http://127.0.0.1:18004/v1/trips" -H "Content-Type: application/json" -d "{\"rider_id\":\"69071b84d55ed889c7aa5994\",\"pickup\":\"A\",\"dropoff\":\"B\",\"distance_km\":7}"
```

Copy returned trip_id.

### 2. Assign Driver
```bash
curl -X POST http://127.0.0.1:18004/v1/trips/<TRIP_ID>/assign -d '{"driver_id":"2"}' -H "Content-Type: application/json"
```

### 3. Accept
```bash
curl -X POST http://127.0.0.1:18004/v1/trips/<TRIP_ID>/accept -d '{"driver_id":"2"}'
```

### 4. Start
```bash
curl -X POST http://127.0.0.1:18004/v1/trips/<TRIP_ID>/start
```

### 5. Complete (Triggers payment)
```bash
curl -X POST http://127.0.0.1:18004/v1/trips/<TRIP_ID>/complete
```

---

# ✅ 16. Payment Verification

You can verify Payment service directly from the trip pod:

```bash
kubectl -n trip exec $POD -- python -c "import http.client;h=http.client.HTTPConnection('host.minikube.internal',8082);h.request('GET','/health');print(h.getresponse().read().decode())"
```

---

# ✅ 17. Common Troubleshooting

### ❌ Issue: `Driver service unreachable`
Fix env:
```bash
kubectl -n trip set env deploy/trip-service DRIVER_URL=http://host.minikube.internal:8000 DRIVER_API_VERSION=v1
```

### ❌ Port-forward fails
Find process:
```
netstat -ano | findstr :18004
```
Kill:
```
taskkill /PID <PID> /F
```

### ❌ Pod CrashLoopBackOff
Check logs:
```bash
kubectl -n trip logs <POD_NAME>
```

---

# ✅ 18. Clean Up

```bash
kubectl delete ns trip
minikube stop
```

---

# ✅ Final Notes
This guide covers **every step required** to:
✅ Run trip-service locally
✅ Build Docker images
✅ Connect to rider, driver, payment services
✅ Run the entire trip lifecycle
✅ Deploy the service to Kubernetes
✅ Validate end-to-end flow inside Minikube

If you want, I can also generate:
✅ Full architecture diagram
✅ Sequence diagrams for each API
✅ Kubernetes Helm chart version
✅ Docker Compose version for all 4 services

Just tell me!


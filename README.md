# TicketRush Backend

### 📸 Product Diagram
![Product Diagram](https://iili.io/f47SXgR.jpg)


# 🎟️ TicketRush — Backend Service

> **Python · FastAPI · PostgreSQL · Redis · WebSocket · APScheduler**  
> Modular Monolith — production-ready ticket platform with real-time seat updates, virtual queue, and content-based recommendation.

---

## 🚀 Quickstart

### Prerequisites

- Docker ≥ 24 & Docker Compose ≥ 2.20
- Python 3.11+ (for local dev without Docker)

```bash
git clone https://github.com/minhnvm2307/TicketRushBE.git
cd TicketRushBE

cp .env.example .env
```

### Option 1. Pull images & start (recommended)

Pull a pre-built API image from the registry:

```bash
docker pull minhnvm2307/ticketrush:latest

docker compose -f docker-compose.prod.yml up -d
```

### Option 2. Rebuild your own container

```bash
# Then build your own backend container
docker compose up -d -f docker-compose.yml
```



### 3. DB connection (PostgresDB)

Use your DB connector to create connection (Recommend: Postgres VS-code extension)

```bash
# Creds
Database_name: ticketrush
Username: postgres
Password: postgres
```

### 4. Verify services

| Service | URL | Note |
|---------|-----|-------------|
| API | http://localhost:8000/docs | Danh sach API va mota |
| Embedding API | http://localhost:8081 | text-embeddings-inference (noi bo) |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3001 | creds: admin / admin |
| PostgreSQL | localhost:5432 | postgres / postgres |
| Redis | localhost:6379 | — |

### 5. Embedding mode (optimized container strategy)

`TicketRush` now uses a hybrid approach to keep `api` image slim:

- Default (`EMBEDDING_PROVIDER=http`): API calls the dedicated `embedding` service over HTTP.
- Optional (`EMBEDDING_PROVIDER=onnx`): API runs ONNX model locally.

Recommended default for Docker:

```bash
EMBEDDING_PROVIDER=http
EMBEDDING_SERVICE_URL=http://embedding:80
```

Optional local ONNX mode (without external embedding container):

```bash
pip install .[embedding-onnx]
export EMBEDDING_PROVIDER=onnx
export EMBEDDING_ONNX_MODEL_PATH=/models/model.onnx
export EMBEDDING_ONNX_TOKENIZER_PATH=/models/tokenizer.json
```

This split removes heavy AI runtime from `ticketrush-api` by default and keeps embedding compute isolated.


---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│              Angular SPA · Mobile · Admin Dashboard                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  HTTP / WebSocket
┌──────────────────────────────▼──────────────────────────────────────┐
│                     🐍 Python / FastAPI                             │
│                                                                     │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌────────────────┐   │
│  │   Auth    │  │  Events   │  │  Seats   │  │    Tickets     │   │
│  │  /api/auth│  │/api/events│  │/api/seats│  │  /api/checkout │   │
│  └───────────┘  └───────────┘  └──────────┘  └────────────────┘   │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌────────────────┐   │
│  │ Dashboard │  │   Queue   │  │  Demogr. │  │  Recommend.    │   │
│  │/api/admin │  │ /api/queue│  │/api/admin│  │ /api/recommend │   │
│  └───────────┘  └───────────┘  └──────────┘  └────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              WebSocket Hub  /ws/events/{event_id}           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │    APScheduler Workers (seat release · queue processor)     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────────┬───────────────────────────┬─────────────────────────────┘
            │                           │
┌───────────▼──────────┐   ┌───────────▼──────────┐
│  🐘 PostgreSQL 16    │   │  🟥 Redis 7           │
│                      │   │                       │
│  • users             │   │  • seat hold locks    │
│  • events            │   │  • virtual queue      │
│  • seat_zones        │   │    sorted sets        │
│  • seats             │   │  • queue access       │
│  • tickets           │   │    tokens (TTL 15min) │
│  • orders            │   │  • rate limit         │
│  • order_items       │   │    counters           │
│  • event_categories  │   │                       │
│  • event_tags        │   └───────────────────────┘
│  • user_event_       │
│    interactions      │
└──────────────────────┘
            │
┌───────────▼──────────────────────────────────────────┐
│                  📊 Observability Stack                │
│                                                        │
│  ┌────────────────────┐    ┌─────────────────────┐   │
│  │  🔥 Prometheus      │───▶│  📈 Grafana          │   │
│  │  :9090             │    │  :3001               │   │
│  │                    │    │                      │   │
│  │  /metrics endpoint │    │  • Revenue charts    │   │
│  │  scraped every 15s │    │  • Seat fill rate    │   │
│  │                    │    │  • Queue depth       │   │
│  │  Tracks:           │    │  • Hold success rate │   │
│  │  · hold attempts   │    │  • Sell-through      │   │
│  │  · checkout rate   │    │  • API latency p99   │   │
│  │  · queue depth     │    │                      │   │
│  └────────────────────┘    └─────────────────────┘   │
└────────────────────────────────────────────────────────┘
```



## 📦 Docker Services Reference

```yaml
# docker-compose.yml summary
api         → FastAPI app          :8000
db          → PostgreSQL 16        :5432
redis       → Redis 7 Alpine       :6379
prometheus  → Prometheus v2.54.1   :9090
grafana     → Grafana 11.2.2       :3001 (admin/admin)
```

Prometheus scrape config lives in `ops/prometheus/prometheus.yml`.  
Grafana dashboards are provisioned from `ops/grafana/provisioning/`.

---

## 🧩 Dependency Order

```
Phase 0  Bootstrap (scaffold, config, docker)
  └─► Phase 1  Models + Security
        ├─► Phase 2  Auth
        ├─► Phase 3  Events
        └─► Phase 4  Seats  ←─ concurrency-critical (SELECT FOR UPDATE)
              └─► Phase 5  WebSocket Hub
                    ├─► Phase 6  Background Workers
                    ├─► Phase 7  Tickets & Checkout
                    │     └─► Phase 9  Demographics
                    └─► Phase 8  Dashboard
Phase 10  Virtual Queue  (independent, after Phase 5)
Phase 11  Recommendations  (independent, after Phase 1)
Phase 12  Hardening: CORS, rate limiting, validation
```

---

API docs:

- Swagger UI: `http://localhost:8000/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
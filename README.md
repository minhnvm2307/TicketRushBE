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

### Option 1. Clone & configure

```bash
git clone https://github.com/minhnvm2307/TicketRushBE.git
cd TicketRushBE

cp .env.example .env
# Edit .env — see variables below
```

```bash
# Then build your own backend container
docker compose up -d
```


### Option 2. Pull images & start (no build needed)

Pull a pre-built API image from the registry:

> ```bash
> docker pull minhnvm2307/ticketrush:latest
> # Then in docker-compose.yml replace `build: .` with `image: docker pull minhnvm2307/ticketrush:latest`
> docker compose up -d
> ```

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

---

## 🗂️ Project Structure

```
backend/
├── main.py                        # App entry, lifespan, middleware
├── core/
│   ├── config.py                  # Pydantic Settings from .env
│   ├── database.py                # Async SQLAlchemy engine + session
│   ├── redis.py                   # Async Redis client singleton
│   ├── security.py                # JWT encode/decode, bcrypt
│   ├── dependencies.py            # get_db, get_current_user, require_admin
│   └── exceptions.py              # Global exception handlers
├── app/
│   └── models/
│       ├── user.py                # User ORM model
│       ├── event.py               # Event, EventCategory, EventTag
│       ├── seat.py                # SeatZone, Seat
│       ├── ticket.py              # Ticket
│       ├── order.py               # Order, OrderItem
│       ├── interaction.py         # UserEventInteraction
│       └── queue.py               # QueueEntry
├── modules/
│   ├── auth/                      # Registration, login, /me
│   ├── events/                    # Event CRUD
│   ├── seats/                     # Zone config, seat map, hold logic
│   ├── tickets/                   # Checkout, QR, my-tickets
│   ├── dashboard/                 # Admin real-time stats
│   ├── demographics/              # Age/gender analytics
│   ├── recommendations/           # Content-based recommendation engine
│   └── queue/                     # Virtual waiting room
├── shared/
│   ├── models/                    # SQLAlchemy Base + all model imports
│   ├── schemas/                   # Shared Pydantic types (RecommendationItem…)
│   └── websocket_manager.py       # Broadcast hub (ConnectionManager)
└── workers/
    ├── seat_release.py            # APScheduler: release expired holds (60s)
    └── queue_processor.py         # APScheduler: pop queue batch (5s)
```

Each module follows:
```
modules/<name>/
├── router.py       # APIRouter (routes only, no logic)
├── service.py      # Business logic
├── repository.py   # DB queries (Repository Pattern)
└── schemas.py      # Pydantic request/response models
```

---

## 🛣️ API Reference

### Auth `/api/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/register` | Public | Register new account |
| `POST` | `/api/auth/login` | Public | Get JWT token |
| `GET` | `/api/auth/me` | Customer / Admin | Current user profile |

### Events `/api/events`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/events` | Public | List published events (`search`, `date_from`, `date_to`) |
| `GET` | `/api/events/:id` | Public | Event detail |
| `POST` | `/api/admin/events` | Admin | Create event |
| `PUT` | `/api/admin/events/:id` | Admin | Update event |
| `DELETE` | `/api/admin/events/:id` | Admin | Delete event |

### Seats `/api/seats`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/events/:id/seats` | Public | Full seat map (zones + status) |
| `POST` | `/api/seats/:id/hold` | Customer | Lock seat for 10 min |
| `DELETE` | `/api/seats/:id/hold` | Customer | Manual release |
| `POST` | `/api/admin/events/:id/zones` | Admin | Create zone + generate seats |
| `GET` | `/api/admin/events/:id/zones` | Admin | List zones |

### Tickets & Checkout

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/checkout` | Customer | Checkout held seats → tickets |
| `GET` | `/api/my-tickets` | Customer | My ticket list |
| `GET` | `/api/tickets/:id` | Customer | Single ticket |
| `GET` | `/api/tickets/:id/qr` | Customer | QR code image (PNG) |

### Admin Dashboard & Analytics

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/admin/dashboard/:event_id` | Admin | Revenue snapshot (HTTP poll) |
| `GET` | `/api/admin/demographics/:event_id` | Admin | Age bracket + gender breakdown |

### Virtual Queue

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/queue/join/:event_id` | Customer | Enter queue, get position |
| `GET` | `/api/queue/status/:event_id` | Customer | Current position |
| `GET` | `/api/queue/token/:event_id` | Customer | Claim access token |

### Recommendations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/recommendations` | Customer | Personalised event list |
| `POST` | `/api/interactions` | Customer | Log interaction (view / hold / purchase) |

### WebSocket Endpoints

| Path | Auth | Description |
|------|------|-------------|
| `/ws/events/:event_id` | Any | Real-time seat status stream |
| `/ws/admin/dashboard/:event_id` | Admin | Revenue + fill-rate push updates |

#### WebSocket Message Types

```jsonc
// Seat status changed
{ "type": "seat_status_changed", "seat_id": "uuid", "status": "locked", "locked_by": "user-uuid | null" }

// Dashboard push
{ "type": "dashboard_update", "event_id": "uuid", "revenue": 4200000, "fill_rate": 0.73 }
```

---


## 🗄️ Database Architecture

### Entity Relationship (Extended Schema)

```
users ──────────────────────────────────────────────┐
  │ id (UUID PK)                                     │
  │ email (unique)                                   │
  │ password_hash                                    │
  │ full_name                                        │
  │ date_of_birth                                    │
  │ gender ENUM(male,female,other)                   │
  │ role ENUM(customer,admin)                        │
  │ created_at                                       │
  │                                                  │
  ├─── tickets.user_id                               │
  ├─── seats.locked_by                               │
  ├─── user_event_interactions.user_id               │
  └─── orders.user_id                                │
                                                     │
events ─────────────────────────────────────────────┤
  │ id (UUID PK)                                     │
  │ title                                            │
  │ slug (unique)           ◄── added for recommend  │
  │ description                                      │
  │ short_description       ◄── added for recommend  │
  │ start_time / end_time                            │
  │ venue                                            │
  │ banner_url                                       │
  │ status ENUM(draft,published,cancelled)           │
  │ is_private                                       │
  │ theme                                            │
  │ created_at                                       │
  │                                                  │
  ├─── seat_zones.event_id                           │
  ├─── event_categories.event_id  ◄── new           │
  ├─── event_tags.event_id        ◄── new           │
  └─── user_event_interactions.event_id ◄── new     │
                                                     │
seat_zones ──────────────────────────────────────────┤
  │ id (UUID PK)                                     │
  │ event_id (FK → events)                           │
  │ name                                             │
  │ rows / cols                                      │
  │ price                                            │
  │ capacity                                         │
  │ color                                            │
  │                                                  │
  └─── seats.zone_id                                 │
                                                     │
seats ───────────────────────────────────────────────┤
  │ id (UUID PK)                                     │
  │ zone_id (FK → seat_zones)                        │
  │ row_index / col_index                            │
  │ label (e.g. "VIP-A3")                            │
  │ status ENUM(available,locked,sold)               │
  │ locked_by (FK → users, nullable)                 │
  │ locked_until (timestamp, nullable)               │
  │                                                  │
  └─── tickets.seat_id (unique)                      │
                                                     │
tickets ─────────────────────────────────────────────┤
  │ id (UUID PK)                                     │
  │ seat_id (FK → seats, unique)                     │
  │ user_id (FK → users)                             │
  │ order_item_id (FK → order_items, nullable)       │
  │ qr_code (base64 PNG)                             │
  │ status ENUM(valid,used,refunded)                 │
  │ purchased_at                                     │
                                                     │
orders ──────────────────────────────────────────────┤  ◄── new
  │ id (UUID PK)                                     │
  │ user_id (FK → users)                             │
  │ total_amount                                     │
  │ status ENUM(pending,paid,refunded)               │
  │ created_at                                       │
  │ paid_at (nullable)                               │
  │                                                  │
  └─── order_items.order_id                          │
                                                     │
order_items ─────────────────────────────────────────┤  ◄── new
  │ id (UUID PK)                                     │
  │ order_id (FK → orders)                           │
  │ ticket_id (FK → tickets, unique)                 │
  │ unit_price                                       │
                                                     │
event_categories ────────────────────────────────────┤  ◄── new (recommend)
  │ id (UUID PK)                                     │
  │ event_id (FK → events)                           │
  │ category  e.g. "music", "sport", "conference"    │
                                                     │
event_tags ──────────────────────────────────────────┤  ◄── new (recommend)
  │ id (UUID PK)                                     │
  │ event_id (FK → events)                           │
  │ tag  e.g. "k-pop", "outdoor", "family"           │
  | weight  FLOAT  -- view=1, hold=3, purchase=5     |
                                                     │
user_event_interactions ─────────────────────────────┘  ◄── new (recommend)
  id (UUID PK)
  user_id (FK → users)
  event_id (FK → events)
  interaction_type ENUM(view, hold, purchase)
  created_at
```

### New Tables Detail

```sql
-- Content signals for recommendation engine
CREATE TABLE event_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id    UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    category    VARCHAR(64) NOT NULL,
    UNIQUE (event_id, category)
);

CREATE TABLE event_tags (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id    UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    tag         VARCHAR(64) NOT NULL,
    UNIQUE (event_id, tag)
);

-- Behavioural signal for recommendation engine
CREATE TABLE user_event_interactions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id          UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    interaction_type  VARCHAR(16) NOT NULL,  -- view | hold | purchase
    weight            FLOAT NOT NULL DEFAULT 1.0,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX (user_id, event_id)
);

-- Order grouping (supports multi-seat checkout + future payments)
CREATE TABLE orders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id),
    total_amount BIGINT NOT NULL,  -- in VND (no decimals)
    status       VARCHAR(16) NOT NULL DEFAULT 'paid',
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE order_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID NOT NULL REFERENCES orders(id),
    ticket_id  UUID NOT NULL UNIQUE REFERENCES tickets(id),
    unit_price BIGINT NOT NULL
);
```

---

## 🤖 Content-Based Recommendation Design

### Approach: Score-only, no schema changes to existing modules

The recommendation engine operates entirely on `event_categories`, `event_tags`, and `user_event_interactions` — **no changes to any existing module schema**.

```
RecommendationItem (shared/schemas/recommendation.py)
  ├── event_id: str
  ├── title: str
  ├── score: float
  └── reasons: list[str]   ← human-readable: "Matches your interest in k-pop"
```

### Scoring algorithm

```
For each candidate event not yet purchased by user:

  category_score  = count(user's top categories ∩ event.categories)
  tag_score       = count(user's top tags ∩ event.tags)
  behaviour_score = SUM(interaction.weight) for this event
                    where: view=1, hold=3, purchase=5

  final_score = (category_score × 2) + (tag_score × 1.5) + behaviour_score
```

### Logging interactions — one lightweight endpoint

```
POST /api/interactions
Body: { "event_id": "uuid", "interaction_type": "view" }
```

The FE calls this endpoint on:
- Event detail page load → `view`
- Seat hold success → `hold` (already happens in seat service, just add a side-call)
- Checkout success → `purchase` (auto-logged inside `checkout` service)

This means **no changes** to existing seat or ticket module logic beyond one side-effect call — both still return their normal response schemas.

---

## 🔧 Extension Points

| Concern | Current | When to upgrade |
|---------|---------|-----------------|
| Migrations | `create_all()` | Switch to **Alembic** before first staging deploy |
| Queue state | Redis sorted set | Already Redis — scale TTL if > 10k concurrent |
| Checkout confirmation | Synchronous | Add **Kafka / RabbitMQ** if payment gateway goes async |
| Recommendations | In-process SQL scoring | Export to dedicated **ML service** when > 100k interactions |
| Metrics | Prometheus `/metrics` | Add custom business metrics: hold success rate, sell-through rate |

---

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

## Suggested CI/CD

- Lint: `ruff check .`
- Syntax gate: `python -m compileall app`
- Tests: `pytest`
- Build image: `docker build .`
- Deploy step: container registry + `docker compose pull && docker compose up -d`

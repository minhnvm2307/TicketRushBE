# TicketRush Backend

Python backend for the TicketRush business requirements. The design follows:

- `api -> services -> repositories -> database`
- FastAPI + SQLAlchemy + PostgreSQL
- JWT auth + RBAC
- seat hold with row-level locking
- background expiry job
- WebSocket event channels
- Prometheus metrics and Grafana provisioning
- schema prepared for content-based recommendations

## Main modules

- `app/api`: HTTP and WebSocket entrypoints
- `app/services`: business logic
- `app/repositories`: database access
- `app/models`: SQLAlchemy models
- `app/schemas`: request/response contracts
- `app/workers`: scheduled jobs
- `ops`: monitoring configs

## Recommendation-ready schema

Instead of only storing event title and description, the backend persists:

- `event_categories`
- `event_tags`
- `user_event_interactions`
- `orders` and `tickets`

That lets you build user profiles from viewed/held/purchased events and score new events by tag/category overlap without redesigning the database later.

## Redis usage

Redis is used for:

- virtual waiting room queue via sorted sets
- seat hold hot-state and TTL keys

PostgreSQL remains the source of truth for:

- users
- events
- seats
- orders
- tickets

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

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

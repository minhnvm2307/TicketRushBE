# Architecture Notes

## Why this is different from the Go sample

The Go sample is useful as a seed, but it does not satisfy the business requirements yet. The Python backend here restructures the project around:

- `routes/controllers`
- `services`
- `repositories`
- `SQLAlchemy models`
- `background workers`
- `observability`

## Core requirement mapping

- Auth + RBAC: `/api/auth/*`, JWT in `app/core/security.py`
- Event management: `/api/admin/events*`
- Seat map and seat states: `app/models/seat.py`
- Concurrency-safe hold: `SeatRepository.get_by_id_for_update`
- Hold expiry job: `app/workers/release_expired_holds.py`
- Checkout + QR payload: `app/services/checkout.py`
- Admin analytics: `app/services/dashboard.py`
- Virtual queue: `app/services/queue.py`
- WebSocket updates: `/api/ws/events/{event_id}`
- Recommendation-ready storage: `event_categories`, `event_tags`, `user_event_interactions`, `embedding`

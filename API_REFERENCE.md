# TicketRush Backend API Reference

## Common Rules

Base API path: `http://localhost:8000/api`

Protected endpoints require this header:

```http
Authorization: Bearer <access_token>
```

Write endpoints usually use:

```http
Content-Type: application/json
```

Standard success response format:

```json
{
  "success": true,
  "data": {}
}
```

Standard failed response format:

```json
{
  "success": false,
  "error": "message"
}
```

Response naming rules:
- Responses backed by `APIModel` are returned in `camelCase`.
- Plain `BaseModel` responses and raw `dict` values stay in `snake_case`.
- Request payloads use `snake_case`.

## Enum Reference

Use these values for enum-typed request and response fields in the API sections below.

| Enum field | Possible values |
| --- | --- |
| `gender` | `MALE`, `FEMALE`, `OTHER` |
| `role` | `CUSTOMER`, `ADMIN` |
| `status` for events | `DRAFT`, `PUBLISHED`, `CANCELLED` |
| `status` for seats | `AVAILABLE`, `SOLD` |
| `status` for held seats and websocket seat updates | `LOCKED` |
| `status` for tickets | `VALID`, `USED`, `REFUNDED` |
| `status` for orders | `PENDING`, `PAID`, `CANCELLED` |
| `interaction_type` | `VIEW`, `HOLD`, `PURCHASE` |

Special response types:
- `GET /metrics` returns Prometheus text, not JSON.
- `GET /api/tickets/{ticket_id}/qr` returns `image/png`, not JSON.
- WebSocket routes return JSON messages over the socket, not the HTTP success envelope.

## Auth APIs

### API: POST `http://localhost:8000/api/auth/register`

Input request:

- Header: `Content-Type: application/json`
- Body: JSON

samples:

```json
{
  "email": "user@example.com",
  "password": "Password123!",
  "full_name": "Nguyen Van A",
  "date_of_birth": "2000-01-15",
  "gender": "MALE"
}
```

Response format:

- Success status: `201 Created`
- Success body: standard envelope with `TokenResponse`
- Failed status: `400 Bad Request` or `422 Unprocessable Entity`
- Failed body: standard error envelope

samples:

Success:

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOi...",
    "tokenType": "bearer",
    "user": {
      "id": "c2d9f7a0-7d86-4e54-b3cf-5ccf5c1c9c15",
      "email": "user@example.com",
      "fullName": "Nguyen Van A",
      "role": "CUSTOMER"
    }
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "email already exists"
}
```

Description about API:
- Create a new user account.
- The password must be at least 8 characters.
- `date_of_birth` must be in the past.
- The API returns a login token immediately after registration.

### API: POST `http://localhost:8000/api/auth/login`

Input request:

- Header: `Content-Type: application/json`
- Body: JSON

samples:

```json
{
  "email": "user@example.com",
  "password": "Password123!"
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `TokenResponse`
- Failed status: `401 Unauthorized` or `422 Unprocessable Entity`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOi...",
    "tokenType": "bearer",
    "user": {
      "id": "c2d9f7a0-7d86-4e54-b3cf-5ccf5c1c9c15",
      "email": "user@example.com",
      "fullName": "Nguyen Van A",
      "role": "CUSTOMER"
    }
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "invalid email or password"
}
```

Description about API:
- Authenticate an existing user.
- Returns the access token and the current user profile.

### API: GET `http://localhost:8000/api/auth/me`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Body: none

samples:

```http
GET /api/auth/me HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `UserResponse`
- Failed status: `401 Unauthorized`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "id": "c2d9f7a0-7d86-4e54-b3cf-5ccf5c1c9c15",
    "email": "user@example.com",
    "fullName": "Nguyen Van A",
    "role": "CUSTOMER"
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "missing bearer token"
}
```

Description about API:
- Return the authenticated user profile.
- The token must be valid and the user must still exist.

## Event APIs

### API: GET `http://localhost:8000/api/events`

Input request:

- Query params:
  - `search` optional string
  - `date_from` optional datetime
  - `date_to` optional datetime
- Header: none

samples:

```http
GET /api/events?search=concert&date_from=2026-04-01T00:00:00Z&date_to=2026-12-31T23:59:59Z HTTP/1.1
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a list of public event items
- Failed status: `422 Unprocessable Entity`

samples:

Success:

```json
{
  "success": true,
  "data": [
    {
      "id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
      "title": "Summer Night Live",
      "slug": "summer-night-live",
      "start_time": "2026-06-01T19:00:00Z",
      "end_time": "2026-06-01T21:00:00Z",
      "venue": "Central Stadium",
      "banner_url": "https://example.com/banner.jpg",
      "lowest_price": 1500000,
      "categories": ["concert"],
      "tags": ["summer", "live"],
      "cosine_distance": null,
      "similarity_score": null
    }
  ]
}
```

Failed:

```json
{
  "success": false,
  "error": "[{\"type\": \"datetime_parsing\", \"loc\": [\"query\", \"date_from\"], ...}]"
}
```

Description about API:
- List public, published, non-private events.
- Search is optional.
- Response items use `snake_case` because the route returns raw dictionaries.

### API: GET `http://localhost:8000/api/events/{event_id}`

Input request:

- Path param: `event_id`
- Header: none

samples:

```http
GET /api/events/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2 HTTP/1.1
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `EventResponse`
- Failed status: `404 Not Found`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
    "title": "Summer Night Live",
    "slug": "summer-night-live",
    "description": "Main concert night",
    "shortDescription": "Open-air performance",
    "startTime": "2026-06-01T19:00:00Z",
    "endTime": "2026-06-01T21:00:00Z",
    "venue": "Central Stadium",
    "bannerUrl": "https://example.com/banner.jpg",
    "isPrivate": false,
    "theme": "minimal",
    "status": "PUBLISHED",
    "categories": ["concert"],
    "tags": ["summer", "live"],
    "zones": []
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "event not found"
}
```

Description about API:
- Return full event detail.
- Response uses `camelCase` because it is built from `APIModel`.

### API: GET `http://localhost:8000/api/events/{event_id}/seats`

Input request:

- Path param: `event_id`
- Header: none

samples:

```http
GET /api/events/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2/seats HTTP/1.1
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `SeatMapResponse`
- Failed status: usually none from the route itself; it can return an empty `zones` array if no data exists

samples:

Success:

```json
{
  "success": true,
  "data": {
    "eventId": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
    "zones": []
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "Internal server error"
}
```

Description about API:
- Return the seat map for an event.
- The response is `camelCase`.
- Locked seats can appear with runtime status `LOCKED` when Redis holds are active.

## Seat APIs

### API: POST `http://localhost:8000/api/seats/{seat_id}/hold`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Path param: `seat_id`
- Body: JSON with `event_id`

samples:

```http
POST /api/seats/3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9/hold HTTP/1.1
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2"
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with seat hold data
- Failed status: `409 Conflict`, `422 Unprocessable Entity`, or `503 Service Unavailable`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "seat_id": "3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9",
    "status": "LOCKED",
    "locked_until": "2026-04-19T12:10:00Z"
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "Seat is already held by another user."
}
```

Description about API:
- Hold a seat for a limited time.
- Redis must be available.
- The seat must belong to the same event in the request body.

### API: DELETE `http://localhost:8000/api/seats/{seat_id}/hold`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Path param: `seat_id`
- Body: JSON with `event_id`

samples:

```http
DELETE /api/seats/3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9/hold HTTP/1.1
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2"
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a message
- Failed status: `400 Bad Request`, `422 Unprocessable Entity`, or `503 Service Unavailable`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "message": "Seat released successfully"
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "Seat is not held."
}
```

Description about API:
- Release a held seat.
- The seat can only be released by the same user who held it.
- Redis must be available.

## Checkout APIs

### API: POST `http://localhost:8000/api/checkout`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Body: JSON

samples:

```json
{
  "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
  "seat_ids": [
    "3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9",
    "cc7e9d54-1966-4f4f-9f3b-0b6ad71d2f7f"
  ]
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `CheckoutResponse`
- Failed status: `409 Conflict` or `422 Unprocessable Entity`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "orderId": "0aa6d8bc-28e8-41f6-8fd9-0d4f6f30b9df",
    "totalAmount": 3000000,
    "tickets": [
      {
        "ticketId": "b61f6b7f-3b0b-42a4-a0ee-4bdb0cc5f7d5",
        "eventId": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
        "seatId": "3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9",
        "qrCode": "iVBORw0KGgoAAAANSUhEUgAA...",
        "status": "VALID",
        "purchasedAt": "2026-04-19T11:20:00Z"
      }
    ]
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "Seat 3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9 is held by another user."
}
```

Description about API:
- Convert held seats into paid tickets.
- All seats in the request must still be locked by the current user.
- Redis is required.

### API: GET `http://localhost:8000/api/my-tickets`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Body: none

samples:

```http
GET /api/my-tickets HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a list of `TicketDetailResponse`
- Failed status: `401 Unauthorized`

samples:

Success:

```json
{
  "success": true,
  "data": [
    {
      "ticketId": "b61f6b7f-3b0b-42a4-a0ee-4bdb0cc5f7d5",
      "qrCode": "iVBORw0KGgoAAAANSUhEUgAA...",
      "status": "VALID",
      "purchasedAt": "2026-04-19T11:20:00Z",
      "seat": {
        "id": "3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9",
        "label": "VIP-A01",
        "rowIndex": 0,
        "colIndex": 0,
        "status": "SOLD"
      },
      "zone": {
        "id": "f4bb2a38-5ecb-4d62-bfb4-2d5f0d19ea48",
        "name": "VIP",
        "color": "#d4af37",
        "price": 1500000
      },
      "event": {
        "id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
        "title": "Summer Night Live",
        "slug": "summer-night-live",
        "venue": "Central Stadium",
        "startTime": "2026-06-01T19:00:00Z",
        "endTime": "2026-06-01T21:00:00Z",
        "bannerUrl": "https://example.com/banner.jpg"
      }
    }
  ]
}
```

Failed:

```json
{
  "success": false,
  "error": "missing bearer token"
}
```

Description about API:
- Return all tickets owned by the current user.
- The response is `camelCase`.

### API: GET `http://localhost:8000/api/tickets/{ticket_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `ticket_id`

samples:

```http
GET /api/tickets/b61f6b7f-3b0b-42a4-a0ee-4bdb0cc5f7d5 HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `TicketDetailResponse`
- Failed status: `404 Not Found` or `401 Unauthorized`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "ticketId": "b61f6b7f-3b0b-42a4-a0ee-4bdb0cc5f7d5",
    "qrCode": "iVBORw0KGgoAAAANSUhEUgAA...",
    "status": "VALID",
    "purchasedAt": "2026-04-19T11:20:00Z",
    "seat": {
      "id": "3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9",
      "label": "VIP-A01",
      "rowIndex": 0,
      "colIndex": 0,
      "status": "SOLD"
    },
    "zone": {
      "id": "f4bb2a38-5ecb-4d62-bfb4-2d5f0d19ea48",
      "name": "VIP",
      "color": "#d4af37",
      "price": 1500000
    },
    "event": {
      "id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
      "title": "Summer Night Live",
      "slug": "summer-night-live",
      "venue": "Central Stadium",
      "startTime": "2026-06-01T19:00:00Z",
      "endTime": "2026-06-01T21:00:00Z",
      "bannerUrl": "https://example.com/banner.jpg"
    }
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "ticket not found"
}
```

Description about API:
- Return one ticket detail.
- The ticket must belong to the current user.

### API: GET `http://localhost:8000/api/tickets/{ticket_id}/qr`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `ticket_id`

samples:

```http
GET /api/tickets/b61f6b7f-3b0b-42a4-a0ee-4bdb0cc5f7d5/qr HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: raw PNG image
- Failed status: `404 Not Found` or `401 Unauthorized`

samples:

Success:

```text
Content-Type: image/png
<binary PNG content>
```

Failed:

```json
{
  "success": false,
  "error": "ticket not found"
}
```

Description about API:
- Download the QR image for a ticket.
- The QR payload is stored as base64 and returned as PNG bytes.

## Admin APIs

### API: POST `http://localhost:8000/api/admin/events`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Body: JSON

samples:

```json
{
  "title": "Summer Night Live",
  "description": "Main concert night",
  "short_description": "Open-air performance",
  "start_time": "2026-06-01T19:00:00Z",
  "end_time": "2026-06-01T21:00:00Z",
  "venue": "Central Stadium",
  "banner_url": "https://example.com/banner.jpg",
  "is_private": false,
  "theme": "minimal",
  "status": "PUBLISHED",
  "categories": ["concert"],
  "tags": ["summer", "live"],
  "zones": [
    {
      "name": "VIP",
      "rows": 2,
      "cols": 4,
      "price": 1500000,
      "color": "#d4af37",
      "capacity": 8
    }
  ]
}
```

Response format:

- Success status: `201 Created`
- Success body: standard envelope with `EventResponse`
- Failed status: `403 Forbidden` or `422 Unprocessable Entity`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
    "title": "Summer Night Live",
    "slug": "summer-night-live",
    "description": "Main concert night",
    "shortDescription": "Open-air performance",
    "startTime": "2026-06-01T19:00:00Z",
    "endTime": "2026-06-01T21:00:00Z",
    "venue": "Central Stadium",
    "bannerUrl": "https://example.com/banner.jpg",
    "isPrivate": false,
    "theme": "minimal",
    "status": "PUBLISHED",
    "categories": ["concert"],
    "tags": ["summer", "live"],
    "zones": []
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "admin only"
}
```

Description about API:
- Create a new event.
- This route is admin-only.
- The response is `camelCase`.

### API: POST `http://localhost:8000/api/admin/events/reindex-embeddings`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Query param: `force` optional boolean, default `true`

samples:

```http
POST /api/admin/events/reindex-embeddings?force=true HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a raw dictionary
- Failed status: `403 Forbidden`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "updated_events": 12,
    "force": true
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "admin only"
}
```

Description about API:
- Rebuild embeddings for public events.
- `force=true` reindexes all public events.
- Response keys stay `snake_case`.

### API: PUT `http://localhost:8000/api/admin/events/{event_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Path param: `event_id`
- Body: JSON

samples:

```json
{
  "title": "Summer Night Live Updated",
  "description": "Main concert night updated",
  "short_description": "Open-air performance",
  "start_time": "2026-06-01T19:00:00Z",
  "end_time": "2026-06-01T21:00:00Z",
  "venue": "Central Stadium",
  "banner_url": "https://example.com/banner.jpg",
  "is_private": false,
  "theme": "minimal",
  "status": "PUBLISHED",
  "categories": ["concert"],
  "tags": ["summer", "live"],
  "zones": []
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `EventResponse`
- Failed status: `403 Forbidden` or `404 Not Found`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
    "title": "Summer Night Live Updated",
    "slug": "summer-night-live-updated",
    "description": "Main concert night updated",
    "shortDescription": "Open-air performance",
    "startTime": "2026-06-01T19:00:00Z",
    "endTime": "2026-06-01T21:00:00Z",
    "venue": "Central Stadium",
    "bannerUrl": "https://example.com/banner.jpg",
    "isPrivate": false,
    "theme": "minimal",
    "status": "PUBLISHED",
    "categories": ["concert"],
    "tags": ["summer", "live"],
    "zones": []
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "event not found"
}
```

Description about API:
- Update an existing event.
- This route is admin-only.
- Returns `404` when the event does not exist.

### API: DELETE `http://localhost:8000/api/admin/events/{event_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `event_id`

samples:

```http
DELETE /api/admin/events/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2 HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `deleted: true`
- Failed status: `403 Forbidden` or `404 Not Found`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "deleted": true
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "event not found"
}
```

Description about API:
- Delete an event.
- The route decorator declares `204`, but the handler actually returns `200`.
- The event cannot be deleted if it already has sold seats.

### API: GET `http://localhost:8000/api/admin/dashboard/{event_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `event_id`

samples:

```http
GET /api/admin/dashboard/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2 HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a raw dictionary
- Failed status: `403 Forbidden`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
    "sold_count": 120,
    "locked_count": 8,
    "available_count": 72,
    "revenue": 180000000
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "admin only"
}
```

Description about API:
- Return dashboard metrics for an event.
- Response keys stay `snake_case`.
- This route does not raise a not-found error in the route layer.

### API: GET `http://localhost:8000/api/admin/demographics/{event_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `event_id`

samples:

```http
GET /api/admin/demographics/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2 HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a raw dictionary
- Failed status: `403 Forbidden`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
    "age_distribution": {
      "18-25": 30,
      "26-35": 60
    },
    "gender_distribution": {
      "MALE": 55,
      "FEMALE": 35
    }
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "admin only"
}
```

Description about API:
- Return ticket buyer demographics.
- Response keys stay `snake_case`.
- The route returns aggregated counts.

### API: GET `http://localhost:8000/api/admin/events/{event_id}/zones`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `event_id`

samples:

```http
GET /api/admin/events/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2/zones HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a list of zones
- Failed status: `403 Forbidden`

samples:

Success:

```json
{
  "success": true,
  "data": [
    {
      "id": "f4bb2a38-5ecb-4d62-bfb4-2d5f0d19ea48",
      "name": "VIP",
      "rows": 2,
      "cols": 4,
      "capacity": 8,
      "price": 1500000,
      "color": "#d4af37",
      "seats": []
    }
  ]
}
```

Failed:

```json
{
  "success": false,
  "error": "admin only"
}
```

Description about API:
- Return all seat zones for an event.
- Response is `camelCase` because it uses `SeatMapZoneResponse`.

### API: POST `http://localhost:8000/api/admin/events/{event_id}/zones`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Path param: `event_id`
- Body: JSON

samples:

```json
{
  "name": "VIP",
  "rows": 2,
  "cols": 4,
  "price": 1500000,
  "color": "#d4af37",
  "capacity": 8
}
```

Response format:

- Success status: `201 Created`
- Success body: standard envelope with a zone object
- Failed status: `403 Forbidden` or `422 Unprocessable Entity`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "id": "f4bb2a38-5ecb-4d62-bfb4-2d5f0d19ea48",
    "name": "VIP",
    "rows": 2,
    "cols": 4,
    "capacity": 8,
    "price": 1500000,
    "color": "#d4af37",
    "seats": []
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "admin only"
}
```

Description about API:
- Create a new seat zone for an event.
- Seats for the zone are generated automatically.
- Response is `camelCase`.

## Queue APIs

### API: GET `http://localhost:8000/api/queue/status/{event_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `event_id`

samples:

```http
GET /api/queue/status/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2 HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `QueueStatus`
- Failed status: `401 Unauthorized` or `503 Service Unavailable`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "position": 3,
    "total_users": 200,
    "is_in_queue": true,
    "has_access": false,
    "access_expires_in": null
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "Redis is not enabled or connected"
}
```

Description about API:
- Show the current queue status for the user.
- Response keys stay `snake_case`.

### API: POST `http://localhost:8000/api/queue/join/{event_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Path param: `event_id`

samples:

```http
POST /api/queue/join/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2 HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `QueueStatus`
- Failed status: `401 Unauthorized` or `503 Service Unavailable`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "position": 1,
    "total_users": 201,
    "is_in_queue": true,
    "has_access": false,
    "access_expires_in": null
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "Redis is not enabled or connected"
}
```

Description about API:
- Join the queue for an event.
- If the user already has access or is already in the queue, the current status is returned.

## Recommendation API

### API: GET `http://localhost:8000/api/recommendations/me`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Body: none

samples:

```http
GET /api/recommendations/me HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a list of recommendation items
- Failed status: `401 Unauthorized`

samples:

Success:

```json
{
  "success": true,
  "data": [
    {
      "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
      "title": "Summer Night Live",
      "score": 6.5,
      "reasons": ["matches category 'concert'", "similar tag 'summer'"]
    }
  ]
}
```

Failed:

```json
{
  "success": false,
  "error": "missing bearer token"
}
```

Description about API:
- Return personalized event recommendations.
- If there is no interaction history, the API returns an empty list.
- Response items stay in `snake_case`.

## WebSocket APIs

### API: WS `ws://localhost:8000/api/ws/events/{event_id}`

Input request:

- No authorization header required
- Path param: `event_id`
- Client must send text frames to keep the socket alive

samples:

```text
ws://localhost:8000/api/ws/events/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2
```

Response format:

- Success status: WebSocket connection open
- Success messages: JSON events on the socket
- Failed status: WebSocket disconnect

samples:

Success message:

```json
{
  "type": "seat_status_changed",
  "seat_id": "3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9",
  "status": "LOCKED",
  "locked_by": "c2d9f7a0-7d86-4e54-b3cf-5ccf5c1c9c15",
  "locked_until": "2026-04-19T12:10:00Z"
}
```

Failed:

```text
socket closed
```

Description about API:
- Broadcast seat and ticket state changes to connected clients.
- This socket is public.

### API: WS `ws://localhost:8000/api/ws/admin/dashboard/{event_id}?token=<jwt>`

Input request:

- Query param: `token`
- Path param: `event_id`
- The token must belong to an admin user

samples:

```text
ws://localhost:8000/api/ws/admin/dashboard/1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2?token=eyJhbGciOi...
```

Response format:

- Success status: WebSocket connection open
- Success messages: initial `dashboard_update` plus future `dashboard_update` payloads
- Failed status: WebSocket close with code `1008`

samples:

Success message:

```json
{
  "type": "dashboard_update",
  "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
  "sold_count": 120,
  "locked_count": 8,
  "available_count": 72,
  "revenue": 180000000
}
```

Failed:

```text
close code 1008
```

Description about API:
- Stream dashboard metrics for admins.
- The token is passed through the query string.
- The connection is rejected if the token is invalid or the user is not an admin.

## Utility APIs

### API: GET `http://localhost:8000/health`

Input request:

- Header: none
- Body: none

samples:

```http
GET /health HTTP/1.1
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope
- Failed status: `500 Internal Server Error`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "status": "ok"
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "Internal server error"
}
```

Description about API:
- Check whether the backend is running.

### API: GET `http://localhost:8000/metrics`

Input request:

- Header: none
- Body: none

samples:

```http
GET /metrics HTTP/1.1
```

Response format:

- Success status: `200 OK`
- Success body: Prometheus metrics text
- Failed status: `500 Internal Server Error`

samples:

Success:

```text
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",route="/health",status="200"} 1
```

Failed:

```json
{
  "success": false,
  "error": "Internal server error"
}
```

Description about API:
- Expose application metrics for Prometheus.
- This endpoint does not use the JSON response envelope.

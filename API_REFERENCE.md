# TicketRush Backend API Reference

## UPDATE SUMMARY:
- EVENTS: event can be FREE or PAID required (determined by ticket_type and seating_type)
- Remove tags table (keep only "categories")
- ADMIN: admin will only manage event that they hosted

> Note for frontend (optional): `theme` features of events used for design the thema page when customer clicked on event, admin can choose the background theme for their events
> > Design the dashboard view (explore view in multiple section: recently buyed, hot events, categories filtering page,...)

## Upcomming update: 
- add maximum ticket user can book
- stored seat_zone in flexible way (not only hectangle shape)

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

> New enum types: events can be free (no need to choose seat)

| Enum field | Possible values |
| --- | --- |
| `ticket_type` | `FREE`, `PAID` |
| `seating_type` | `ASSIGNED`, `GENERAL_ADMISSION` |
| `zone_type` | `ASSIGNED`, `GENERAL_ADMISSION` |

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
- `full_name` is trimmed and must be at least 2 characters after trimming.
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
- `password` must be a non-empty string.
- Returns the access token and the current user profile.

### API: POST `http://localhost:8000/api/auth/forgot-password`

Input request:

- Header: `Content-Type: application/json`
- Body: JSON
- Optional environment for email delivery: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`
- Optional environment for code expiry: `PASSWORD_RESET_CODE_TTL_MINUTES`

samples:

```json
{
  "email": "user@example.com"
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a generic message
- Failed status: `422 Unprocessable Entity` or `503 Service Unavailable`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "message": "If the email exists, a verification code has been sent."
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "unable to send email"
}
```

Description about API:
- Generate a 6-digit verification code for password reset and send it by email.
- The response is intentionally generic so attackers cannot discover registered emails.
- The verification code is stored as a hash in Redis when Redis is enabled. In local/dev without Redis, a temporary in-memory store is used.
- If SMTP settings are missing, the email service currently no-ops so you can add real email credentials later without changing the API.

### API: POST `http://localhost:8000/api/auth/reset-password`

Input request:

- Header: `Content-Type: application/json`
- Body: JSON

samples:

```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "NewPassword123!"
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with a message
- Failed status: `400 Bad Request` or `422 Unprocessable Entity`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "message": "Password has been reset."
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "invalid or expired verification code"
}
```

Description about API:
- Reset password using email, 6-digit code, and a new password.
- `new_password` must be 8 to 255 characters.
- A verification code can be used only once and is deleted after a successful reset.

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
    "dateOfBirth": "2000-01-15",
    "gender": "MALE",
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

### API: PATCH `http://localhost:8000/api/auth/me`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Body: JSON with at least one editable profile field

samples:

```json
{
  "full_name": "Nguyen Van B",
  "date_of_birth": "2001-02-20",
  "gender": "FEMALE"
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with the updated profile
- Failed status: `401 Unauthorized`, `404 Not Found`, or `422 Unprocessable Entity`

samples:

Success:

```json
{
  "success": true,
  "data": {
    "id": "c2d9f7a0-7d86-4e54-b3cf-5ccf5c1c9c15",
    "email": "user@example.com",
    "fullName": "Nguyen Van B",
    "dateOfBirth": "2001-02-20",
    "gender": "FEMALE",
    "role": "CUSTOMER"
  }
}
```

Failed:

```json
{
  "success": false,
  "error": "[{\"type\": \"value_error\", \"loc\": [\"body\"], ...}]"
}
```

Description about API:
- Update only the authenticated user's editable profile fields: `full_name`, `date_of_birth`, and `gender`.
- `email`, `password_hash`, and `role` cannot be changed through this endpoint.
- `full_name` is trimmed and must be at least 2 characters after trimming.
- `date_of_birth` must be in the past.
- Empty bodies and explicit `null` values are rejected.

## Event APIs (BIG UPDATE)

#### UPDATE-1: Event have two types: FREE or PAID
FREE type not require choosing
#### UPDATE-2: Event have max_capacity, max_bookable

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
          "id": "3705501d-9924-443d-9c4a-ff515743a2a6",
          "title": "K-Pop Dance Battle",
          "slug": "kpop-dance-battle",
          "start_time": "2026-05-10T07:00:00+00:00",
          "end_time": "2026-05-10T11:00:00+00:00",
          "venue": "AEON Mall Long Bien",
          "banner_url": "https://images.unsplash.com/photo-1547153760-18fc86324498",
          "lowest_price": 0.0,
            "categories": [
              {
                "id": "ea37afa6-0700-4f99-93f1-01541ddfdc1d",
                "name": "entertainment",
                "createdAt": "2026-05-02T04:40:36.712599Z",
                "updatedAt": "2026-05-02T04:40:36.712599Z"
              }
            ],
          "max_capacity": 23, // (nullable)
          "cosine_distance": 0.4288503953471895,
          "similarity_score": 0.7855748023264053
      },
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
- Top-level event fields use `snake_case` because the route returns raw dictionaries. Nested category objects use the `CategoryResponse` shape.

### API: GET `http://localhost:8000/api/events/{event_id}`

> NOTE: event can have seat-zone or not (zones = [])

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
  "success":true,
  "data": {
    "id":"163474dd-2d96-4fcf-8052-18b037272e66","title":"V-Pop Summer Night","slug":"vpop-night-2026","description":"Dem nhac V-Pop quy mo lon voi nhieu headliner va san khau LED ngoai troi.","shortDescription":"Concert V-Pop mua he","startTime":"2026-06-20T12:00:00Z","endTime":"2026-06-20T16:00:00Z",
    "venue":"My Dinh National Stadium","bannerUrl":"https://images.unsplash.com/photo-1470225620780-dba8ba36b745",
    "isPrivate":false,
    "theme":"music-vibrant",
    "status":"PUBLISHED",
    "categories": [
      {
        "id": "bd35fda2-6005-4b42-b898-58d7b0591a81",
        "name": "music",
        "createdAt": "2026-05-02T04:40:36.712599Z",
        "updatedAt": "2026-05-02T04:40:36.712599Z"
      }
    ],
    "zones": [
      {
        "id":"a4190480-8dfc-4486-a375-7dbf8de2abd8","name":"VIP",
        "rows":6,
        "cols":8,
        "price":1800000.0,
        "capacity":48,
        "color":"#F06292",
        "seats":[
          {"id":"0958e193-7013-4075-9e5c-97013fd4a980","label":"VIP-A01","rowIndex":0,"colIndex":0,"status":"AVAILABLE","lockedBy":null,"lockedUntil":null
          },
          ...
        ]
      }
    ]
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

## Seat APIs (UPDATE)

#### UPDATE-1: seat_zone have capacity
#### UPDATE-2: seat have two types: ASSIGNED / GENERAL_ADMISSION
- ASSIGNED: need booking by customer (need to pay)
- GENERAL_ADMISSION: free seat (no payment)

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
- Hold a seat until the user's booking session expires.
- Redis must be available.
- The user must first start a booking session and receive `has_access=true` for the event.
- Multiple seats held by the same user for the same event share the same `locked_until`.
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

Assigned seating:

```json
{
  "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
  "seat_ids": [
    "3f1c0d5a-fc05-4f0a-bd48-3a1ebfd6d7b9",
    "cc7e9d54-1966-4f4f-9f3b-0b6ad71d2f7f"
  ]
}
```

General admission:

```json
{
  "event_id": "1df1d7c6-7f22-4f31-a5aa-0e7eb3e9f9b2",
  "seat_ids": [],
  "quantity": 1
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
- Convert held seats or general-admission quantity into tickets.
- For FREE events, checkout allows exactly 1 ticket per request.
- For ASSIGNED events, all seats in the request must still be locked by the current user.
- For GENERAL_ADMISSION events, `seat_ids` can be empty and `quantity` is used.
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

## Admin APIs (UPDATE)

#### UPDATE-1: Each admin is a user that have can host a event, and manage their own events
#### UPDATE-2: Validate the price of zone and ticketprice
- IF ticket_type is FREE, price must be 0
- IF ticket_type is PAID, price must > 0

### API: GET `http://localhost:8000/api/admin/events`

List owner's events

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
  "categories":[
    {
      "id":"58881584-8d6b-41aa-9595-e990f5e57a82",
      "name":"technology",
      "createdAt":"2026-05-02T04:58:16.659608Z",
      "updatedAt":"2026-05-02T04:58:16.659608Z"
    }
  ],
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

- Success status: `200 OK`

Description about API:
- Get event that hosted by "admin-account".
- This route is admin-only.

### API: POST `http://localhost:8000/api/admin/events`

Create new event

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
  "categories": [
    {
      "id": "58881584-8d6b-41aa-9595-e990f5e57a82",
      "name": "technology",
      "createdAt": "2026-05-02T04:58:16.659608Z",
      "updatedAt": "2026-05-02T04:58:16.659608Z"
    }
  ],
  "category_ids": ["58881584-8d6b-41aa-9595-e990f5e57a82"], // Optional legacy fallback
  "zones": [
    {
      "name": "VIP",
      "rows": 2,
      "cols": 4,
      "price": 1500000,
      "color": "#d4af37",
    }
  ],
  "seating_type": "ASSIGNED"/"GENERAL_ADMISSION",
  "ticket_type": "FREE"/"PAID"
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
    "categories": [
      {
        "id": "58881584-8d6b-41aa-9595-e990f5e57a82",
        "name": "technology",
        "createdAt": "2026-05-02T04:58:16.659608Z",
        "updatedAt": "2026-05-02T04:58:16.659608Z"
      }
    ],
    "zones": []
  }
}
```

Failed (WHEN failed in validate price and ticket price):

```json
{
  "success":false,
  "error":"[{'type': 'value_error', 'loc': ('body',), 'msg': 'Value error, All zones must have a price of 0 for FREE ticket type', 'input': {'title': 'Test event 2', 'description': 'Main concert night', 'short_description': 'Open-air performance', 'start_time': '2026-06-01T19:00:00Z', 'end_time': '2026-06-01T21:00:00Z', 'venue': 'Central Stadium', 'banner_url': 'https://example.com/banner.jpg', 'is_private': False, 'theme': 'minimal', 'status': 'PUBLISHED', 'categories': ['music', 'technology'], 'zones': [{'name': 'NORMAL', 'rows': 10, 'cols': 14, 'price': 2, 'color': '#d4af37'}], 'seating_type': 'ASSIGNED', 'ticket_type': 'FREE'}, 'ctx': {'error': ValueError('All zones must have a price of 0 for FREE ticket type')}}]"
}
```

Description about API:
- Create a new event.
- This route is admin-only.
- The response is `camelCase`.
- The `categories` request field must use the full `CategoryResponse` object shape copied from a list or detail response.

### API: PUT `http://localhost:8000/api/admin/events/{event_id}`

Input request:

- Header: `Authorization: Bearer <access_token>`
- Header: `Content-Type: application/json`
- Path param: `event_id`
- Body: JSON

samples:

```json
{
  "status": "DRAFT"
}
```

Response format:

- Success status: `200 OK`
- Success body: standard envelope with `EventResponse`
- Failed status: `403 Forbidden`, `404 Not Found`, or `409 Conflict`

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
    "categories": [
      {
        "id": "58881584-8d6b-41aa-9595-e990f5e57a82",
        "name": "technology",
        "createdAt": "2026-05-02T04:58:16.659608Z",
        "updatedAt": "2026-05-02T04:58:16.659608Z"
      }
    ],
    "zones": []
  }
}
```

Description about API:
- Supports partial updates. You can send only the fields you want to change.
- Publishing/unpublishing by updating only `status` is supported.
- Updating `zones` is blocked with `409 Conflict` if the event already has sold seats.

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
- The `categories` request field must use the full `CategoryResponse` object shape copied from a list or detail response.

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
x
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
    "active_users": 200,
    "max_active_users": 200,
    "has_access": false,
    "notice": "Seat selection room is currently full. Please try again in a moment.",
    "session_expires_in": null
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
- Show the current seat-room access status for the user.
- There is no numbered waiting queue anymore.
- Seat selection and held-seat checkout share the same booking session TTL.
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
    "active_users": 142,
    "max_active_users": 200,
    "has_access": true,
    "notice": null,
    "session_expires_in": 900
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
- Request immediate access to the seat-selection room.
- If `active_users < max_active_users`, access is granted immediately.
- If the room is full, the API returns `has_access=false` with a human-readable `notice`.
- The returned `session_expires_in` is the single TTL used for seat selection and all holds made in that event.

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

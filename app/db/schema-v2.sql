-- ==============================================================================
-- TICKETRUSH — SCHEMA V2 (Redesigned)
-- PostgreSQL 16+
-- Changes vs v1:
--   • events: thêm host_id, ticket_type, seating_type, max_capacity
--   • seat_zones: thêm zone_type (ASSIGNED/GA), price DEFAULT 0
--   • seats: trả lại LOCKED vào enum, thêm locked_by + locked_until
--   • order_items / tickets: seat_id nullable → hỗ trợ GA
--   • order_items: thêm zone_id
--   • tickets: thêm zone_id
--   • Categories: tách bảng categories + many-to-many event_categories
--   • Bỏ: event_tags
-- ==============================================================================

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET row_security = off;

-- ------------------------------------------------------------------------------
-- EXTENSIONS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ------------------------------------------------------------------------------
-- AUTO-UPDATE updated_at
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------
-- ENUMS
-- ------------------------------------------------------------------------------
CREATE TYPE public.user_role_enum       AS ENUM ('CUSTOMER', 'ADMIN');
CREATE TYPE public.gender_enum          AS ENUM ('MALE', 'FEMALE', 'OTHER');

-- [FIX #1] ticket_type: phân biệt event free vs paid
CREATE TYPE public.ticket_type_enum     AS ENUM ('FREE', 'PAID');

-- [FIX #3] seating_type: event cần chọn chỗ hay không
CREATE TYPE public.seating_type_enum    AS ENUM ('ASSIGNED', 'GENERAL_ADMISSION');

CREATE TYPE public.event_status_enum    AS ENUM ('DRAFT', 'PUBLISHED', 'CANCELLED');

-- [FIX #3] zone_type: zone chọn ghế hay zone vào tự do
CREATE TYPE public.zone_type_enum       AS ENUM ('ASSIGNED', 'GENERAL_ADMISSION');

-- [FIX #3] LOCKED được trả lại — schema cũ đã bỏ nhầm, BRD yêu cầu hold 10 phút
CREATE TYPE public.seat_status_enum     AS ENUM ('AVAILABLE', 'LOCKED', 'SOLD');

CREATE TYPE public.order_status_enum    AS ENUM ('PENDING', 'PAID', 'CANCELLED');
CREATE TYPE public.ticket_status_enum   AS ENUM ('VALID', 'USED', 'REFUNDED');
CREATE TYPE public.interaction_type_enum AS ENUM ('VIEW', 'HOLD', 'PURCHASE');

-- ------------------------------------------------------------------------------
-- USERS
-- (Không đổi — chỉ giữ role CUSTOMER / ADMIN)
-- ------------------------------------------------------------------------------
CREATE TABLE public.users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    full_name     VARCHAR(255)  NOT NULL,
    date_of_birth DATE          NOT NULL,
    gender        public.gender_enum    NOT NULL,
    role          public.user_role_enum NOT NULL DEFAULT 'CUSTOMER',
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- EVENTS
-- [FIX #2] host_id → user với role=ADMIN đã tạo/host event này
-- [FIX #1] ticket_type → FREE hoặc PAID
-- [FIX #3] seating_type → ASSIGNED (có sơ đồ chỗ) hay GENERAL_ADMISSION
--          max_capacity  → tổng số người được tham dự (áp dụng khi seating_type=GA
--                          hoặc là cap cứng cho toàn event nếu muốn)
-- ------------------------------------------------------------------------------
CREATE TABLE public.events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- [FIX #2] ai là người tổ chức event
    host_id           UUID          NOT NULL REFERENCES public.users(id),

    title             VARCHAR(255)  NOT NULL,
    slug              VARCHAR(255)  NOT NULL UNIQUE,
    description       TEXT          NOT NULL,
    short_description VARCHAR(500)  NOT NULL,
    venue             VARCHAR(255)  NOT NULL,
    banner_url        VARCHAR(500),
    start_time        TIMESTAMPTZ   NOT NULL,
    end_time          TIMESTAMPTZ   NOT NULL,
    is_private        BOOLEAN       NOT NULL DEFAULT false,
    theme             VARCHAR(50)   NOT NULL DEFAULT 'minimal',
    status            public.event_status_enum NOT NULL DEFAULT 'DRAFT',

    -- [FIX #1] phân biệt free / paid rõ ràng
    ticket_type       public.ticket_type_enum  NOT NULL DEFAULT 'PAID',

    -- [FIX #3] event cần chọn chỗ ngồi cụ thể hay không
    seating_type      public.seating_type_enum NOT NULL DEFAULT 'ASSIGNED',

    -- [FIX #3] giới hạn tổng số người (nullable = không giới hạn)
    -- Với GA event: đây là cap tổng. Với ASSIGNED event: cap tự động = tổng seats.
    max_capacity      INTEGER       CHECK (max_capacity > 0),

    -- Explicit seat-map grid size. NULL for GENERAL_ADMISSION.
    seat_map_rows     INTEGER       CHECK (seat_map_rows > 0),
    seat_map_cols     INTEGER       CHECK (seat_map_cols > 0),

    -- Recommendation / AI
    embedding         vector(384),

    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ   -- soft delete
);

-- ------------------------------------------------------------------------------
-- CATEGORIES
-- Many-to-many giữa events và categories
-- ------------------------------------------------------------------------------
CREATE TABLE public.categories (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE public.event_categories (
    event_id    UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES public.categories(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_event_category UNIQUE (event_id, category_id)
);

-- ------------------------------------------------------------------------------
-- SEAT ZONES
-- [FIX #3] zone_type → mỗi zone có thể ASSIGNED hoặc GA độc lập
--           price DEFAULT 0 → free zone
--           capacity = số seats explicit với ASSIGNED, cap với GA
-- ------------------------------------------------------------------------------
CREATE TABLE public.seat_zones (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id   UUID          NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    name       VARCHAR(100)  NOT NULL,

    -- [FIX #3] loại zone: ASSIGNED → seats explicit, GA → chỉ đếm capacity
    zone_type  public.zone_type_enum NOT NULL DEFAULT 'ASSIGNED',

    -- Tổng sức chứa zone (bắt buộc với GA, auto-computed với ASSIGNED)
    capacity   INTEGER       NOT NULL CHECK (capacity > 0),

    -- [FIX #1] giá vé zone này — 0 = miễn phí
    price      NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (price >= 0),

    color      VARCHAR(20)   NOT NULL,

    created_at TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    CONSTRAINT uq_event_zone_name UNIQUE (event_id, name)
);

-- ------------------------------------------------------------------------------
-- SEATS
-- Chỉ tạo cho zone_type = ASSIGNED
-- [FIX #3] trả lại LOCKED + locked_by + locked_until
--           → thay vì dùng bảng riêng, giữ trên seat row cho đơn giản
-- ------------------------------------------------------------------------------
CREATE TABLE public.seats (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id    UUID          NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    zone_id     UUID          NOT NULL REFERENCES public.seat_zones(id) ON DELETE CASCADE,
    label       VARCHAR(30)   NOT NULL,
    row_index   SMALLINT      NOT NULL CHECK (row_index >= 0),
    col_index   SMALLINT      NOT NULL CHECK (col_index >= 0),
    display_order INTEGER     NOT NULL DEFAULT 0 CHECK (display_order >= 0),

    -- [FIX #3] LOCKED trả lại
    status      public.seat_status_enum NOT NULL DEFAULT 'AVAILABLE',

    -- [FIX #3] ai đang giữ ghế này (nullable = không ai giữ)
    locked_by   UUID          REFERENCES public.users(id) ON DELETE SET NULL,
    locked_until TIMESTAMPTZ,

    CONSTRAINT uq_seats_event_position UNIQUE (event_id, row_index, col_index),
    CONSTRAINT uq_seats_event_label UNIQUE (event_id, label),
    -- locked_by và locked_until phải cùng null hoặc cùng có giá trị
    CONSTRAINT chk_lock_consistency CHECK (
        (locked_by IS NULL AND locked_until IS NULL)
        OR (locked_by IS NOT NULL AND locked_until IS NOT NULL)
    )
);

-- ------------------------------------------------------------------------------
-- ORDERS
-- Thêm event_id để query dashboard theo event dễ hơn
-- ------------------------------------------------------------------------------
CREATE TABLE public.orders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID          NOT NULL REFERENCES public.users(id),
    -- Denormalize event_id lên orders để query nhanh hơn (dashboard, demographics)
    event_id     UUID          NOT NULL REFERENCES public.events(id),
    status       public.order_status_enum NOT NULL DEFAULT 'PENDING',
    -- [FIX #1] total_amount = 0 với free event (không cần nullable)
    total_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    paid_at      TIMESTAMPTZ
);

-- ------------------------------------------------------------------------------
-- ORDER ITEMS
-- [FIX #3] seat_id nullable → hỗ trợ GA (không chọn ghế cụ thể)
--           thêm zone_id → biết item thuộc zone nào dù seat_id null
-- ------------------------------------------------------------------------------
CREATE TABLE public.order_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID          NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    event_id   UUID          NOT NULL REFERENCES public.events(id) ON DELETE RESTRICT,
    zone_id    UUID          NOT NULL REFERENCES public.seat_zones(id) ON DELETE RESTRICT,

    -- nullable: ASSIGNED zone → có seat_id; GA zone → NULL
    seat_id    UUID          REFERENCES public.seats(id) ON DELETE RESTRICT,

    -- Snapshot tại thời điểm mua (giữ lại kể cả seat bị đổi sau)
    zone_name  VARCHAR(100)  NOT NULL,
    seat_label VARCHAR(50),       -- NULL nếu GA

    -- [FIX #1] unit_price = 0 nếu free
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (unit_price >= 0),

    -- Chỉ enforce unique khi có seat_id (ASSIGNED)
    CONSTRAINT uq_order_item_seat UNIQUE (seat_id)
);

-- ------------------------------------------------------------------------------
-- TICKETS
-- [FIX #3] seat_id nullable, thêm zone_id
-- [FIX #1] ticket tồn tại cả với free event
-- ------------------------------------------------------------------------------
CREATE TABLE public.tickets (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id     UUID          NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    event_id     UUID          NOT NULL REFERENCES public.events(id) ON DELETE RESTRICT,
    zone_id      UUID          NOT NULL REFERENCES public.seat_zones(id) ON DELETE RESTRICT,

    -- nullable: ASSIGNED → có seat; GA → NULL
    seat_id      UUID          REFERENCES public.seats(id) ON DELETE RESTRICT,

    user_id      UUID          NOT NULL REFERENCES public.users(id),
    qr_code      TEXT          NOT NULL,
    status       public.ticket_status_enum NOT NULL DEFAULT 'VALID',
    purchased_at TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- Chỉ enforce 1 ticket / ghế khi seat_id có giá trị
    CONSTRAINT uq_ticket_seat UNIQUE (seat_id)
);

-- ------------------------------------------------------------------------------
-- USER EVENT INTERACTIONS (giữ nguyên cho recommendation)
-- ------------------------------------------------------------------------------
CREATE TABLE public.user_event_interactions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID          NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    event_id         UUID          NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    interaction_type public.interaction_type_enum NOT NULL,
    occurred_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- TRIGGERS
-- ------------------------------------------------------------------------------
CREATE TRIGGER trg_users_modtime        BEFORE UPDATE ON public.users        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_events_modtime       BEFORE UPDATE ON public.events       FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_seat_zones_modtime   BEFORE UPDATE ON public.seat_zones   FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_orders_modtime       BEFORE UPDATE ON public.orders       FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_tickets_modtime      BEFORE UPDATE ON public.tickets      FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- ------------------------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------------------------
-- Events
CREATE INDEX ix_events_host_id        ON public.events (host_id);
CREATE INDEX ix_events_start_end      ON public.events (start_time, end_time);
CREATE INDEX ix_events_active         ON public.events (status)
    WHERE deleted_at IS NULL AND status = 'PUBLISHED';

-- Seat zones & seats
CREATE INDEX ix_seat_zones_event_id   ON public.seat_zones (event_id);
CREATE INDEX ix_seat_zones_active     ON public.seat_zones (event_id)
    WHERE deleted_at IS NULL;
CREATE INDEX ix_seats_event_id        ON public.seats (event_id);
CREATE INDEX ix_seats_zone_id         ON public.seats (zone_id);
-- Index cho background job giải phóng seat hết hạn
CREATE INDEX ix_seats_locked_until    ON public.seats (locked_until)
    WHERE status = 'LOCKED';

-- Orders & items
CREATE INDEX ix_orders_user_id        ON public.orders (user_id);
CREATE INDEX ix_orders_event_id       ON public.orders (event_id);
CREATE INDEX ix_order_items_order_id  ON public.order_items (order_id);
CREATE INDEX ix_order_items_event_id  ON public.order_items (event_id);
CREATE INDEX ix_order_items_zone_id   ON public.order_items (zone_id);

-- Tickets
CREATE INDEX ix_tickets_user_id       ON public.tickets (user_id);
CREATE INDEX ix_tickets_event_id      ON public.tickets (event_id);
CREATE INDEX ix_tickets_order_id      ON public.tickets (order_id);
CREATE INDEX ix_tickets_zone_id       ON public.tickets (zone_id);

-- Interactions
CREATE INDEX ix_interactions_user_id  ON public.user_event_interactions (user_id);
CREATE INDEX ix_interactions_event_id ON public.user_event_interactions (event_id);

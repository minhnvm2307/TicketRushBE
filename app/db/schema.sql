-- ==============================================================================
-- TICKETRUSH SAAS - HIGH-CONCURRENCY SCHEMA
-- PostgreSQL 16+ 
-- ==============================================================================

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ------------------------------------------------------------------------------
-- 1. EXTENSIONS & FUNCTIONS & TRIGGERS
-- ------------------------------------------------------------------------------
-- Extension bắt buộc cho UUID (mặc định có sẵn ở PG 13+)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Hàm tự động cập nhật updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------
-- 2. ENUMS
-- ------------------------------------------------------------------------------
CREATE TYPE public.event_status_enum AS ENUM ('DRAFT', 'PUBLISHED', 'CANCELLED');
CREATE TYPE public.gender_enum AS ENUM ('MALE', 'FEMALE', 'OTHER');
CREATE TYPE public.interaction_type_enum AS ENUM ('VIEW', 'HOLD', 'PURCHASE');
CREATE TYPE public.order_status_enum AS ENUM ('PENDING', 'PAID', 'CANCELLED');
CREATE TYPE public.seat_status_enum AS ENUM ('AVAILABLE', 'SOLD'); -- Đã xóa 'LOCKED'
CREATE TYPE public.ticket_status_enum AS ENUM ('VALID', 'USED', 'REFUNDED');
CREATE TYPE public.user_role_enum AS ENUM ('CUSTOMER', 'ADMIN');

-- ------------------------------------------------------------------------------
-- 3. TABLES
-- ------------------------------------------------------------------------------

CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender public.gender_enum NOT NULL,
    role public.user_role_enum NOT NULL DEFAULT 'CUSTOMER',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    is_private BOOLEAN NOT NULL DEFAULT false,
    theme VARCHAR(50) NOT NULL,
    venue VARCHAR(255) NOT NULL,
    banner_url VARCHAR(500),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status public.event_status_enum NOT NULL DEFAULT 'DRAFT',
    embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ -- Soft delete
);

CREATE TABLE public.event_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT uq_event_category UNIQUE (event_id, name)
);

CREATE TABLE public.event_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    weight NUMERIC(5,2) NOT NULL,
    CONSTRAINT uq_event_tag UNIQUE (event_id, name)
);

CREATE TABLE public.seat_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    rows SMALLINT NOT NULL CHECK (rows > 0),
    cols SMALLINT NOT NULL CHECK (cols > 0),
    price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
    capacity INTEGER NOT NULL CHECK (capacity >= 0),
    color VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ, -- Soft delete
    CONSTRAINT uq_event_zone_name UNIQUE (event_id, name)
);

CREATE TABLE public.seats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES public.seat_zones(id) ON DELETE CASCADE,
    label VARCHAR(30) NOT NULL,
    row_index SMALLINT NOT NULL CHECK (row_index >= 0),
    col_index SMALLINT NOT NULL CHECK (col_index >= 0),
    status public.seat_status_enum NOT NULL DEFAULT 'AVAILABLE',
    CONSTRAINT uq_zone_position UNIQUE (zone_id, row_index, col_index)
);

CREATE TABLE public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id),
    status public.order_status_enum NOT NULL DEFAULT 'PENDING',
    total_amount NUMERIC(12,2) NOT NULL CHECK (total_amount >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

CREATE TABLE public.order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE RESTRICT,
    seat_id UUID NOT NULL REFERENCES public.seats(id) ON DELETE RESTRICT,
    zone_name VARCHAR(100) NOT NULL,
    seat_label VARCHAR(50) NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    CONSTRAINT order_items_seat_id_key UNIQUE (seat_id)
);

CREATE TABLE public.tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE RESTRICT,
    seat_id UUID NOT NULL REFERENCES public.seats(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES public.users(id),
    qr_code TEXT NOT NULL,
    status public.ticket_status_enum NOT NULL DEFAULT 'VALID',
    purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ticket_seat UNIQUE (seat_id)
);

CREATE TABLE public.user_event_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    interaction_type public.interaction_type_enum NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 4. APPLY TRIGGERS
-- ------------------------------------------------------------------------------
CREATE TRIGGER update_users_modtime BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_events_modtime BEFORE UPDATE ON public.events FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_seat_zones_modtime BEFORE UPDATE ON public.seat_zones FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_orders_modtime BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_tickets_modtime BEFORE UPDATE ON public.tickets FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- ------------------------------------------------------------------------------
-- 5. OPTIMIZED INDEXING
-- ------------------------------------------------------------------------------
-- Foreign Key Indexes (B-Tree)
CREATE INDEX ix_seat_zones_event_id ON public.seat_zones (event_id);
CREATE INDEX ix_seats_zone_id ON public.seats (zone_id);
CREATE INDEX ix_orders_user_id ON public.orders (user_id);
CREATE INDEX ix_order_items_order_id ON public.order_items (order_id);
CREATE INDEX ix_order_items_event_id ON public.order_items (event_id);
CREATE INDEX ix_tickets_user_id ON public.tickets (user_id);
CREATE INDEX ix_tickets_order_id ON public.tickets (order_id);
CREATE INDEX ix_tickets_event_id ON public.tickets (event_id);
CREATE INDEX ix_interactions_user_id ON public.user_event_interactions (user_id);
CREATE INDEX ix_interactions_event_id ON public.user_event_interactions (event_id);

-- Filtering Indexes
CREATE INDEX ix_events_start_end ON public.events (start_time, end_time);

-- TỐI ƯU CỰC ĐẠI: Partial Index 
-- Chỉ index những sự kiện đang PUBLISHED và CHƯA BỊ XÓA (Giúp API GET /events nhanh gấp nhiều lần)
CREATE INDEX ix_events_active_published ON public.events (status) 
WHERE deleted_at IS NULL AND status = 'PUBLISHED';

-- Tương tự cho Seat Zones: Chỉ index những Zone chưa bị xóa
CREATE INDEX ix_seat_zones_active ON public.seat_zones (event_id) 
WHERE deleted_at IS NULL;
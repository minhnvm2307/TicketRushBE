-- This script is modified to be idempotent and use UUIDs as per the new schema.
-- User-specific data has been removed as requested.

-- ==============================================================================
-- 2. EVENTS
-- ==============================================================================
-- Use a temporary table to store generated event UUIDs
CREATE TEMP TABLE temp_events (
    slug VARCHAR(255) PRIMARY KEY,
    id UUID
);

INSERT INTO temp_events (slug, id) VALUES
('nexus-events-launch', gen_random_uuid()),
('kpop-superfest-2026', gen_random_uuid()),
('ai-unicorn-hackathon', gen_random_uuid());

INSERT INTO public.events (id, title, slug, description, short_description, is_private, theme, venue, banner_url, start_time, end_time, status)
SELECT id, 'Nexus Events Launch Summit', slug, 'Sự kiện ra mắt nền tảng quản lý sự kiện SaaS với tính năng sơ đồ ghế động.', 'SaaS Event Management Launch', false, 'tech-dark', 'Hanoi Innovation Hub', 'https://img.nexus.com/b1.jpg', '2026-10-15 09:00:00+07', '2026-10-15 18:00:00+07', 'PUBLISHED'
FROM temp_events WHERE slug = 'nexus-events-launch'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO public.events (id, title, slug, description, short_description, is_private, theme, venue, banner_url, start_time, end_time, status)
SELECT id, 'K-Pop SuperFest 2026', slug, 'Đại nhạc hội K-Pop quy mô lớn nhất Châu Á năm 2026.', 'K-Pop Music Festival', false, 'music-vibrant', 'My Dinh National Stadium', 'https://img.nexus.com/b2.jpg', '2026-12-20 19:00:00+07', '2026-12-20 23:00:00+07', 'PUBLISHED'
FROM temp_events WHERE slug = 'kpop-superfest-2026'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO public.events (id, title, slug, description, short_description, is_private, theme, venue, banner_url, start_time, end_time, status)
SELECT id, 'AI Unicorn Hackathon', slug, 'Cuộc thi xây dựng sản phẩm AI thực chiến (GenAI, RAG, Graph).', 'Hackathon AI Tech', false, 'tech-light', 'UET Campus, VNU', 'https://img.nexus.com/b3.jpg', '2026-08-10 08:00:00+07', '2026-08-12 17:00:00+07', 'PUBLISHED'
FROM temp_events WHERE slug = 'ai-unicorn-hackathon'
ON CONFLICT (slug) DO NOTHING;


-- ==============================================================================
-- 3. CONTENT SIGNALS (Categories & Tags)
-- ==============================================================================
INSERT INTO public.event_categories (event_id, name)
SELECT id, 'Conference' FROM temp_events WHERE slug = 'nexus-events-launch'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_categories (event_id, name)
SELECT id, 'Technology' FROM temp_events WHERE slug = 'nexus-events-launch'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_categories (event_id, name)
SELECT id, 'Music' FROM temp_events WHERE slug = 'kpop-superfest-2026'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_categories (event_id, name)
SELECT id, 'Entertainment' FROM temp_events WHERE slug = 'kpop-superfest-2026'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_categories (event_id, name)
SELECT id, 'Technology' FROM temp_events WHERE slug = 'ai-unicorn-hackathon'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_categories (event_id, name)
SELECT id, 'Education' FROM temp_events WHERE slug = 'ai-unicorn-hackathon'
ON CONFLICT (event_id, name) DO NOTHING;

INSERT INTO public.event_tags (event_id, name, weight)
SELECT id, 'saas', 1.0 FROM temp_events WHERE slug = 'nexus-events-launch'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_tags (event_id, name, weight)
SELECT id, 'startup', 1.5 FROM temp_events WHERE slug = 'nexus-events-launch'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_tags (event_id, name, weight)
SELECT id, 'k-pop', 1.0 FROM temp_events WHERE slug = 'kpop-superfest-2026'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_tags (event_id, name, weight)
SELECT id, 'outdoor', 1.0 FROM temp_events WHERE slug = 'kpop-superfest-2026'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_tags (event_id, name, weight)
SELECT id, 'ai', 2.0 FROM temp_events WHERE slug = 'ai-unicorn-hackathon'
ON CONFLICT (event_id, name) DO NOTHING;
INSERT INTO public.event_tags (event_id, name, weight)
SELECT id, 'machine-learning', 1.5 FROM temp_events WHERE slug = 'ai-unicorn-hackathon'
ON CONFLICT (event_id, name) DO NOTHING;


-- ==============================================================================
-- 4. SEAT ZONES
-- ==============================================================================
CREATE TEMP TABLE temp_zones (
    event_slug VARCHAR(255),
    name VARCHAR(100),
    id UUID
);

INSERT INTO temp_zones (event_slug, name, id) VALUES
('nexus-events-launch', 'VIP Area', gen_random_uuid()),
('nexus-events-launch', 'Standard', gen_random_uuid()),
('kpop-superfest-2026', 'Standing Pit', gen_random_uuid());

INSERT INTO public.seat_zones (id, event_id, name, rows, cols, price, capacity, color)
SELECT z.id, e.id, 'VIP Area', 2, 2, 1000000.00, 4, '#FFD700'
FROM temp_zones z JOIN temp_events e ON z.event_slug = e.slug WHERE z.name = 'VIP Area'
ON CONFLICT (event_id, name) DO NOTHING;

INSERT INTO public.seat_zones (id, event_id, name, rows, cols, price, capacity, color)
SELECT z.id, e.id, 'Standard', 2, 3, 200000.00, 6, '#CCCCCC'
FROM temp_zones z JOIN temp_events e ON z.event_slug = e.slug WHERE z.name = 'Standard'
ON CONFLICT (event_id, name) DO NOTHING;

INSERT INTO public.seat_zones (id, event_id, name, rows, cols, price, capacity, color)
SELECT z.id, e.id, 'Standing Pit', 2, 5, 500000.00, 10, '#00FF00'
FROM temp_zones z JOIN temp_events e ON z.event_slug = e.slug WHERE z.name = 'Standing Pit'
ON CONFLICT (event_id, name) DO NOTHING;


-- ==============================================================================
-- 5. SEATS
-- ==============================================================================
-- Event 1: Zone 1 (VIP)
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'VIP-A1', 0, 0, 'SOLD' FROM temp_zones WHERE name = 'VIP Area'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'VIP-A2', 0, 1, 'AVAILABLE' FROM temp_zones WHERE name = 'VIP Area'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'VIP-B1', 1, 0, 'AVAILABLE' FROM temp_zones WHERE name = 'VIP Area'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'VIP-B2', 1, 1, 'AVAILABLE' FROM temp_zones WHERE name = 'VIP Area'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;

-- Event 1: Zone 2 (Standard)
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'STD-A1', 0, 0, 'SOLD' FROM temp_zones WHERE name = 'Standard'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'STD-A2', 0, 1, 'SOLD' FROM temp_zones WHERE name = 'Standard'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'STD-A3', 0, 2, 'AVAILABLE' FROM temp_zones WHERE name = 'Standard'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'STD-B1', 1, 0, 'AVAILABLE' FROM temp_zones WHERE name = 'Standard'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'STD-B2', 1, 1, 'AVAILABLE' FROM temp_zones WHERE name = 'Standard'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'STD-B3', 1, 2, 'AVAILABLE' FROM temp_zones WHERE name = 'Standard'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;

-- Event 2: Zone 1 (Standing Pit)
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-1', 0, 0, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-2', 0, 1, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-3', 0, 2, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-4', 0, 3, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-5', 0, 4, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-6', 1, 0, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-7', 1, 1, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-8', 1, 2, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-9', 1, 3, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;
INSERT INTO public.seats (zone_id, label, row_index, col_index, status)
SELECT id, 'PIT-10', 1, 4, 'AVAILABLE' FROM temp_zones WHERE name = 'Standing Pit'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;

-- Clean up temp tables
DROP TABLE temp_events;
DROP TABLE temp_zones;
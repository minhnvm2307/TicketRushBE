-- ==============================================================================
-- 1. USERS (Tạo Admin và nhiều Customer để test concurrency)
-- ==============================================================================
INSERT INTO public.users (id, email, password_hash, full_name, date_of_birth, gender, role, created_at) VALUES
('u1', 'admin@ticketrush.com', '$2b$12$dummyhash1', 'System Admin', '1990-01-01', 'OTHER', 'ADMIN', NOW()),
('u2', 'minhnv@uet.vnu.edu.vn', '$2b$12$dummyhash2', 'Minh Nguyen', '2001-07-23', 'MALE', 'CUSTOMER', NOW()),
('u3', 'alice@startup.com', '$2b$12$dummyhash3', 'Alice Tran', '1999-05-15', 'FEMALE', 'CUSTOMER', NOW()),
('u4', 'bob.le@gmail.com', '$2b$12$dummyhash4', 'Bob Le', '2002-10-10', 'MALE', 'CUSTOMER', NOW()),
('u5', 'charlie@yahoo.com', '$2b$12$dummyhash5', 'Charlie Pham', '1998-12-05', 'MALE', 'CUSTOMER', NOW());


-- ==============================================================================
-- 2. EVENTS (Đa dạng sự kiện: Hội thảo, Nhạc hội, Hackathon)
-- ==============================================================================
INSERT INTO public.events (id, title, slug, description, short_description, is_private, theme, venue, banner_url, start_time, end_time, status, created_at) VALUES
('e1', 'Nexus Events Launch Summit', 'nexus-events-launch', 'Sự kiện ra mắt nền tảng quản lý sự kiện SaaS với tính năng sơ đồ ghế động.', 'SaaS Event Management Launch', false, 'tech-dark', 'Hanoi Innovation Hub', 'https://img.nexus.com/b1.jpg', '2026-10-15 09:00:00+07', '2026-10-15 18:00:00+07', 'PUBLISHED', NOW()),
('e2', 'K-Pop SuperFest 2026', 'kpop-superfest-2026', 'Đại nhạc hội K-Pop quy mô lớn nhất Châu Á năm 2026.', 'K-Pop Music Festival', false, 'music-vibrant', 'My Dinh National Stadium', 'https://img.nexus.com/b2.jpg', '2026-12-20 19:00:00+07', '2026-12-20 23:00:00+07', 'PUBLISHED', NOW()),
('e3', 'AI Unicorn Hackathon', 'ai-unicorn-hackathon', 'Cuộc thi xây dựng sản phẩm AI thực chiến (GenAI, RAG, Graph).', 'Hackathon AI Tech', false, 'tech-light', 'UET Campus, VNU', 'https://img.nexus.com/b3.jpg', '2026-08-10 08:00:00+07', '2026-08-12 17:00:00+07', 'PUBLISHED', NOW());


-- ==============================================================================
-- 3. CONTENT SIGNALS (Categories & Tags cho thuật toán Recommendation)
-- ==============================================================================
INSERT INTO public.event_categories (id, event_id, name) VALUES
('cat1', 'e1', 'Conference'),
('cat2', 'e1', 'Technology'),
('cat3', 'e2', 'Music'),
('cat4', 'e2', 'Entertainment'),
('cat5', 'e3', 'Technology'),
('cat6', 'e3', 'Education');

-- Trọng số (weight) được set theo hệ thập phân (numeric 5,2)
INSERT INTO public.event_tags (id, event_id, name, weight) VALUES
('tag1', 'e1', 'saas', 1.0),
('tag2', 'e1', 'startup', 1.5),
('tag3', 'e2', 'k-pop', 1.0),
('tag4', 'e2', 'outdoor', 1.0),
('tag5', 'e3', 'ai', 2.0),
('tag6', 'e3', 'machine-learning', 1.5);


-- ==============================================================================
-- 4. SEAT ZONES (Khởi tạo khu vực)
-- ==============================================================================
INSERT INTO public.seat_zones (id, event_id, name, rows, cols, price, capacity, color, created_at) VALUES
('z1_e1', 'e1', 'VIP Area', 2, 2, 1000000.00, 4, '#FFD700', NOW()),
('z2_e1', 'e1', 'Standard', 2, 3, 200000.00, 6, '#CCCCCC', NOW()),
('z1_e2', 'e2', 'Standing Pit', 2, 5, 500000.00, 10, '#00FF00', NOW());


-- ==============================================================================
-- 5. SEATS (Ma trận ghế chi tiết)
-- ==============================================================================
-- ==============================================================================
-- 5. SEATS (Ma trận ghế chi tiết) - Đã refactor để tránh lỗi syntax
-- ==============================================================================

-- Event 1: Zone 1 (VIP) - 4 ghế
INSERT INTO public.seats (id, zone_id, label, row_index, col_index, status, locked_by, locked_until) VALUES
('s1_z1_e1', 'z1_e1', 'VIP-A1', 0, 0, 'SOLD', NULL, NULL),
('s2_z1_e1', 'z1_e1', 'VIP-A2', 0, 1, 'LOCKED', 'u3', NOW() + INTERVAL '10 minutes'), 
('s3_z1_e1', 'z1_e1', 'VIP-B1', 1, 0, 'AVAILABLE', NULL, NULL),
('s4_z1_e1', 'z1_e1', 'VIP-B2', 1, 1, 'AVAILABLE', NULL, NULL);

-- Event 1: Zone 2 (Standard) - 6 ghế
INSERT INTO public.seats (id, zone_id, label, row_index, col_index, status, locked_by, locked_until) VALUES
('s1_z2_e1', 'z2_e1', 'STD-A1', 0, 0, 'SOLD', NULL, NULL),
('s2_z2_e1', 'z2_e1', 'STD-A2', 0, 1, 'SOLD', NULL, NULL),
('s3_z2_e1', 'z2_e1', 'STD-A3', 0, 2, 'AVAILABLE', NULL, NULL),
('s4_z2_e1', 'z2_e1', 'STD-B1', 1, 0, 'AVAILABLE', NULL, NULL),
('s5_z2_e1', 'z2_e1', 'STD-B2', 1, 1, 'AVAILABLE', NULL, NULL),
('s6_z2_e1', 'z2_e1', 'STD-B3', 1, 2, 'AVAILABLE', NULL, NULL);

-- Event 2: Zone 1 (Standing Pit) - 10 ghế
INSERT INTO public.seats (id, zone_id, label, row_index, col_index, status, locked_by, locked_until) VALUES
('s1_z1_e2', 'z1_e2', 'PIT-1', 0, 0, 'AVAILABLE', NULL, NULL),
('s2_z1_e2', 'z1_e2', 'PIT-2', 0, 1, 'AVAILABLE', NULL, NULL),
('s3_z1_e2', 'z1_e2', 'PIT-3', 0, 2, 'LOCKED', 'u5', NOW() + INTERVAL '5 minutes'),
('s4_z1_e2', 'z1_e2', 'PIT-4', 0, 3, 'AVAILABLE', NULL, NULL),
('s5_z1_e2', 'z1_e2', 'PIT-5', 0, 4, 'AVAILABLE', NULL, NULL),
('s6_z1_e2', 'z1_e2', 'PIT-6', 1, 0, 'AVAILABLE', NULL, NULL),
('s7_z1_e2', 'z1_e2', 'PIT-7', 1, 1, 'AVAILABLE', NULL, NULL),
('s8_z1_e2', 'z1_e2', 'PIT-8', 1, 2, 'AVAILABLE', NULL, NULL),
('s9_z1_e2', 'z1_e2', 'PIT-9', 1, 3, 'AVAILABLE', NULL, NULL),
('s10_z1_e2', 'z1_e2', 'PIT-10', 1, 4, 'AVAILABLE', NULL, NULL);

-- ==============================================================================
-- 6. ORDERS & ORDER ITEMS (Lịch sử giao dịch)
-- ==============================================================================
-- Minh (u2) mua 1 vé VIP Event 1
INSERT INTO public.orders (id, user_id, status, total_amount, created_at, paid_at) VALUES
('o1', 'u2', 'PAID', 1000000.00, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days');

INSERT INTO public.order_items (id, order_id, event_id, seat_id, zone_name, seat_label, unit_price) VALUES
('oi1', 'o1', 'e1', 's1_z1_e1', 'VIP Area', 'VIP-A1', 1000000.00);

-- Bob (u4) mua 2 vé Standard Event 1 (1 đơn hàng, 2 order items)
INSERT INTO public.orders (id, user_id, status, total_amount, created_at, paid_at) VALUES
('o2', 'u4', 'PAID', 400000.00, NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours');

INSERT INTO public.order_items (id, order_id, event_id, seat_id, zone_name, seat_label, unit_price) VALUES
('oi2', 'o2', 'e1', 's1_z2_e1', 'Standard', 'STD-A1', 200000.00),
('oi3', 'o2', 'e1', 's2_z2_e1', 'Standard', 'STD-A2', 200000.00);


-- ==============================================================================
-- 7. TICKETS (Vé điện tử)
-- ==============================================================================
INSERT INTO public.tickets (id, order_id, event_id, seat_id, user_id, qr_code, status, purchased_at) VALUES
('tk1', 'o1', 'e1', 's1_z1_e1', 'u2', 'qr_u2_nexus_vip1_base64_str', 'VALID', NOW() - INTERVAL '2 days'),
('tk2', 'o2', 'e1', 's1_z2_e1', 'u4', 'qr_u4_nexus_std1_base64_str', 'VALID', NOW() - INTERVAL '12 hours'),
('tk3', 'o2', 'e1', 's2_z2_e1', 'u4', 'qr_u4_nexus_std2_base64_str', 'VALID', NOW() - INTERVAL '12 hours');


-- ==============================================================================
-- 8. BEHAVIOURAL SIGNALS (Tương tác User - Event dồi dào)
-- ==============================================================================
INSERT INTO public.user_event_interactions (id, user_id, event_id, interaction_type, occurred_at) VALUES
('int1', 'u2', 'e1', 'VIEW', NOW() - INTERVAL '3 days'),
('int2', 'u2', 'e1', 'HOLD', NOW() - INTERVAL '2 days'),
('int3', 'u2', 'e1', 'PURCHASE', NOW() - INTERVAL '2 days'),
('int4', 'u2', 'e3', 'VIEW', NOW() - INTERVAL '1 day');

-- Alice (u3) đang săn vé Event 1
INSERT INTO public.user_event_interactions (id, user_id, event_id, interaction_type, occurred_at) VALUES
('int5', 'u3', 'e1', 'VIEW', NOW() - INTERVAL '20 minutes'),
('int6', 'u3', 'e1', 'HOLD', NOW() - INTERVAL '10 minutes');

-- Bob (u4) luớt cả 3 sự kiện
INSERT INTO public.user_event_interactions (id, user_id, event_id, interaction_type, occurred_at) VALUES
('int7', 'u4', 'e2', 'VIEW', NOW() - INTERVAL '14 hours'),
('int8', 'u4', 'e1', 'VIEW', NOW() - INTERVAL '13 hours'),
('int9', 'u4', 'e1', 'HOLD', NOW() - INTERVAL '12 hours'),
('int10', 'u4', 'e1', 'PURCHASE', NOW() - INTERVAL '12 hours'),
('int11', 'u4', 'e3', 'VIEW', NOW() - INTERVAL '1 hour');

-- Charlie (u5) đang chầu chực ở K-Pop Fest
INSERT INTO public.user_event_interactions (id, user_id, event_id, interaction_type, occurred_at) VALUES
('int12', 'u5', 'e2', 'VIEW', NOW() - INTERVAL '10 minutes'),
('int13', 'u5', 'e2', 'HOLD', NOW() - INTERVAL '5 minutes');
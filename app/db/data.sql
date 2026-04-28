-- Seed data compatible with schema-v2.sql
-- Admin password for all seeded hosts: Admin@123456
-- Demo customer password: User@123456

-- ==============================================================================
-- 1. USERS
-- ==============================================================================
INSERT INTO public.users (
    email,
    password_hash,
    full_name,
    date_of_birth,
    gender,
    role
) VALUES
    (
        'admin@ticketrush.com',
        '$2b$12$nC96eLgf/J0EldH2QVdZwO08SS1J8hBih6YoOgiSFWU8sGZ/v4khO',
        'VNU Events Office',
        DATE '1995-03-15',
        'OTHER',
        'ADMIN'
    ),
    (
        'admin.vpop@ticketrush.com',
        '$2b$12$nC96eLgf/J0EldH2QVdZwO08SS1J8hBih6YoOgiSFWU8sGZ/v4khO',
        'VPOP Company',
        DATE '1994-07-22',
        'OTHER',
        'ADMIN'
    ),
    (
        'admin.expo@ticketrush.com',
        '$2b$12$nC96eLgf/J0EldH2QVdZwO08SS1J8hBih6YoOgiSFWU8sGZ/v4khO',
        'VNX Expo Collective',
        DATE '1993-11-03',
        'OTHER',
        'ADMIN'
    ),
    (
        'user@gmail.com',
        '$2b$12$.wST9Fg9dLDJ/xWNn3ooOu7Greps9CKODNrnLsVU2.ulJal8npekS',
        'Nguyen Van A',
        DATE '2005-01-01',
        'OTHER',
        'CUSTOMER'
    )
ON CONFLICT (email) DO NOTHING;

-- ==============================================================================
-- 2. CATEGORIES
-- ==============================================================================
INSERT INTO public.categories (name) VALUES
    ('technology'),
    ('education'),
    ('music'),
    ('entertainment'),
    ('business'),
    ('art'),
    ('lifestyle'),
    ('sports'),
    ('career')
ON CONFLICT (name) DO NOTHING;

-- ==============================================================================
-- 3. EVENTS
-- ==============================================================================
CREATE TEMP TABLE seed_events (
    slug VARCHAR(255) PRIMARY KEY,
    host_email VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    venue VARCHAR(255) NOT NULL,
    banner_url VARCHAR(500),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    theme VARCHAR(50) NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    ticket_type public.ticket_type_enum NOT NULL,
    seating_type public.seating_type_enum NOT NULL,
    max_capacity INTEGER
);

INSERT INTO seed_events (
    slug,
    host_email,
    title,
    description,
    short_description,
    venue,
    banner_url,
    start_time,
    end_time,
    theme,
    category_name,
    ticket_type,
    seating_type,
    max_capacity
) VALUES
    (
        'ai-unicorn-hackathon',
        'admin@ticketrush.com',
        'AI Unicorn Hackathon',
        'Hackathon 3 ngay ve GenAI, RAG va graph systems cho sinh vien va startup.',
        'Hackathon AI thuc chien',
        'UET Campus, VNU',
        'https://images.unsplash.com/photo-1516321318423-f06f85e504b3',
        '2026-08-10 08:00:00+07',
        '2026-08-12 17:00:00+07',
        'tech-dark',
        'technology',
        'FREE',
        'GENERAL_ADMISSION',
        500
    ),
    (
        'ai-mastery-hanoi-2026',
        'admin@ticketrush.com',
        'AI Mastery Workshop: RAG and Graph',
        'Workshop chuyen sau ve retrieval, graph-enhanced search va agent evaluation.',
        'Workshop RAG va graph',
        'Hanoi Innovation Hub',
        'https://images.unsplash.com/photo-1677442136019-21780ecad995',
        '2026-06-10 09:00:00+07',
        '2026-06-10 17:00:00+07',
        'tech-dark',
        'technology',
        'FREE',
        'GENERAL_ADMISSION',
        220
    ),
    (
        'python-con-vietnam',
        'admin@ticketrush.com',
        'PyCon Vietnam 2026',
        'Su kien cong dong Python lon, gom talks, sponsor booths va lightning sessions.',
        'Cong dong Python Vietnam',
        'UET Campus, VNU',
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5',
        '2026-10-12 08:00:00+07',
        '2026-10-13 17:00:00+07',
        'tech-dark',
        'technology',
        'PAID',
        'ASSIGNED',
        NULL
    ),
    (
        'data-eng-workshop',
        'admin@ticketrush.com',
        'Data Engineering 101',
        'Buoi workshop gioi thieu ETL, Airflow, dbt va data platform cho nguoi moi bat dau.',
        'Nhap mon Data Engineering',
        'Online via Zoom',
        'https://images.unsplash.com/photo-1551288049-bbdac8626ad1',
        '2026-06-15 19:30:00+07',
        '2026-06-15 22:00:00+07',
        'tech-light',
        'technology',
        'FREE',
        'GENERAL_ADMISSION',
        800
    ),
    (
        'rust-vn-gathering',
        'admin@ticketrush.com',
        'Rust Vietnam Gathering',
        'Gap go cong dong Rustaceans voi chu de performance, tooling va backend safety.',
        'Meetup cong dong Rust',
        'Bach Khoa Ha Noi',
        'https://images.unsplash.com/photo-1515879218367-8466d910aaa4',
        '2026-07-30 14:00:00+07',
        '2026-07-30 17:00:00+07',
        'tech-dark',
        'technology',
        'FREE',
        'GENERAL_ADMISSION',
        180
    ),
    (
        'career-fair-vnu',
        'admin@ticketrush.com',
        'VNU Career Fair 2026',
        'Ngay hoi viec lam ket noi sinh vien VNU voi doanh nghiep cong nghe va tai chinh.',
        'Career fair cho sinh vien',
        'VNU Campus, Xuan Thuy',
        'https://images.unsplash.com/photo-1521737711867-e3b97375f902',
        '2026-04-12 08:00:00+07',
        '2026-04-12 16:00:00+07',
        'edu-light',
        'career',
        'FREE',
        'GENERAL_ADMISSION',
        1200
    ),
    (
        'generative-ai-workshop',
        'admin@ticketrush.com',
        'Generative AI Workshop',
        'Hands-on session ve prompt engineering, tool calling va workflow automation.',
        'Workshop GenAI thuc hanh',
        'Tech Space Lab',
        'https://images.unsplash.com/photo-1485827404703-89b55fcc595e',
        '2026-05-22 13:30:00+07',
        '2026-05-22 17:30:00+07',
        'tech-light',
        'education',
        'FREE',
        'GENERAL_ADMISSION',
        160
    ),
    (
        'game-dev-con-vn',
        'admin@ticketrush.com',
        'GameDev Con Vietnam',
        'Hoi thao chia se quy trinh lam game, production art va Unreal Engine pipelines.',
        'Hoi thao phat trien game',
        'FPT Software Village',
        'https://images.unsplash.com/photo-1550745165-9bc0b252726f',
        '2026-05-30 09:00:00+07',
        '2026-05-31 17:00:00+07',
        'tech-dark',
        'technology',
        'FREE',
        'GENERAL_ADMISSION',
        350
    ),
    (
        'vpop-night-2026',
        'admin.vpop@ticketrush.com',
        'V-Pop Summer Night',
        'Dem nhac V-Pop quy mo lon voi nhieu headliner va san khau LED ngoai troi.',
        'Concert V-Pop mua he',
        'My Dinh National Stadium',
        'https://images.unsplash.com/photo-1470225620780-dba8ba36b745',
        '2026-06-20 19:00:00+07',
        '2026-06-20 23:00:00+07',
        'music-vibrant',
        'music',
        'PAID',
        'ASSIGNED',
        NULL
    ),
    (
        'indie-music-fest',
        'admin.vpop@ticketrush.com',
        'Hanoi Indie Music Fest',
        'Le hoi am nhac danh cho indie bands, singer-songwriters va khan gia tre.',
        'Le hoi am nhac indie',
        'Thong Nhat Park',
        'https://images.unsplash.com/photo-1501386761578-eac5c94b800a',
        '2026-05-18 16:00:00+07',
        '2026-05-18 22:00:00+07',
        'music-light',
        'music',
        'FREE',
        'GENERAL_ADMISSION',
        900
    ),
    (
        'jazz-under-stars',
        'admin.vpop@ticketrush.com',
        'Jazz Under The Stars',
        'Dem nhac jazz khong gian nho voi ban nhac song va cho ngoi co dinh.',
        'Dem nhac jazz than mat',
        'Ha Noi Opera House',
        'https://images.unsplash.com/photo-1511192336575-5a79af67a629',
        '2026-04-15 20:00:00+07',
        '2026-04-15 22:30:00+07',
        'music-vibrant',
        'music',
        'PAID',
        'ASSIGNED',
        NULL
    ),
    (
        'rock-fire-danang',
        'admin.vpop@ticketrush.com',
        'Rock Fire Da Nang',
        'Show rock Viet ngoai troi voi san khau trung tam va nhieu khu standing.',
        'Concert rock ngoai troi',
        'Dragon Bridge Riverside, Da Nang',
        'https://images.unsplash.com/photo-1493225255756-d9584f8606e9',
        '2026-08-08 19:00:00+07',
        '2026-08-08 23:00:00+07',
        'music-dark',
        'music',
        'PAID',
        'ASSIGNED',
        NULL
    ),
    (
        'acoustic-dalat',
        'admin.vpop@ticketrush.com',
        'Acoustic Sunset Da Lat',
        'Mini show acoustic giua doi, phu hop khan gia tre va khach du lich.',
        'Acoustic mini show',
        'May Lang Thang, Da Lat',
        'https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee',
        '2026-05-02 17:30:00+07',
        '2026-05-02 20:00:00+07',
        'music-light',
        'music',
        'FREE',
        'GENERAL_ADMISSION',
        240
    ),
    (
        'rap-viet-tour',
        'admin.vpop@ticketrush.com',
        'Rap Viet Concert Tour',
        'Concert arena quy tu nhieu nghe si rap, DJ set va hieu ung san khau quy mo lon.',
        'Concert Rap Viet',
        'Quan Khu 7 Stadium',
        'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad',
        '2026-09-15 19:00:00+07',
        '2026-09-15 23:00:00+07',
        'music-vibrant',
        'entertainment',
        'PAID',
        'ASSIGNED',
        NULL
    ),
    (
        'kpop-dance-battle',
        'admin.vpop@ticketrush.com',
        'K-Pop Dance Battle',
        'Cuoc thi dance cover theo nhom voi khu san khau mo va booth fandom.',
        'Dance battle K-Pop',
        'AEON Mall Long Bien',
        'https://images.unsplash.com/photo-1547153760-18fc86324498',
        '2026-05-10 14:00:00+07',
        '2026-05-10 18:00:00+07',
        'music-vibrant',
        'entertainment',
        'FREE',
        'GENERAL_ADMISSION',
        600
    ),
    (
        'startup-founders-2026',
        'admin.expo@ticketrush.com',
        'Startup Founders Mixer',
        'Networking session ket noi founders, angels va builder communities.',
        'Networking cho founders',
        'Dreamplex HCM',
        'https://images.unsplash.com/photo-1515187029135-18ee286d815b',
        '2026-06-05 18:00:00+07',
        '2026-06-05 21:00:00+07',
        'business-dark',
        'business',
        'FREE',
        'GENERAL_ADMISSION',
        180
    ),
    (
        'digital-art-expo',
        'admin.expo@ticketrush.com',
        'Digital Art Expo',
        'Trien lam digital art, installation va artwork tao bang AI generative tools.',
        'Trien lam digital art',
        'VCCA Ha Noi',
        'https://images.unsplash.com/photo-1547891319-184a7553c185',
        '2026-07-01 09:00:00+07',
        '2026-07-10 21:00:00+07',
        'art-colorful',
        'art',
        'FREE',
        'GENERAL_ADMISSION',
        700
    ),
    (
        'marketing-trends-vn',
        'admin.expo@ticketrush.com',
        'Vietnam Marketing Trends',
        'Hoi nghi marketing cap nhat retail media, creator economy va AI campaign ops.',
        'Hoi nghi marketing 2026',
        'Lotte Hotel Saigon',
        'https://images.unsplash.com/photo-1460925895917-afdab827c52f',
        '2026-08-15 08:30:00+07',
        '2026-08-15 17:00:00+07',
        'business-light',
        'business',
        'FREE',
        'GENERAL_ADMISSION',
        320
    ),
    (
        'hanoi-coffee-festival',
        'admin.expo@ticketrush.com',
        'Hanoi Coffee Festival',
        'Le hoi trai nghiem van hoa ca phe, tasting sessions va cupping workshops.',
        'Le hoi ca phe Ha Noi',
        'Hoang Thanh Thang Long',
        'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085',
        '2026-11-20 08:00:00+07',
        '2026-11-22 20:00:00+07',
        'lifestyle-light',
        'lifestyle',
        'FREE',
        'GENERAL_ADMISSION',
        1500
    ),
    (
        'fintech-summit-vn',
        'admin.expo@ticketrush.com',
        'Vietnam Fintech Summit',
        'Su kien cho fintech operators, banks, payment rails va policy teams.',
        'Summit cong nghe tai chinh',
        'Pullman Danang',
        'https://images.unsplash.com/photo-1551288049-bbdac8626ad1',
        '2026-12-10 09:00:00+07',
        '2026-12-10 17:00:00+07',
        'business-dark',
        'business',
        'PAID',
        'ASSIGNED',
        NULL
    ),
    (
        'photography-workshop',
        'admin.expo@ticketrush.com',
        'Street Photography Workshop',
        'Workshop chup anh duong pho voi city walk, practical critiques va live demos.',
        'Workshop street photography',
        'Ha Noi Old Quarter',
        'https://images.unsplash.com/photo-1452784444945-3f422708fe5e',
        '2026-05-15 07:00:00+07',
        '2026-05-15 11:00:00+07',
        'art-colorful',
        'art',
        'FREE',
        'GENERAL_ADMISSION',
        120
    ),
    (
        'film-festival-hanoi',
        'admin.expo@ticketrush.com',
        'Hanoi International Film Fest',
        'Le hoi dien anh voi premiere screenings, Q&A va gala closing night.',
        'Le hoi dien anh quoc te',
        'CGV Vincom Center',
        'https://images.unsplash.com/photo-1485846234645-a62644f84728',
        '2026-11-01 18:00:00+07',
        '2026-11-07 23:00:00+07',
        'art-colorful',
        'entertainment',
        'PAID',
        'ASSIGNED',
        NULL
    );

INSERT INTO public.events (
    host_id,
    title,
    slug,
    description,
    short_description,
    venue,
    banner_url,
    start_time,
    end_time,
    is_private,
    theme,
    status,
    ticket_type,
    seating_type,
    max_capacity
)
SELECT
    users.id,
    seed_events.title,
    seed_events.slug,
    seed_events.description,
    seed_events.short_description,
    seed_events.venue,
    seed_events.banner_url,
    seed_events.start_time,
    seed_events.end_time,
    false,
    seed_events.theme,
    'PUBLISHED',
    seed_events.ticket_type,
    seed_events.seating_type,
    seed_events.max_capacity
FROM seed_events
JOIN public.users ON users.email = seed_events.host_email
ON CONFLICT (slug) DO NOTHING;

-- ==============================================================================
-- 4. EVENT CATEGORIES
-- ==============================================================================
INSERT INTO public.event_categories (event_id, category_id)
SELECT events.id, categories.id
FROM seed_events
JOIN public.events ON events.slug = seed_events.slug
JOIN public.categories ON categories.name = seed_events.category_name
ON CONFLICT (event_id, category_id) DO NOTHING;

-- ==============================================================================
-- 5. FREE EVENT ZONES (GENERAL ADMISSION)
-- ==============================================================================
INSERT INTO public.seat_zones (
    event_id,
    name,
    zone_type,
    rows,
    cols,
    capacity,
    price,
    color
)
SELECT
    events.id,
    'Free Pass',
    'GENERAL_ADMISSION',
    NULL,
    NULL,
    seed_events.max_capacity,
    0,
    '#4CAF50'
FROM seed_events
JOIN public.events ON events.slug = seed_events.slug
WHERE seed_events.ticket_type = 'FREE'
ON CONFLICT (event_id, name) DO NOTHING;

-- ==============================================================================
-- 6. PAID EVENT ZONES (ASSIGNED SEATING)
-- ==============================================================================
CREATE TEMP TABLE paid_zone_specs (
    event_slug VARCHAR(255) NOT NULL,
    zone_name VARCHAR(100) NOT NULL,
    rows SMALLINT NOT NULL,
    cols SMALLINT NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    color VARCHAR(20) NOT NULL
);

INSERT INTO paid_zone_specs (event_slug, zone_name, rows, cols, price, color) VALUES
    ('python-con-vietnam', 'VIP', 4, 6, 1200000.00, '#D4AF37'),
    ('python-con-vietnam', 'Standard', 8, 10, 450000.00, '#5C6BC0'),
    ('vpop-night-2026', 'VIP', 6, 8, 1800000.00, '#F06292'),
    ('vpop-night-2026', 'Fan Zone', 10, 12, 650000.00, '#BA68C8'),
    ('jazz-under-stars', 'Front Row', 4, 5, 900000.00, '#8D6E63'),
    ('jazz-under-stars', 'Balcony', 5, 8, 450000.00, '#90A4AE'),
    ('rock-fire-danang', 'Pit A', 6, 10, 1100000.00, '#EF5350'),
    ('rock-fire-danang', 'Pit B', 8, 12, 550000.00, '#FF7043'),
    ('rap-viet-tour', 'Gold', 6, 8, 1500000.00, '#FFB300'),
    ('rap-viet-tour', 'Silver', 10, 10, 700000.00, '#78909C'),
    ('fintech-summit-vn', 'Executive', 4, 6, 1000000.00, '#26A69A'),
    ('fintech-summit-vn', 'Standard', 8, 8, 380000.00, '#42A5F5'),
    ('film-festival-hanoi', 'Premiere', 5, 6, 750000.00, '#7E57C2'),
    ('film-festival-hanoi', 'Standard', 8, 10, 280000.00, '#78909C');

INSERT INTO public.seat_zones (
    event_id,
    name,
    zone_type,
    rows,
    cols,
    capacity,
    price,
    color
)
SELECT
    events.id,
    paid_zone_specs.zone_name,
    'ASSIGNED',
    paid_zone_specs.rows,
    paid_zone_specs.cols,
    paid_zone_specs.rows * paid_zone_specs.cols,
    paid_zone_specs.price,
    paid_zone_specs.color
FROM paid_zone_specs
JOIN public.events ON events.slug = paid_zone_specs.event_slug
ON CONFLICT (event_id, name) DO NOTHING;

-- ==============================================================================
-- 7. GENERATED SEATS FOR PAID EVENTS
-- ==============================================================================
INSERT INTO public.seats (
    zone_id,
    label,
    row_index,
    col_index,
    status
)
SELECT
    seat_zones.id,
    LEFT(UPPER(REGEXP_REPLACE(seat_zones.name, '[^A-Za-z0-9]+', '', 'g')), 8)
        || '-' || CHR(64 + row_no) || LPAD(col_no::TEXT, 2, '0'),
    row_no - 1,
    col_no - 1,
    'AVAILABLE'
FROM public.seat_zones
JOIN public.events ON public.events.id = seat_zones.event_id
CROSS JOIN LATERAL GENERATE_SERIES(1, seat_zones.rows) AS row_no
CROSS JOIN LATERAL GENERATE_SERIES(1, seat_zones.cols) AS col_no
WHERE public.events.ticket_type = 'PAID'
  AND seat_zones.zone_type = 'ASSIGNED'
ON CONFLICT (zone_id, row_index, col_index) DO NOTHING;

DROP TABLE seed_events;
DROP TABLE paid_zone_specs;

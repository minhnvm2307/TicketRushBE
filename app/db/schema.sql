--
-- PostgreSQL database dump
--

\restrict vidAWb85a6Tup7B9bVRKbwq4L0ZTMbpxyw1ffIjDL6fp2j2TFbusXOcGrvUYPgZ

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: event_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.event_status_enum AS ENUM (
    'DRAFT',
    'PUBLISHED',
    'CANCELLED'
);


ALTER TYPE public.event_status_enum OWNER TO postgres;

--
-- Name: gender_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.gender_enum AS ENUM (
    'MALE',
    'FEMALE',
    'OTHER'
);


ALTER TYPE public.gender_enum OWNER TO postgres;

--
-- Name: interaction_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.interaction_type_enum AS ENUM (
    'VIEW',
    'HOLD',
    'PURCHASE'
);


ALTER TYPE public.interaction_type_enum OWNER TO postgres;

--
-- Name: order_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.order_status_enum AS ENUM (
    'PENDING',
    'PAID',
    'CANCELLED'
);


ALTER TYPE public.order_status_enum OWNER TO postgres;

--
-- Name: seat_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.seat_status_enum AS ENUM (
    'AVAILABLE',
    'LOCKED',
    'SOLD'
);


ALTER TYPE public.seat_status_enum OWNER TO postgres;

--
-- Name: ticket_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.ticket_status_enum AS ENUM (
    'VALID',
    'USED',
    'REFUNDED'
);


ALTER TYPE public.ticket_status_enum OWNER TO postgres;

--
-- Name: user_role_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_role_enum AS ENUM (
    'CUSTOMER',
    'ADMIN'
);


ALTER TYPE public.user_role_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: event_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_categories (
    id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.event_categories OWNER TO postgres;

--
-- Name: event_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_tags (
    id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    name character varying(100) NOT NULL,
    weight numeric(5,2) NOT NULL
);


ALTER TABLE public.event_tags OWNER TO postgres;

--
-- Name: events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.events (
    id character varying(36) NOT NULL,
    title character varying(255) NOT NULL,
    slug character varying(255) NOT NULL,
    description text NOT NULL,
    short_description character varying(500) NOT NULL,
    is_private boolean NOT NULL,
    theme character varying(50) NOT NULL,
    venue character varying(255) NOT NULL,
    banner_url character varying(500),
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    status public.event_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.events OWNER TO postgres;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.order_items (
    id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    seat_id character varying(36) NOT NULL,
    zone_name character varying(100) NOT NULL,
    seat_label character varying(50) NOT NULL,
    unit_price numeric(10,2) NOT NULL
);


ALTER TABLE public.order_items OWNER TO postgres;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.orders (
    id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    status public.order_status_enum NOT NULL,
    total_amount numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    paid_at timestamp with time zone
);


ALTER TABLE public.orders OWNER TO postgres;

--
-- Name: queue_entries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.queue_entries (
    id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    access_token character varying(255),
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.queue_entries OWNER TO postgres;

--
-- Name: seat_zones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.seat_zones (
    id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    name character varying(100) NOT NULL,
    rows integer NOT NULL,
    cols integer NOT NULL,
    price numeric(10,2) NOT NULL,
    capacity integer NOT NULL,
    color character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.seat_zones OWNER TO postgres;

--
-- Name: seats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.seats (
    id character varying(36) NOT NULL,
    zone_id character varying(36) NOT NULL,
    label character varying(30) NOT NULL,
    row_index integer NOT NULL,
    col_index integer NOT NULL,
    status public.seat_status_enum NOT NULL,
    locked_by character varying(36),
    locked_until timestamp with time zone
);


ALTER TABLE public.seats OWNER TO postgres;

--
-- Name: tickets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tickets (
    id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    seat_id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    qr_code text NOT NULL,
    status public.ticket_status_enum NOT NULL,
    purchased_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tickets OWNER TO postgres;

--
-- Name: user_event_interactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_event_interactions (
    id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    interaction_type public.interaction_type_enum NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_event_interactions OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id character varying(36) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    date_of_birth date NOT NULL,
    gender public.gender_enum NOT NULL,
    role public.user_role_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: event_categories event_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT event_categories_pkey PRIMARY KEY (id);


--
-- Name: event_tags event_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_tags
    ADD CONSTRAINT event_tags_pkey PRIMARY KEY (id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_seat_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_seat_id_key UNIQUE (seat_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: queue_entries queue_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.queue_entries
    ADD CONSTRAINT queue_entries_pkey PRIMARY KEY (id);


--
-- Name: seat_zones seat_zones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seat_zones
    ADD CONSTRAINT seat_zones_pkey PRIMARY KEY (id);


--
-- Name: seats seats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seats
    ADD CONSTRAINT seats_pkey PRIMARY KEY (id);


--
-- Name: tickets tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_pkey PRIMARY KEY (id);


--
-- Name: event_categories uq_event_category; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT uq_event_category UNIQUE (event_id, name);


--
-- Name: event_tags uq_event_tag; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_tags
    ADD CONSTRAINT uq_event_tag UNIQUE (event_id, name);


--
-- Name: seat_zones uq_event_zone_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seat_zones
    ADD CONSTRAINT uq_event_zone_name UNIQUE (event_id, name);


--
-- Name: tickets uq_ticket_seat; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT uq_ticket_seat UNIQUE (seat_id);


--
-- Name: seats uq_zone_position; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seats
    ADD CONSTRAINT uq_zone_position UNIQUE (zone_id, row_index, col_index);


--
-- Name: user_event_interactions user_event_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_event_interactions
    ADD CONSTRAINT user_event_interactions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_event_categories_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_event_categories_event_id ON public.event_categories USING btree (event_id);


--
-- Name: ix_event_categories_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_event_categories_name ON public.event_categories USING btree (name);


--
-- Name: ix_event_tags_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_event_tags_event_id ON public.event_tags USING btree (event_id);


--
-- Name: ix_event_tags_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_event_tags_name ON public.event_tags USING btree (name);


--
-- Name: ix_events_end_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_events_end_time ON public.events USING btree (end_time);


--
-- Name: ix_events_slug; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_events_slug ON public.events USING btree (slug);


--
-- Name: ix_events_start_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_events_start_time ON public.events USING btree (start_time);


--
-- Name: ix_events_title; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_events_title ON public.events USING btree (title);


--
-- Name: ix_order_items_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_order_items_event_id ON public.order_items USING btree (event_id);


--
-- Name: ix_order_items_order_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_order_items_order_id ON public.order_items USING btree (order_id);


--
-- Name: ix_orders_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_orders_user_id ON public.orders USING btree (user_id);


--
-- Name: ix_queue_entries_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_queue_entries_event_id ON public.queue_entries USING btree (event_id);


--
-- Name: ix_queue_entries_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_queue_entries_user_id ON public.queue_entries USING btree (user_id);


--
-- Name: ix_seat_zones_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_seat_zones_event_id ON public.seat_zones USING btree (event_id);


--
-- Name: ix_seats_zone_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_seats_zone_id ON public.seats USING btree (zone_id);


--
-- Name: ix_tickets_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tickets_event_id ON public.tickets USING btree (event_id);


--
-- Name: ix_tickets_order_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tickets_order_id ON public.tickets USING btree (order_id);


--
-- Name: ix_tickets_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tickets_user_id ON public.tickets USING btree (user_id);


--
-- Name: ix_user_event_interactions_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_event_interactions_event_id ON public.user_event_interactions USING btree (event_id);


--
-- Name: ix_user_event_interactions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_event_interactions_user_id ON public.user_event_interactions USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: event_categories event_categories_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_categories
    ADD CONSTRAINT event_categories_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: event_tags event_tags_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_tags
    ADD CONSTRAINT event_tags_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: order_items order_items_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: order_items order_items_seat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_seat_id_fkey FOREIGN KEY (seat_id) REFERENCES public.seats(id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: queue_entries queue_entries_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.queue_entries
    ADD CONSTRAINT queue_entries_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);


--
-- Name: queue_entries queue_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.queue_entries
    ADD CONSTRAINT queue_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: seat_zones seat_zones_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seat_zones
    ADD CONSTRAINT seat_zones_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: seats seats_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seats
    ADD CONSTRAINT seats_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- Name: seats seats_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seats
    ADD CONSTRAINT seats_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.seat_zones(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);


--
-- Name: tickets tickets_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: tickets tickets_seat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_seat_id_fkey FOREIGN KEY (seat_id) REFERENCES public.seats(id);


--
-- Name: tickets tickets_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_event_interactions user_event_interactions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_event_interactions
    ADD CONSTRAINT user_event_interactions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);


--
-- Name: user_event_interactions user_event_interactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_event_interactions
    ADD CONSTRAINT user_event_interactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict vidAWb85a6Tup7B9bVRKbwq4L0ZTMbpxyw1ffIjDL6fp2j2TFbusXOcGrvUYPgZ


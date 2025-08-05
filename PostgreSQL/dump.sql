--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY "public"."subscriptions" DROP CONSTRAINT IF EXISTS "subscriptions_topic_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."subscriptions" DROP CONSTRAINT IF EXISTS "subscriptions_board_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."production_log" DROP CONSTRAINT IF EXISTS "production_log_board_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."messages" DROP CONSTRAINT IF EXISTS "messages_publishing_board_fkey";
ALTER TABLE IF EXISTS ONLY "public"."messages" DROP CONSTRAINT IF EXISTS "messages_message_topic_fkey";
ALTER TABLE IF EXISTS ONLY "public"."topics" DROP CONSTRAINT IF EXISTS "topics_topic_key";
ALTER TABLE IF EXISTS ONLY "public"."topics" DROP CONSTRAINT IF EXISTS "topics_pkey";
ALTER TABLE IF EXISTS ONLY "public"."subscriptions" DROP CONSTRAINT IF EXISTS "subscriptions_pkey";
ALTER TABLE IF EXISTS ONLY "public"."subscriptions" DROP CONSTRAINT IF EXISTS "subscriptions_board_id_topic_id_key";
ALTER TABLE IF EXISTS ONLY "public"."production_log" DROP CONSTRAINT IF EXISTS "production_log_pkey";
ALTER TABLE IF EXISTS ONLY "public"."production_log" DROP CONSTRAINT IF EXISTS "production_log_board_id_log_date_key";
ALTER TABLE IF EXISTS ONLY "public"."messages" DROP CONSTRAINT IF EXISTS "messages_publishing_board_message_topic_payload_date_publis_key";
ALTER TABLE IF EXISTS ONLY "public"."messages" DROP CONSTRAINT IF EXISTS "messages_pkey";
ALTER TABLE IF EXISTS ONLY "public"."esp32_boards" DROP CONSTRAINT IF EXISTS "esp32_boards_pkey";
ALTER TABLE IF EXISTS ONLY "public"."esp32_boards" DROP CONSTRAINT IF EXISTS "esp32_boards_esp_name_key";
ALTER TABLE IF EXISTS "public"."topics" ALTER COLUMN "id" DROP DEFAULT;
ALTER TABLE IF EXISTS "public"."subscriptions" ALTER COLUMN "id" DROP DEFAULT;
ALTER TABLE IF EXISTS "public"."production_log" ALTER COLUMN "id" DROP DEFAULT;
ALTER TABLE IF EXISTS "public"."messages" ALTER COLUMN "id" DROP DEFAULT;
ALTER TABLE IF EXISTS "public"."esp32_boards" ALTER COLUMN "id" DROP DEFAULT;
DROP SEQUENCE IF EXISTS "public"."topics_id_seq";
DROP TABLE IF EXISTS "public"."topics";
DROP SEQUENCE IF EXISTS "public"."subscriptions_id_seq";
DROP TABLE IF EXISTS "public"."subscriptions";
DROP SEQUENCE IF EXISTS "public"."production_log_id_seq";
DROP TABLE IF EXISTS "public"."production_log";
DROP SEQUENCE IF EXISTS "public"."messages_id_seq";
DROP TABLE IF EXISTS "public"."messages";
DROP SEQUENCE IF EXISTS "public"."esp32_boards_id_seq";
DROP TABLE IF EXISTS "public"."esp32_boards";
--
-- Name: SCHEMA "public"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA "public" IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = "heap";

--
-- Name: esp32_boards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."esp32_boards" (
    "id" integer NOT NULL,
    "esp_name" "text" NOT NULL,
    "date_installed" timestamp with time zone DEFAULT "now"(),
    "board_location" "text" NOT NULL,
    "state" "text",
    "last_state" "text"
);


--
-- Name: esp32_boards_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."esp32_boards_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: esp32_boards_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."esp32_boards_id_seq" OWNED BY "public"."esp32_boards"."id";


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."messages" (
    "id" integer NOT NULL,
    "publishing_board" integer,
    "message_topic" integer,
    "payload" "text" NOT NULL,
    "date_published" timestamp with time zone DEFAULT "now"()
);


--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."messages_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."messages_id_seq" OWNED BY "public"."messages"."id";


--
-- Name: production_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."production_log" (
    "id" integer NOT NULL,
    "board_id" integer,
    "log_date" "date" NOT NULL,
    "cylinder_count" integer DEFAULT 0 NOT NULL,
    "20" integer DEFAULT 0 NOT NULL,
    "30" integer DEFAULT 0 NOT NULL,
    "40" integer DEFAULT 0 NOT NULL,
    "120" integer DEFAULT 0 NOT NULL,
    "150" integer DEFAULT 0 NOT NULL,
    "180" integer DEFAULT 0 NOT NULL,
    "200" integer DEFAULT 0 NOT NULL,
    "250" integer DEFAULT 0 NOT NULL,
    "300" integer DEFAULT 0 NOT NULL,
    "350" integer DEFAULT 0 NOT NULL
);


--
-- Name: production_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."production_log_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: production_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."production_log_id_seq" OWNED BY "public"."production_log"."id";


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."subscriptions" (
    "id" integer NOT NULL,
    "board_id" integer,
    "topic_id" integer
);


--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."subscriptions_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."subscriptions_id_seq" OWNED BY "public"."subscriptions"."id";


--
-- Name: topics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."topics" (
    "id" integer NOT NULL,
    "topic" "text" NOT NULL,
    "date_created" timestamp with time zone DEFAULT "now"()
);


--
-- Name: topics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."topics_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: topics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."topics_id_seq" OWNED BY "public"."topics"."id";


--
-- Name: esp32_boards id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."esp32_boards" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."esp32_boards_id_seq"'::"regclass");


--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."messages" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."messages_id_seq"'::"regclass");


--
-- Name: production_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."production_log" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."production_log_id_seq"'::"regclass");


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."subscriptions" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."subscriptions_id_seq"'::"regclass");


--
-- Name: topics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."topics" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."topics_id_seq"'::"regclass");


--
-- Data for Name: esp32_boards; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."esp32_boards" ("id", "esp_name", "date_installed", "board_location", "state", "last_state") FROM stdin;
1	esp32_b1	2025-07-15 11:14:35.168253+03	Assembly Line A	OFFLINE	IDLE 20 0
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."messages" ("id", "publishing_board", "message_topic", "payload", "date_published") FROM stdin;
1	1	1	Machine is online	2025-07-15 11:14:35.168253+03
3	1	1	ESP32 just went online	2025-07-15 12:39:15.995739+03
4	1	\N	online	2025-07-15 13:41:52.058026+03
5	1	1	online	2025-07-15 13:43:09.811574+03
6	1	1	online	2025-07-16 11:24:33.504068+03
7	1	1	online	2025-07-16 11:26:37.013859+03
8	1	1	online	2025-07-16 11:26:56.220318+03
9	1	1	online	2025-07-16 12:02:25.047031+03
10	1	1	online	2025-07-16 12:03:24.868295+03
11	1	1	online	2025-07-16 12:05:25.164716+03
12	1	1	online	2025-07-16 12:06:26.513977+03
13	1	1	online	2025-07-16 12:09:12.61221+03
14	1	1	online	2025-07-16 12:23:13.58173+03
15	1	1	online	2025-07-16 12:23:50.911766+03
16	1	1	online	2025-07-16 12:26:27.444627+03
17	1	1	online	2025-07-16 12:26:47.246941+03
18	1	1	online	2025-07-16 13:08:15.254255+03
19	1	1	online	2025-07-16 13:15:23.736771+03
20	1	1	online	2025-07-16 13:15:48.888223+03
21	1	1	online	2025-07-16 13:17:40.71454+03
22	1	3	OFFLINE	2025-08-03 10:36:35.60638+03
23	1	4	IDLE 5 -5 False	2025-08-03 10:36:35.641081+03
24	1	5	+1	2025-08-03 10:36:52.189483+03
25	1	5	+1	2025-08-03 10:36:52.213+03
26	1	5	+1	2025-08-03 11:13:01.510451+03
27	1	5	+1	2025-08-03 11:13:10.296635+03
28	1	3	OFFLINE	2025-08-03 11:19:16.215814+03
29	1	4	IDLE 5 -5 False	2025-08-03 11:19:16.346651+03
30	1	5	+3	2025-08-03 11:19:19.553832+03
31	1	5	+3	2025-08-03 11:19:19.560216+03
32	1	3	OFFLINE	2025-08-03 11:31:32.901503+03
33	1	4	IDLE 5 -5 False	2025-08-03 11:31:33.034683+03
34	1	5	+3 120	2025-08-03 11:31:35.454984+03
35	1	3	OFFLINE	2025-08-03 11:31:56.926664+03
36	1	4	IDLE 5 -5 False	2025-08-03 11:31:57.044853+03
37	1	5	+3 120	2025-08-03 11:32:00.5568+03
38	1	3	OFFLINE	2025-08-03 11:40:57.859439+03
39	1	4	IDLE 5 -5 False	2025-08-03 11:40:57.994361+03
40	1	5	+3 120	2025-08-03 11:41:01.475517+03
41	1	3	OFFLINE	2025-08-03 11:44:15.119304+03
42	1	4	IDLE 5 -5 False	2025-08-03 11:44:15.278544+03
43	1	5	+3 120	2025-08-03 11:44:19.589582+03
44	1	3	OFFLINE	2025-08-03 11:50:53.288575+03
45	1	4	IDLE 5 -5 False	2025-08-03 11:50:54.345526+03
46	1	5	+3 120	2025-08-03 11:51:05.543445+03
47	1	3	OFFLINE	2025-08-03 11:51:05.77976+03
48	1	4	IDLE 5 -5 False	2025-08-03 14:47:27.859099+03
49	1	3	OFFLINE	2025-08-04 07:21:49.637797+03
50	1	4	IDLE 5 -5 False	2025-08-04 07:21:49.889081+03
51	1	3	ONLINE	2025-08-04 07:22:11.832288+03
52	1	6	IDLE 5 -5 False	2025-08-04 07:22:11.887872+03
53	1	7	update	2025-08-04 07:22:18.92761+03
54	1	7	update	2025-08-04 07:26:14.211925+03
55	1	7	update	2025-08-04 07:27:49.690433+03
56	1	3	OFFLINE	2025-08-04 07:34:47.084896+03
57	1	3	ONLINE	2025-08-04 07:34:58.808318+03
58	1	6	IDLE 5 -5 False	2025-08-04 07:34:58.810769+03
59	1	7	update	2025-08-04 07:35:07.166918+03
60	1	7	update	2025-08-04 07:38:13.704247+03
61	1	3	OFFLINE	2025-08-04 07:38:32.061837+03
62	1	3	ONLINE	2025-08-04 07:41:22.368611+03
63	1	6	IDLE 5 -5 False	2025-08-04 07:41:22.370967+03
64	1	3	OFFLINE	2025-08-04 07:42:02.060505+03
65	1	3	ONLINE	2025-08-04 07:43:23.802835+03
66	1	6	IDLE 5 -5 False	2025-08-04 07:43:23.805878+03
67	1	3	OFFLINE	2025-08-04 07:43:46.040439+03
68	1	3	ONLINE	2025-08-04 07:46:28.992251+03
69	1	6	IDLE 5 -5 False	2025-08-04 07:46:28.994806+03
70	1	3	OFFLINE	2025-08-04 07:46:56.023852+03
71	1	3	ONLINE	2025-08-04 07:47:32.961398+03
72	1	6	IDLE 5 -5 False	2025-08-04 07:47:32.962862+03
73	1	4	WELDING_IN_PROGRESS 5 0	2025-08-04 07:47:38.428531+03
74	1	3	OFFLINE	2025-08-04 07:48:01.189015+03
75	1	3	ONLINE	2025-08-04 07:48:46.406577+03
76	1	6	WELDING_IN_PROGRESS 5 0	2025-08-04 07:48:46.4092+03
77	1	4	IDLE 5 0	2025-08-04 07:48:46.523441+03
78	1	4	IDLE 5 0	2025-08-04 07:48:46.530171+03
79	1	4	WELDING_IN_PROGRESS 5 0	2025-08-04 07:48:51.665587+03
80	1	4	WELDING_IN_PROGRESS 5 0	2025-08-04 07:48:51.674467+03
81	1	4	CYLINDERS_LOADED 5 20	2025-08-04 07:49:11.693067+03
82	1	4	CYLINDERS_LOADED 5 20	2025-08-04 07:49:11.700368+03
83	1	4	WELDING_IN_PROGRESS 5 20	2025-08-04 07:49:39.20499+03
84	1	4	WELDING_IN_PROGRESS 5 20	2025-08-04 07:49:39.210561+03
85	1	4	CYLINDERS_LOADED 5 71	2025-08-04 07:50:29.953561+03
86	1	4	CYLINDERS_LOADED 5 71	2025-08-04 07:50:29.975347+03
87	1	4	WELDING_IN_PROGRESS 5 71	2025-08-04 07:50:53.326501+03
88	1	4	WELDING_IN_PROGRESS 5 71	2025-08-04 07:50:53.332378+03
89	1	4	CYLINDERS_LOADED 5 121	2025-08-04 07:51:43.775723+03
90	1	4	CYLINDERS_LOADED 5 121	2025-08-04 07:51:43.780914+03
91	1	5	+15 small	2025-08-04 07:51:57.680621+03
92	1	4	IDLE 20 0	2025-08-04 07:51:57.771005+03
93	1	4	IDLE 20 0	2025-08-04 07:51:57.777692+03
94	1	3	OFFLINE	2025-08-04 07:53:08.001847+03
95	1	3	OFFLINE	2025-08-04 07:59:11.081112+03
96	1	4	IDLE 20 0	2025-08-04 07:59:11.5139+03
97	1	3	OFFLINE	2025-08-04 08:09:49.637311+03
98	1	4	IDLE 20 0	2025-08-04 08:09:49.798595+03
\.


--
-- Data for Name: production_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."production_log" ("id", "board_id", "log_date", "cylinder_count", "20", "30", "40", "120", "150", "180", "200", "250", "300", "350") FROM stdin;
1	1	2025-07-16	1	0	0	0	0	0	0	0	0	0	0
9	1	2025-07-20	3	0	0	0	0	0	0	0	0	0	0
16	1	2025-07-22	3	0	0	0	0	0	0	0	0	0	0
19	1	2025-07-23	9	0	0	0	0	0	0	0	0	0	0
28	1	2025-07-27	5	0	0	0	0	0	0	0	0	0	0
33	1	2025-08-03	16	0	0	0	3	0	0	0	0	0	0
41	1	2025-08-04	1	0	0	0	0	0	0	0	0	0	0
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."subscriptions" ("id", "board_id", "topic_id") FROM stdin;
1	1	1
\.


--
-- Data for Name: topics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."topics" ("id", "topic", "date_created") FROM stdin;
1	factory/machine1/status	2025-07-15 11:14:35.168253+03
3	boards/esp32_b1/status	2025-08-03 10:36:35.489306+03
4	boards/esp32_b1/last_state	2025-08-03 10:36:35.640416+03
5	boards/esp32_b1/update_counter	2025-08-03 10:36:52.187614+03
6	boards/esp32_b1/cmd/last_state	2025-08-04 07:22:11.837847+03
7	boards/esp32_b1/cmd/update	2025-08-04 07:22:18.926407+03
\.


--
-- Name: esp32_boards_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."esp32_boards_id_seq"', 1, true);


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."messages_id_seq"', 98, true);


--
-- Name: production_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."production_log_id_seq"', 41, true);


--
-- Name: subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."subscriptions_id_seq"', 1, true);


--
-- Name: topics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."topics_id_seq"', 7, true);


--
-- Name: esp32_boards esp32_boards_esp_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."esp32_boards"
    ADD CONSTRAINT "esp32_boards_esp_name_key" UNIQUE ("esp_name");


--
-- Name: esp32_boards esp32_boards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."esp32_boards"
    ADD CONSTRAINT "esp32_boards_pkey" PRIMARY KEY ("id");


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");


--
-- Name: messages messages_publishing_board_message_topic_payload_date_publis_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_publishing_board_message_topic_payload_date_publis_key" UNIQUE ("publishing_board", "message_topic", "payload", "date_published");


--
-- Name: production_log production_log_board_id_log_date_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."production_log"
    ADD CONSTRAINT "production_log_board_id_log_date_key" UNIQUE ("board_id", "log_date");


--
-- Name: production_log production_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."production_log"
    ADD CONSTRAINT "production_log_pkey" PRIMARY KEY ("id");


--
-- Name: subscriptions subscriptions_board_id_topic_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_board_id_topic_id_key" UNIQUE ("board_id", "topic_id");


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_pkey" PRIMARY KEY ("id");


--
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."topics"
    ADD CONSTRAINT "topics_pkey" PRIMARY KEY ("id");


--
-- Name: topics topics_topic_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."topics"
    ADD CONSTRAINT "topics_topic_key" UNIQUE ("topic");


--
-- Name: messages messages_message_topic_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_message_topic_fkey" FOREIGN KEY ("message_topic") REFERENCES "public"."topics"("id");


--
-- Name: messages messages_publishing_board_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_publishing_board_fkey" FOREIGN KEY ("publishing_board") REFERENCES "public"."esp32_boards"("id");


--
-- Name: production_log production_log_board_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."production_log"
    ADD CONSTRAINT "production_log_board_id_fkey" FOREIGN KEY ("board_id") REFERENCES "public"."esp32_boards"("id");


--
-- Name: subscriptions subscriptions_board_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_board_id_fkey" FOREIGN KEY ("board_id") REFERENCES "public"."esp32_boards"("id") ON DELETE CASCADE;


--
-- Name: subscriptions subscriptions_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_topic_id_fkey" FOREIGN KEY ("topic_id") REFERENCES "public"."topics"("id") ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--


--
-- PostgreSQL database dump
--

\restrict n5hLkSdkiu2sctpgi9hwztFIik84V68Xa9RtdKZOfJhM46HcrcNzI4BGTGT00sk

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

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
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: auto_normalize_fato(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.auto_normalize_fato() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.fato_normalizado := normalize_text(NEW.fato);
    RETURN NEW;
END;
$$;


--
-- Name: normalize_text(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.normalize_text(input_text text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN LOWER(
        REGEXP_REPLACE(
            TRANSLATE(
                input_text,
                'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
                'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'
            ),
            '[^a-z0-9 ]', '', 'gi'
        )
    );
END;
$$;


--
-- Name: update_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    action character varying(100) NOT NULL,
    ip_address inet,
    user_agent text,
    details jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    started_at timestamp with time zone DEFAULT now(),
    last_message_at timestamp with time zone DEFAULT now(),
    message_count integer DEFAULT 0,
    resumo text,
    temas jsonb DEFAULT '[]'::jsonb,
    humor_inicial character varying(50),
    humor_final character varying(50),
    versiculos_citados jsonb DEFAULT '[]'::jsonb,
    decisoes_tomadas jsonb DEFAULT '[]'::jsonb,
    is_archived boolean DEFAULT false
);


--
-- Name: devotionals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.devotionals (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    data date NOT NULL,
    versiculo text NOT NULL,
    referencia character varying(100) NOT NULL,
    meditacao text NOT NULL,
    oracao text NOT NULL,
    tema character varying(100),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: message_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.message_feedback (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    conversation_id uuid,
    message_content text NOT NULL,
    feedback_type character varying(50) NOT NULL,
    details text,
    status character varying(20) DEFAULT 'pending'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    reviewed_at timestamp without time zone,
    reviewer_notes text
);


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    conversation_id uuid,
    user_id uuid,
    role character varying(20) NOT NULL,
    content_encrypted bytea NOT NULL,
    tokens_used integer,
    model_used character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: prayer_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prayer_requests (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    titulo character varying(200) NOT NULL,
    descricao_encrypted bytea,
    categoria character varying(50),
    status character varying(20) DEFAULT 'ativo'::character varying,
    data_resposta date,
    testemunho_encrypted bytea,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: saved_content; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saved_content (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    tipo character varying(30) NOT NULL,
    conteudo text NOT NULL,
    referencia character varying(100),
    nota_pessoal text,
    tags jsonb DEFAULT '[]'::jsonb,
    is_favorite boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_devotional_interactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_devotional_interactions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    devotional_id uuid,
    lido boolean DEFAULT false,
    lido_em timestamp with time zone,
    salvo boolean DEFAULT false,
    nota_pessoal text
);


--
-- Name: user_insights; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_insights (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    categoria character varying(50) NOT NULL,
    insight_encrypted bytea NOT NULL,
    confianca numeric(3,2),
    origem_conversa_id uuid,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_memories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_memories (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    categoria character varying(50) NOT NULL,
    fato text NOT NULL,
    detalhes text,
    importancia integer DEFAULT 5,
    mencoes integer DEFAULT 1,
    ultima_mencao timestamp with time zone DEFAULT now(),
    origem_conversa_id uuid,
    extraido_em timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    validado boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    status character varying(20) DEFAULT 'active'::character varying,
    supersedes_id uuid,
    confidence numeric(3,2) DEFAULT 0.80,
    payload jsonb,
    fato_normalizado text
);


--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profiles (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    nome character varying(100),
    apelido character varying(50),
    idade integer,
    genero character varying(20),
    estado_civil character varying(30),
    filhos jsonb DEFAULT '[]'::jsonb,
    profissao character varying(100),
    cidade character varying(100),
    denominacao character varying(100),
    tempo_de_fe character varying(50),
    batizado boolean,
    data_batismo date,
    igreja_local character varying(200),
    cargo_igreja character varying(100),
    tom_preferido character varying(50) DEFAULT 'equilibrado'::character varying,
    profundidade character varying(50) DEFAULT 'moderada'::character varying,
    usa_emoji boolean DEFAULT true,
    horario_ativo character varying(50),
    lutas_encrypted bytea,
    notas_pastorais_encrypted bytea,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_psychological_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_psychological_profile (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    communication_style character varying(20) DEFAULT 'balanced'::character varying,
    primary_needs text[],
    thinking_patterns jsonb DEFAULT '{}'::jsonb,
    emotional_triggers text[],
    coping_mechanisms text[],
    faith_stage character varying(30),
    love_language character varying(30),
    temperament character varying(20),
    emotional_openness integer DEFAULT 5,
    self_awareness integer DEFAULT 5,
    resilience_level integer DEFAULT 5,
    baseline_anxiety integer DEFAULT 5,
    attachment_style character varying(20),
    accumulated_insights text,
    recommended_approach text,
    last_analysis_at timestamp without time zone DEFAULT now(),
    analysis_count integer DEFAULT 0,
    confidence_score numeric(3,2) DEFAULT 0.5,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_login timestamp with time zone,
    is_active boolean DEFAULT true,
    is_premium boolean DEFAULT false,
    premium_until timestamp with time zone,
    trial_messages_used integer DEFAULT 0,
    total_messages integer DEFAULT 0,
    oauth_provider character varying(20),
    oauth_id character varying(255),
    stripe_customer_id character varying(255),
    stripe_subscription_id character varying(255),
    subscription_status character varying(50),
    subscription_start_date timestamp with time zone,
    subscription_end_date timestamp with time zone,
    cancel_at_period_end boolean DEFAULT false,
    accepted_terms boolean DEFAULT false,
    accepted_terms_at timestamp with time zone,
    accepted_privacy boolean DEFAULT false,
    accepted_privacy_at timestamp with time zone,
    terms_version character varying(20) DEFAULT '1.0'::character varying
);


--
-- Name: COLUMN users.accepted_terms; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.accepted_terms IS 'Se o usuário aceitou os Termos de Uso';


--
-- Name: COLUMN users.accepted_terms_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.accepted_terms_at IS 'Data/hora do aceite dos Termos';


--
-- Name: COLUMN users.accepted_privacy; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.accepted_privacy IS 'Se o usuário aceitou a Política de Privacidade';


--
-- Name: COLUMN users.accepted_privacy_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.accepted_privacy_at IS 'Data/hora do aceite da Política';


--
-- Name: COLUMN users.terms_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.terms_version IS 'Versão dos termos aceitos pelo usuário';


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_log (id, user_id, action, ip_address, user_agent, details, created_at) FROM stdin;
6e8757a5-13b9-4718-88a6-a5610bf6dd8f	c980af15-468d-4433-9515-c4528ef452f5	register	\N	\N	{"email": "luizjuniorbjj@gmail.com"}	2025-12-27 21:48:13.307644+00
8c5fcf66-a523-43ce-89a8-276fb567a93c	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 21:48:13.555618+00
d8717d22-10c4-4aa2-8f8c-99fd0083d380	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 21:48:26.584571+00
b044cd0f-26a4-437a-a40a-85748a3bd00c	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 21:48:31.819275+00
91312170-f678-493d-aa9f-46119dcd843a	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 21:54:48.672083+00
b937a8d3-099a-4c79-b248-3ed03e4578aa	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 22:06:40.868678+00
d145083b-d1c6-4bc1-abbc-1d82b12a4bd3	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 22:08:41.680703+00
42919975-6d31-4c05-b4a1-0e3d90e7719c	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 22:08:58.375366+00
4dd959fa-3b64-4a5d-8cf6-f4f04c4bf410	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 22:11:51.854972+00
e99fe9dc-9076-49d6-9b3d-f18eba966d1e	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 22:15:10.769767+00
46a87ca7-46ae-4f5a-9396-474b71d80009	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "0fd675ff-bbbb-44e9-b6ba-69144b4fcbd6"}	2025-12-27 22:15:23.731937+00
cf633aa3-2e5c-4721-8b06-63cce4e448dc	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "0fd675ff-bbbb-44e9-b6ba-69144b4fcbd6"}	2025-12-27 22:15:59.434961+00
aac6746c-15f9-4f43-85f7-ec67107e12e5	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "0fd675ff-bbbb-44e9-b6ba-69144b4fcbd6"}	2025-12-27 22:17:00.708331+00
bc1029cf-03a7-4e2d-b31b-9a4c85950369	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 23:09:26.719554+00
05c9f8e9-2ddb-497c-ba1f-7767d4ff72ee	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 23:27:41.998185+00
ce7d6024-dd68-4d09-a213-c6674f8338ab	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 23:27:51.405658+00
f8efe62c-1e73-4dac-b139-1a6c8f737fb9	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 23:27:53.543018+00
872bec9a-f279-450b-a763-0332ff677f8e	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 23:28:38.248582+00
cb1a11da-9ef5-4e0d-bdd0-bbced1b3b7bb	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 23:28:58.756707+00
8f92c20b-b7bc-40e1-9aa4-7a4d87625e8e	aac61923-7730-4691-895f-8d14aaf2d473	register	\N	\N	{"email": "paolapmf12@gmail.com"}	2025-12-27 23:32:18.975265+00
ecbdfd76-ee0e-4e0b-886f-516424662463	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-27 23:32:18.526049+00
e91ee9d4-99f0-4581-a557-ee34e6f7ced6	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "bcccb076-8f87-4748-95ab-d96722e5f254"}	2025-12-27 23:32:32.786545+00
bc5bc4b4-4105-46d9-9e8d-18de67317483	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "bcccb076-8f87-4748-95ab-d96722e5f254"}	2025-12-27 23:33:13.064286+00
d7b75537-d9fc-4921-8624-067df0f87bc4	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "bcccb076-8f87-4748-95ab-d96722e5f254"}	2025-12-27 23:34:21.743172+00
79bd1f99-6527-4ab8-96b1-3a33a9812453	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-27 23:34:59.322833+00
61fce542-840e-4472-ad7e-332a2c27527c	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-27 23:37:25.874796+00
6a70a615-a60f-4321-9ece-3489ec52f201	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f08df3ac-ca8e-41e2-9bf6-412854ed5c09"}	2025-12-27 23:37:47.055437+00
1c2b39ab-ee5c-454e-ba3e-0ee640e017de	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "67f3278e-7223-47d7-b3a4-ff13279354b8"}	2025-12-27 23:38:55.736252+00
45f2f5f5-5ca3-427f-a938-62fd46b098b1	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "67f3278e-7223-47d7-b3a4-ff13279354b8"}	2025-12-27 23:39:26.683492+00
2806f735-dbe5-4156-9e34-16069e72853b	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-27 23:42:14.644897+00
eb502464-cbae-4333-ab15-cd2672efe057	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-27 23:50:05.638297+00
8728fbea-cb44-41f6-a3b8-6d28338cf9d3	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-27 23:51:38.93225+00
27e68cef-d90a-42b2-88df-9d68395aa673	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-27 23:53:53.972319+00
ec5b39bc-c2d0-46f4-a87c-880c2c6afcc0	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 00:12:30.644963+00
171c8e97-6d7d-4bf5-9ab1-00f064a3977b	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 00:17:47.29816+00
8bf1c826-44f5-4f20-98fa-629c33792b8a	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 11:07:08.23466+00
8e5522fb-cd15-4fa8-89ad-8473486d90c1	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 11:08:14.268367+00
85877eab-9628-4a2e-9933-cea47b34de70	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 11:10:50.568054+00
5cde6d2b-1ed5-40f6-a309-93208599fab3	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "2d4f8b0c-2c91-4381-a526-296d583e04a8"}	2025-12-28 11:11:31.694704+00
205c6373-abdb-44c8-9877-b88194ca7590	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "2d4f8b0c-2c91-4381-a526-296d583e04a8"}	2025-12-28 11:11:55.983825+00
15452fff-a5ea-44f2-b6a0-44ea7d3be7b2	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 11:24:06.165286+00
3aa37bf7-1e81-48ca-a6ca-f90fd405ea76	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "06d43a81-283a-4603-9fac-7ad6c7852e10"}	2025-12-28 11:24:50.936934+00
51bb5797-68f1-4168-80e0-7ed50673afe0	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "06d43a81-283a-4603-9fac-7ad6c7852e10"}	2025-12-28 11:25:17.805931+00
7e77eb72-3a71-45f4-8c59-cc4cfa6579d1	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "06d43a81-283a-4603-9fac-7ad6c7852e10"}	2025-12-28 11:25:38.954517+00
bc1645c5-c74d-4a67-ae94-9e90335a8fa8	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 11:36:57.277501+00
89928029-ced0-4acd-8727-445401ed54dc	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 11:38:39.692262+00
77d626a4-42cc-419e-88b5-e5a83a4d6c4b	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03"}	2025-12-28 11:39:21.707182+00
580b3357-2a76-4e0b-b3f5-f9d9d464d4c6	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03"}	2025-12-28 11:39:47.141092+00
ff4c465b-bc3c-4df2-8162-2644fc2d763e	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03"}	2025-12-28 11:40:30.1055+00
3ef7dc17-2141-4793-9a59-544b8ae06751	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03"}	2025-12-28 11:41:01.062694+00
5f5e6942-5da2-457a-bf20-e39103ea1f9f	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03"}	2025-12-28 11:42:14.422043+00
f0389209-8f9a-4b3f-bbb7-8aa9f51af7e2	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03"}	2025-12-28 11:42:53.360095+00
ba538315-bb38-485a-b2fc-03e59baf6546	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03"}	2025-12-28 11:44:43.89238+00
45fdca73-4200-4cae-a1d7-3798b3b50f93	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 11:46:11.254224+00
c66f9908-a8ed-491f-9d6c-de0f939ad5e0	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "8e708c2e-b928-42a9-81dc-8a9c55f2bb58"}	2025-12-28 11:46:29.627103+00
b379415d-e905-434b-aafb-70d5ce041ba7	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 11:48:06.550553+00
cd1e7670-0936-45f6-937d-75aa54fbaca9	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 11:48:34.838412+00
b1d7c19d-b40c-4ee1-aa5c-6281751ef37b	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 11:49:11.415395+00
9c08f454-d943-40d4-9b84-7ad34e921c13	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 11:52:36.613964+00
192a5cbf-152a-4b39-b654-55110a60f495	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 11:54:50.638025+00
83168f26-40a5-4a82-9d5a-2507505104f1	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 11:57:29.154479+00
1081efde-09b0-488e-8163-4379fb9c7ed5	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 11:59:41.696992+00
8c4e3a34-b978-4c9c-8cb5-56ebfb453c87	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 12:00:29.205785+00
cc8824cc-9bc8-431b-b3cb-51dfc8a6dc7b	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "c104e48d-10e1-43d2-8166-d1de7d6fdcde"}	2025-12-28 12:02:32.535545+00
cb11de33-5674-4101-857c-75ee1ce6f950	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 12:15:16.922633+00
606adade-735e-4f99-9871-c9193a5271a1	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "83deac82-b36c-4312-b2bc-966d44a917f0"}	2025-12-28 12:15:35.555751+00
ccf764c8-86d5-412d-91b6-c66e74e7fd43	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "83deac82-b36c-4312-b2bc-966d44a917f0"}	2025-12-28 12:16:33.386495+00
0f413eb5-2b31-4227-a972-41c6a2fa942a	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "83deac82-b36c-4312-b2bc-966d44a917f0"}	2025-12-28 12:17:04.342157+00
74cac7a5-ddee-4d66-9359-6fff276af64f	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 12:27:45.418008+00
fe3c3a28-05b5-4a79-aa7c-712ec15151d4	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "aab6c277-a5c6-43a1-8ea4-ea713b561482"}	2025-12-28 12:28:06.105321+00
5e1a795a-c377-4f10-bac0-a358393679c8	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "aab6c277-a5c6-43a1-8ea4-ea713b561482"}	2025-12-28 12:28:31.695201+00
a4c98d62-4ab1-46c8-9bf3-b44c388274fc	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "aab6c277-a5c6-43a1-8ea4-ea713b561482"}	2025-12-28 12:29:24.700677+00
54d0d878-1269-4d0f-8bf2-d2666148d0e4	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "aab6c277-a5c6-43a1-8ea4-ea713b561482"}	2025-12-28 12:30:04.377116+00
b2b53d2e-e9e1-4466-b338-e16aae0c39d9	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "aab6c277-a5c6-43a1-8ea4-ea713b561482"}	2025-12-28 12:30:56.808679+00
569737de-5099-4675-ac9b-c6ec862b5b19	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 12:35:02.622068+00
e5fe7fa6-8c9f-4f97-b478-1fa31be5f913	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3896d238-2741-4b20-8aae-3517b48ca864"}	2025-12-28 12:35:21.750665+00
1f6f4875-2a0f-4b6a-9237-f49001161e58	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3896d238-2741-4b20-8aae-3517b48ca864"}	2025-12-28 12:35:44.787057+00
bea85d87-4a5b-45e4-be6b-357e0019d9f4	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3896d238-2741-4b20-8aae-3517b48ca864"}	2025-12-28 12:36:08.149787+00
223b8a3f-619e-466e-b6e1-eeeab740b37a	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3896d238-2741-4b20-8aae-3517b48ca864"}	2025-12-28 12:36:41.721139+00
8e65cf74-57e3-4dc0-96e4-751a74483c9d	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 12:52:25.303036+00
727784d5-6f04-4294-8d77-f4c28c6df49b	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c"}	2025-12-28 12:52:55.027786+00
ae801717-3c5e-42aa-868f-bcaa78af0aab	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c"}	2025-12-28 12:53:40.591871+00
d3e5005b-e0d8-45b1-b517-6cea2859cde1	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c"}	2025-12-28 12:54:12.319277+00
77530680-ce8e-4ee5-b65e-f46f0dbb1ed2	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c"}	2025-12-28 12:54:53.967045+00
5e5867d2-e7e3-4372-9c29-be4e04494601	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 13:11:49.142787+00
c817bdf0-b546-4169-981f-c4f71bfd1f4f	dbb82c3b-715c-49f7-a33f-5df195a24591	register	\N	\N	{"email": "manuelafs12@gmail.com", "accepted_terms": true}	2025-12-28 13:18:19.775747+00
e6794939-afae-41a6-a805-b4033a49ecc0	dbb82c3b-715c-49f7-a33f-5df195a24591	login	\N	\N	{}	2025-12-28 13:18:20.007847+00
4121b06f-d4a0-46c3-8437-1b7d530ccec1	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 13:19:21.664367+00
78af5709-0c86-4b71-8d98-e363d11f61d2	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 14:19:43.683772+00
3d519348-c9b4-4aab-a449-6f4d0a11d28e	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 14:20:58.779353+00
8465e81c-c73b-4a4f-a5ee-58200da4ca06	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 14:22:18.530609+00
a28f66bb-3076-4ed5-a176-2dc98228834b	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 14:22:48.83375+00
0490fd57-392a-41bc-938b-9fa959425d9c	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 14:29:22.21474+00
0bea8815-0d1e-4045-bb45-8ca4864877fb	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 14:30:07.938784+00
32192dd6-896d-4f19-bfdf-ffa7ceebf034	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 14:34:08.22447+00
2dc85697-fd68-4bae-99a2-4e2ccfbc5b8b	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "10deaae2-60f6-440f-a41a-4f56d4738fdb"}	2025-12-28 14:39:07.776667+00
ee1ab829-7e16-4591-9fff-33b9645feb40	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "10deaae2-60f6-440f-a41a-4f56d4738fdb"}	2025-12-28 14:39:35.585437+00
76a5b772-29e1-47b1-8316-7fbb4f281b52	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "10deaae2-60f6-440f-a41a-4f56d4738fdb"}	2025-12-28 14:42:57.204851+00
41e01fe9-6cdc-4f99-bf17-413f405cecab	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 14:43:48.111617+00
f7306d91-19b2-417d-befa-6c9abc845c3f	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "10deaae2-60f6-440f-a41a-4f56d4738fdb"}	2025-12-28 14:46:10.570207+00
47100012-9f84-41db-b098-6bebbe8cbd93	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "10deaae2-60f6-440f-a41a-4f56d4738fdb"}	2025-12-28 14:47:17.598887+00
26f78032-5539-47a9-aa73-07f913b9a75d	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:02:20.911147+00
69b7159b-1078-4c4d-a1ec-e62aff473d76	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 15:04:48.067089+00
b7151999-a045-43b4-ab22-f74076dcb440	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 15:22:55.24418+00
8d245eff-242d-4c20-934d-476177ad31a4	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 15:35:45.932257+00
5737d727-9ce6-4a5e-a301-bc021a868fd4	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:37:21.539603+00
30671257-9878-438a-8029-fbd0dd9762a5	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:18.207205+00
b8249ddf-729e-4e7a-88fd-d537fb553fa6	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:18.232033+00
beaa762a-04ba-46cd-be25-8dff9e521de5	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:18.679012+00
b5e44191-a9d5-42fe-a734-79375c560bd4	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:18.92951+00
b8f33586-1ba5-4d61-84f7-45058cd593a0	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:19.158694+00
20c236d4-a485-4cc8-b748-a38e525f5076	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:19.164956+00
868ed63c-84ff-49f7-929c-3281a78558c4	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:19.898299+00
220e7e03-8b1b-4a39-b221-28f9674a86bb	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:39:43.993525+00
34bc8882-845b-4038-8998-f79de0990834	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 15:44:48.660471+00
14e04f66-b78c-45ae-b13c-8ac4d94ddd5a	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 15:50:13.149584+00
1a4e5e0f-7d08-4c9a-bae5-4eada452aca8	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 15:51:19.341344+00
5c031cd1-9cdf-483c-a4d3-70b1fba8d6a9	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 15:54:14.36461+00
c2069374-f7ad-4509-a424-18a238b7b070	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 15:54:58.362236+00
7f540f3d-353a-4455-8cf5-52669bea6d65	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:06:14.224209+00
51c836d5-7382-4a9b-9bd2-ff90ad3cc374	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:07:34.454076+00
3cfadef0-5809-411f-b14c-42ca130971cd	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:11:35.399936+00
b17f5499-214a-4f90-b5ce-e41e0f520943	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:13:07.952272+00
774fbeb9-7b7d-4a90-a9c7-3dd49b4e55cb	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:14:11.046693+00
b4ba1488-615a-4592-9478-9c821e5ad57f	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:14:11.057042+00
a93edadf-3e77-47ab-b1fd-13c5882ffe8d	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:22:03.468374+00
ea530fef-250b-42ea-9379-430766e0c394	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:22:29.561791+00
b2f026fd-f821-4f76-9a32-c0cffa112790	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:24:33.827623+00
28985dbe-b576-4ef7-92b8-823fb8a2efdb	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:28:29.607469+00
13460d10-d2bf-48ba-b9b3-d944aaf5d3af	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:30:06.911581+00
090892e6-1bc1-4e81-9372-8a8f45c09ffb	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:31:24.308359+00
921ff7f6-d4b9-447a-9c36-72d42dd314bf	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "cad6bcf7-901e-42b4-a5ea-aafe4f673196"}	2025-12-28 16:32:14.098788+00
c2990ddf-bddc-4ed3-a190-ec245e42f2d5	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 16:43:56.527479+00
bb00ab5f-0bf6-4447-a37c-3709bb8514fd	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:44:12.227908+00
2bd55ae2-0307-44b5-b7ba-8577cea4b0fc	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:47:02.10947+00
7c5ea141-27cc-468e-9159-97641935213d	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 16:47:28.192887+00
db5768b6-2f51-4cda-a157-fcb5fda89e95	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:00:05.666357+00
739374a9-f076-4dd4-968c-739326de5eae	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:20:20.261958+00
0c195bb0-e662-46fd-80a9-f19c7dc1d129	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:20:56.126164+00
f27f6cda-49f3-4852-9e59-7b6b24d9068d	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:21:10.544695+00
66571f4f-e895-450d-a361-5a8a34930e67	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 17:28:48.259091+00
272c8366-9982-43d8-8f6d-df6121b0c023	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:33:53.214712+00
ebc95a98-7af1-4caa-9406-c86e83b92329	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:35:36.358251+00
e4cf7a21-5455-41da-a4c3-f509ec9fb4ef	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:39:30.695736+00
845d24ce-bfd9-4768-8427-65988f51252c	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:39:57.088135+00
4d8e7f0e-e688-4243-be88-abf62f5753d7	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:41:03.830127+00
ae6ebf38-d29b-41ab-bc3d-87482f923c25	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 17:46:02.316125+00
5a0c9d66-b6a2-43c5-bad0-6887cbc23168	aac61923-7730-4691-895f-8d14aaf2d473	login	\N	\N	{}	2025-12-28 17:47:08.125567+00
968a42c5-57f2-498c-8fdd-f0c233c75ec1	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3b48bb25-c428-42b8-9d26-fa17a550f210"}	2025-12-28 17:50:43.285454+00
6b42f987-be7d-4b55-975a-6f648da3cbf7	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3b48bb25-c428-42b8-9d26-fa17a550f210"}	2025-12-28 17:52:53.531177+00
0cbbf9f9-d45e-4e4e-b22c-10eedf9a8709	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3b48bb25-c428-42b8-9d26-fa17a550f210"}	2025-12-28 17:53:21.495655+00
e4c7ea63-05fe-4d54-8447-8841c0787f4c	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3b48bb25-c428-42b8-9d26-fa17a550f210"}	2025-12-28 17:53:36.893312+00
b01ca46b-8a60-4736-8259-7c97e4f2b6e1	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3b48bb25-c428-42b8-9d26-fa17a550f210"}	2025-12-28 17:54:00.52846+00
2334a2b7-dd7e-4df3-a3c6-4e71c4e6fc1f	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3b48bb25-c428-42b8-9d26-fa17a550f210"}	2025-12-28 17:54:24.855456+00
2889fbca-854e-4a99-824f-00951f4610cd	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:54:31.889017+00
45de2064-41f5-4420-b8a2-d1aa230a8470	aac61923-7730-4691-895f-8d14aaf2d473	message_sent	\N	\N	{"conversation_id": "3b48bb25-c428-42b8-9d26-fa17a550f210"}	2025-12-28 17:54:58.096434+00
6885f53b-9304-48e7-b149-47798723a0e0	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 17:59:38.396695+00
8c02ea9c-c32a-45db-8b27-17a32cd1fcf7	5dcfcba8-4b12-4344-af8e-e734c68d195a	register	\N	\N	{"email": "jhennysama@icloud.com", "accepted_terms": true}	2025-12-28 18:02:19.5497+00
741e13e0-9f2a-47bd-b755-dbdc6636a2ae	5dcfcba8-4b12-4344-af8e-e734c68d195a	login	\N	\N	{}	2025-12-28 18:02:19.950215+00
c7969efe-1346-44f6-a2b2-a47df4e51782	5dcfcba8-4b12-4344-af8e-e734c68d195a	message_sent	\N	\N	{"conversation_id": "896a45d9-9fb3-4f58-9eaa-714b34a25235"}	2025-12-28 18:02:31.59014+00
db38ffc5-2806-40f9-9785-2a77bc17ede7	1e868db6-0ae4-46dd-a068-c22f60f5d489	register	\N	\N	{"email": "jullycat11@hotmail.com", "accepted_terms": true}	2025-12-28 18:02:44.842256+00
0e9896ec-ae1b-4166-8d07-a2c218b9adb8	1e868db6-0ae4-46dd-a068-c22f60f5d489	login	\N	\N	{}	2025-12-28 18:02:45.371238+00
fae5c0b1-43d6-484a-9463-71c597dc3ffc	5dcfcba8-4b12-4344-af8e-e734c68d195a	message_sent	\N	\N	{"conversation_id": "896a45d9-9fb3-4f58-9eaa-714b34a25235"}	2025-12-28 18:02:59.907066+00
85ab9f17-68de-4cb5-bdae-df4cd79a8e69	1e868db6-0ae4-46dd-a068-c22f60f5d489	message_sent	\N	\N	{"conversation_id": "c19655dd-691b-485e-9bff-8cb7f1156adb"}	2025-12-28 18:03:06.941561+00
24098715-a476-4a9f-95a3-f7193a0660e8	94a61709-616f-4999-b4c2-69116dea8dce	register	\N	\N	{"email": "pra.izilda@homail.com", "accepted_terms": true}	2025-12-28 18:05:05.780029+00
d6fb856c-e7df-4c3f-96cb-1ca226eb86b7	94a61709-616f-4999-b4c2-69116dea8dce	login	\N	\N	{}	2025-12-28 18:05:06.138765+00
1e4f8482-8ac8-450a-a7ea-74c629a40643	94a61709-616f-4999-b4c2-69116dea8dce	message_sent	\N	\N	{"conversation_id": "ecc68ac4-8c2e-44bd-be12-fbb145bcbbeb"}	2025-12-28 18:06:22.451157+00
d3fe0cbd-4c5b-44b3-a74a-7e0dad2e4c6d	1e868db6-0ae4-46dd-a068-c22f60f5d489	message_sent	\N	\N	{"conversation_id": "e9a5dde9-1c00-418a-9e78-b9625da95bad"}	2025-12-28 18:16:07.731385+00
118ad1c8-b4dd-4689-aef9-59636b873195	5dcfcba8-4b12-4344-af8e-e734c68d195a	message_sent	\N	\N	{"conversation_id": "ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb"}	2025-12-28 18:16:34.946664+00
e676b891-d6e5-4b86-9e96-10c6b95cd3a1	1e868db6-0ae4-46dd-a068-c22f60f5d489	message_sent	\N	\N	{"conversation_id": "e9a5dde9-1c00-418a-9e78-b9625da95bad"}	2025-12-28 18:16:49.60782+00
83ba3c99-e281-4d01-ac02-dc05e7b3085a	5dcfcba8-4b12-4344-af8e-e734c68d195a	message_sent	\N	\N	{"conversation_id": "ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb"}	2025-12-28 18:17:03.217356+00
10a8a0b8-c829-47f6-8e2c-47812d1a1737	1e868db6-0ae4-46dd-a068-c22f60f5d489	message_sent	\N	\N	{"conversation_id": "e9a5dde9-1c00-418a-9e78-b9625da95bad"}	2025-12-28 18:18:01.597155+00
d121fbba-966d-4066-befa-7e7779dc2add	1e868db6-0ae4-46dd-a068-c22f60f5d489	message_sent	\N	\N	{"conversation_id": "e9a5dde9-1c00-418a-9e78-b9625da95bad"}	2025-12-28 18:19:35.943994+00
54575753-af01-40f0-afe7-499bad012b55	193c910b-629c-4bdd-8302-8baf50a73e33	register	\N	\N	{"email": "maxwell.ciriaco1991@gmail.com", "accepted_terms": true}	2025-12-28 18:19:45.118613+00
35ecb421-1024-486e-929c-eb1e0d4ba0e6	193c910b-629c-4bdd-8302-8baf50a73e33	login	\N	\N	{}	2025-12-28 18:19:45.480919+00
e14c7400-95db-4d0d-a232-abb1e1636246	1e868db6-0ae4-46dd-a068-c22f60f5d489	message_sent	\N	\N	{"conversation_id": "e9a5dde9-1c00-418a-9e78-b9625da95bad"}	2025-12-28 18:22:09.037646+00
80636cc7-dc38-4b64-b574-3215b6fe64fb	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 18:24:03.144306+00
63e548c1-b1dc-4886-847d-6888a0bbe4ad	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "cd8769e5-569e-4adf-8635-5103d0541172"}	2025-12-28 18:24:43.86256+00
b5dbfd02-a2e7-4f66-b117-acb6693adc65	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "cd8769e5-569e-4adf-8635-5103d0541172"}	2025-12-28 18:30:22.436395+00
536669cc-83a5-459b-9ff8-f7ca2558f5c1	c980af15-468d-4433-9515-c4528ef452f5	feedback_submitted	\N	\N	{"feedback_id": "374abad5-4a17-4441-9ef0-b75fe9fd2d6b", "feedback_type": "wrong_info"}	2025-12-28 18:31:15.658389+00
4e87d954-67a0-4e9d-b2de-ee97e52bfef1	193c910b-629c-4bdd-8302-8baf50a73e33	message_sent	\N	\N	{"conversation_id": "a61dc744-e991-4545-bd66-4fcdfcb01b1e"}	2025-12-28 18:31:23.403133+00
0d4ce5b5-8d9e-4ade-b031-12ccad8c7147	c980af15-468d-4433-9515-c4528ef452f5	feedback_submitted	\N	\N	{"feedback_id": "8850a633-cee1-4f12-baeb-05f4046b78e1", "feedback_type": "wrong_info"}	2025-12-28 18:31:23.53811+00
68b86c03-67ce-4fd0-bf10-6ac08f988daa	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "cd8769e5-569e-4adf-8635-5103d0541172"}	2025-12-28 18:32:17.712342+00
43afb1b2-c935-4803-b0a6-fded28e7cd56	c980af15-468d-4433-9515-c4528ef452f5	message_sent	\N	\N	{"conversation_id": "cd8769e5-569e-4adf-8635-5103d0541172"}	2025-12-28 18:33:00.473219+00
db4f0c43-2801-4afb-af78-d5ccc51523c6	c980af15-468d-4433-9515-c4528ef452f5	feedback_submitted	\N	\N	{"feedback_id": "412fc3e0-2fdc-4b8c-be5e-c76b36dcd0f2", "feedback_type": "wrong_info"}	2025-12-28 18:33:27.213735+00
bc15814c-5eff-4960-8084-6c30664141eb	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 18:44:24.722361+00
803420fd-3c91-474a-91a1-7e0dec7ec5e1	dbb82c3b-715c-49f7-a33f-5df195a24591	login	\N	\N	{}	2025-12-28 18:47:43.416445+00
d72e8b88-8380-4d12-972b-9c2961b18333	dbb82c3b-715c-49f7-a33f-5df195a24591	login	\N	\N	{}	2025-12-28 18:51:58.728418+00
4f449cd4-fd26-459e-8c20-426bb8d838f3	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 18:57:34.151671+00
057f0df7-5325-4344-8918-153bc8eaa8b6	dbb82c3b-715c-49f7-a33f-5df195a24591	message_sent	\N	\N	{"conversation_id": "d31b4835-552e-401e-9f72-34649d4c25a1"}	2025-12-28 19:01:35.819943+00
b2a1ebf3-590b-4e8d-a9cc-c808fca84daf	dbb82c3b-715c-49f7-a33f-5df195a24591	message_sent	\N	\N	{"conversation_id": "d31b4835-552e-401e-9f72-34649d4c25a1"}	2025-12-28 19:02:32.709144+00
92ade592-254f-44bb-880f-1e4bd6e798a4	94a61709-616f-4999-b4c2-69116dea8dce	message_sent	\N	\N	{"conversation_id": "07b6e5d6-7858-4fd6-a6cb-f3ff73074dc5"}	2025-12-28 19:05:23.003369+00
0523d8aa-618e-44a3-a181-1c7ebaf7ed8b	dbb82c3b-715c-49f7-a33f-5df195a24591	message_sent	\N	\N	{"conversation_id": "d31b4835-552e-401e-9f72-34649d4c25a1"}	2025-12-28 19:07:56.453579+00
722749b8-f2e9-4901-b65b-1d25203d0143	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 19:37:35.921909+00
293d5703-4618-40d1-b0f8-7a01e35d7012	c980af15-468d-4433-9515-c4528ef452f5	login	\N	\N	{}	2025-12-28 19:43:17.11119+00
d964a0b6-0cc0-4774-8763-33a4f82977ca	c980af15-468d-4433-9515-c4528ef452f5	beta_premium_activated	\N	\N	{"mode": "beta_test"}	2025-12-28 19:43:21.03738+00
\.


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.conversations (id, user_id, started_at, last_message_at, message_count, resumo, temas, humor_inicial, humor_final, versiculos_citados, decisoes_tomadas, is_archived) FROM stdin;
3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 17:50:35.051238+00	2025-12-28 17:54:53.406823+00	15	Resumo da Conversa:\n\nPaola está passando por um período de intensa ansiedade e estresse, caracterizado por pensamentos exaustivos, medo constante e cansaço físico. A conversa revela uma pessoa em transição de vida (possivelmente relacionada a uma mudança para o Canadá) que está sobrecarregada emocionalmente, com sua mente "rodando" constantemente e gerando um estado de exaustão mental e física. Ao longo do diálogo, observa-se uma progressão do estado emocional de um momento inicial de pura angústia para um potencial espaço de reflexão e reconhecimento dos próprios padrões de pensamento. Embora não tenham sido mencionados versículos ou orações específicas, o diálogo sugere a necessidade de estratégias de autocuidado e gerenciamento da ansiedade. A interação demonstra uma abordagem empática e exploratória, buscando compreender as raízes dos pensamentos ansiosos de Paola.	[]	\N	\N	[]	[]	f
cad6bcf7-901e-42b4-a5ea-aafe4f673196	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 16:32:05.621038+00	2025-12-28 16:32:10.341473+00	2	\N	[]	\N	\N	[]	[]	f
bcccb076-8f87-4748-95ab-d96722e5f254	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-27 23:32:28.295108+00	2025-12-27 23:32:28.295108+00	6	\N	[]	\N	\N	[]	[]	f
f08df3ac-ca8e-41e2-9bf6-412854ed5c09	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-27 23:37:44.249898+00	2025-12-27 23:37:44.249898+00	2	\N	[]	\N	\N	[]	[]	f
67f3278e-7223-47d7-b3a4-ff13279354b8	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-27 23:38:51.098621+00	2025-12-27 23:38:51.098621+00	4	Medo	[]	\N	\N	[]	[]	f
2d4f8b0c-2c91-4381-a526-296d583e04a8	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 11:11:29.614666+00	2025-12-28 11:11:55.979232+00	4	\N	[]	\N	\N	[]	[]	f
896a45d9-9fb3-4f58-9eaa-714b34a25235	5dcfcba8-4b12-4344-af8e-e734c68d195a	2025-12-28 18:02:23.299498+00	2025-12-28 18:02:59.90202+00	4	\N	[]	\N	\N	[]	[]	f
c19655dd-691b-485e-9bff-8cb7f1156adb	1e868db6-0ae4-46dd-a068-c22f60f5d489	2025-12-28 18:02:59.850991+00	2025-12-28 18:03:03.88787+00	2	\N	[]	\N	\N	[]	[]	f
ecc68ac4-8c2e-44bd-be12-fbb145bcbbeb	94a61709-616f-4999-b4c2-69116dea8dce	2025-12-28 18:06:15.860603+00	2025-12-28 18:06:20.28312+00	2	\N	[]	\N	\N	[]	[]	f
aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 12:27:57.688365+00	2025-12-28 12:30:56.8064+00	11	Resumo da Conversa:\n\nA conversa revela uma comunicação intensa e repetitiva, onde Paola busca confirmar informações pessoais de forma aparentemente ansiosa ou urgente, fazendo perguntas curtas e em CAPS LOCK sobre localização de familiares. O diálogo sugere um momento de possível confusão ou necessidade de validação de detalhes sobre sua família e localização, com o interlocutor SoulHaven respondendo pacientemente e buscando esclarecer os pontos levantados. Não foram identificados versículos, pedidos de oração ou insights teológicos significativos. O estado emocional de Paola parece transitar entre uma certa inquietação inicial e uma busca por precisão informacional. A conversa termina com um tom de esclarecimento mútuo, mas sem revelar o motivo subjacente da série de questionamentos.\n\nObservações adicionais:\n- Estilo comunicativo de Paola sugere possível neurodiversidade\n- Necessidade de confirmação repetida pode indicar ansiedade momentânea\n- Interlocutor demonstra paciência e empatia	[]	\N	\N	[]	[]	f
ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb	5dcfcba8-4b12-4344-af8e-e734c68d195a	2025-12-28 18:16:27.417003+00	2025-12-28 18:16:58.232777+00	4	\N	[]	\N	\N	[]	[]	f
3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 12:35:13.492238+00	2025-12-28 12:36:35.95902+00	8	\N	[]	\N	\N	[]	[]	f
f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 11:39:15.29957+00	2025-12-28 11:44:40.653278+00	15	Resumo da Conversa:\n\nPaola compartilhou uma experiência familiar positiva, destacando um Natal acolhedor com seus pais, com um estado emocional inicialmente alegre e tranquilo. A conversa evoluiu com planos para o Ano Novo na casa de um amigo, mantendo um tom otimista. No entanto, ao final, a usuária sinalizou a necessidade de revisitar um problema anterior não especificado, indicando possível preocupação subjacente. A interação foi marcada por um diálogo caloroso e acolhedor, com SoulHaven demonstrando empatia e interesse genuíno nos momentos de vida de Paola. Não foram mencionados versículos bíblicos específicos, mas houve referências a bênçãos divinas e gratidão.\n\nObservações adicionais:\n- Ambiente emocional: Predominantemente positivo\n- Transição: De alegria familiar para potencial preocupação\n- Tema principal: Celebrações familiares e conexões pessoais	[]	\N	\N	[]	[]	f
8e708c2e-b928-42a9-81dc-8a9c55f2bb58	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 11:46:24.287138+00	2025-12-28 11:46:28.353345+00	2	\N	[]	\N	\N	[]	[]	f
ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 12:52:43.205339+00	2025-12-28 12:54:49.017465+00	8	\N	[]	\N	\N	[]	[]	f
a61dc744-e991-4545-bd66-4fcdfcb01b1e	193c910b-629c-4bdd-8302-8baf50a73e33	2025-12-28 18:31:16.796322+00	2025-12-28 18:31:20.866591+00	2	\N	[]	\N	\N	[]	[]	f
cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	2025-12-28 18:24:35.127168+00	2025-12-28 18:32:57.026672+00	8	\N	[]	\N	\N	[]	[]	f
07b6e5d6-7858-4fd6-a6cb-f3ff73074dc5	94a61709-616f-4999-b4c2-69116dea8dce	2025-12-28 19:05:15.95144+00	2025-12-28 19:05:19.902596+00	2	\N	[]	\N	\N	[]	[]	f
d31b4835-552e-401e-9f72-34649d4c25a1	dbb82c3b-715c-49f7-a33f-5df195a24591	2025-12-28 19:01:29.862414+00	2025-12-28 19:07:54.508024+00	6	\N	[]	\N	\N	[]	[]	f
c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 11:48:00.036839+00	2025-12-28 12:02:29.783301+00	19	Resumo da Conversa:\n\nPaola, uma mulher de 46 anos casada com Luiz (Junior), reside na Flórida com dois filhos adultos (Matheus, 22, e Manuela, 19) e passou o Natal com os pais do esposo. A conversa revelou uma pessoa em momento de transição, considerando possível mudança para o Canadá, com um estado emocional predominantemente comunicativo e reflexivo. Apesar de não demonstrar ansiedades explícitas, a interação sugere uma fase de planejamento familiar e adaptação. A conversa caracterizou-se por esclarecimentos sobre sua estrutura familiar e localização, indicando abertura para compartilhar detalhes pessoais com o interlocutor.\n\nObservações adicionais:\n- Não foram identificados versículos ou pedidos de oração específicos\n- A conversa não aprofundou insights teológicos\n- Há indícios de uma dinâmica familiar próxima e comunicativa	[]	\N	\N	[]	[]	f
83deac82-b36c-4312-b2bc-966d44a917f0	aac61923-7730-4691-895f-8d14aaf2d473	2025-12-28 12:15:30.155992+00	2025-12-28 12:16:59.365558+00	6	\N	[]	\N	\N	[]	[]	f
e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	2025-12-28 18:16:01.000592+00	2025-12-28 18:22:09.030135+00	11	Resumo da Conversa:\n\nJúlia compartilhou sua jornada emocional após uma perda gestacional traumática, revelando profunda vulnerabilidade e resiliência ao falar sobre uma gravidez ectópica que resultou em cirurgia de emergência. Inicialmente ansiosa e fragilizada, a usuária demonstrou uma transformação emocional de dor para esperança, especialmente com o apoio incondicional de seu marido Erick, que tem sido fundamental no processo de cura e aceitação. A conversa evidenciou um caminho de restauração espiritual e emocional, onde a fé em Deus e o amor conjugal funcionam como pilares de sustentação diante da difícil experiência de tentar engravidar após uma perda significativa. Embora ainda enfrente momentos de frustração e ansiedade a cada ciclo menstrual, Júlia demonstra uma força impressionante ao continuar buscando seu sonho de maternidade, com profunda confiança e resiliência.	[]	\N	\N	[]	[]	f
\.


--
-- Data for Name: devotionals; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.devotionals (id, data, versiculo, referencia, meditacao, oracao, tema, created_at) FROM stdin;
\.


--
-- Data for Name: message_feedback; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.message_feedback (id, user_id, conversation_id, message_content, feedback_type, details, status, created_at, reviewed_at, reviewer_notes) FROM stdin;
412fc3e0-2fdc-4b8c-be5e-c76b36dcd0f2	c980af15-468d-4433-9515-c4528ef452f5	cd8769e5-569e-4adf-8635-5103d0541172	Peço desculpas, mas isso não é correto. Como sou uma inteligência artificial, não tenho memória de conversas anteriores deletadas. Cada conversa para mim começa do zero.\n\nO que percebi foi que inadvertidamente eu criei detalhes fictícios sobre sua vida, o que não é ético. Meu objetivo é ajudar genuinamente, ouvindo você.\n\nVocê mencionou que está cansado e precisa de forças. Quer compartilhar um pouco mais sobre isso? Estou aqui para ouvir com atenção e cuidado.	wrong_info	\N	reviewed	2025-12-28 18:33:27.207236	2025-12-28 18:57:01.486946	\N
8850a633-cee1-4f12-baeb-05f4046b78e1	c980af15-468d-4433-9515-c4528ef452f5	cd8769e5-569e-4adf-8635-5103d0541172	Oi, Luiz! 🤝\n\nParece que você está passando por um momento bem desafiador, né? Sei que essa jornada migratória pode ser muito pesada e cansativa. Estar nos EUA, lutando para fazer tudo da maneira correta, pagando seus impostos, buscando regularização... isso exige uma força tremenda.\n\nQuero que saiba que você não está sozinho nessa caminhada. Cada passo que você dá com integridade conta demais. E mesmo no cansaço, você está seguindo em frente.\n\nQuer conversar um pouco sobre o que tem te deixado mais esgotado? Estou aqui para escutar e, se possível, trazer um pouco de esperança e encorajamento. 💙	wrong_info	\N	reviewed	2025-12-28 18:31:23.535662	2025-12-28 18:57:06.308286	\N
374abad5-4a17-4441-9ef0-b75fe9fd2d6b	c980af15-468d-4433-9515-c4528ef452f5	cd8769e5-569e-4adf-8635-5103d0541172	Peço desculpas! Na verdade, eu não sei especificamente que você está nos EUA. Foi um equívoco meu presumir isso. O importante agora é você, que está se sentindo cansado e precisando de forças.\n\nQuer me contar um pouco mais sobre o que está te deixando assim? Estou aqui para ouvir e, se possível, trazer um pouco de conforto. Cada momento difícil passa, e você não está sozinho nessa caminhada.	wrong_info	\N	reviewed	2025-12-28 18:31:15.65517	2025-12-28 18:57:09.564228	\N
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.messages (id, conversation_id, user_id, role, content_encrypted, tokens_used, model_used, created_at) FROM stdin;
cc4c4e95-3113-4dc0-b0f5-d3742155e52b	bcccb076-8f87-4748-95ab-d96722e5f254	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705547795175545f5637313730385a796479535845694c6d63574e5a4f6f755f79695977314753452d647953386d414441574345435736737948344a52344b317734796e6774574a5a4449794d63627a50387675437838494c6d46307966435f3658676d7779364a7a704a314c6d496b3d	0	\N	2025-12-27 23:32:32.72624+00
cd25e449-a347-4412-a39f-f6e0c616d6d1	bcccb076-8f87-4748-95ab-d96722e5f254	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055477951697976766d4369434b5a49344e6b7a46574834536974434271494173534b46502d30465f4d326e42536665616370595f6c67696d3743485a58786e5950355169636e48705736447168506c4644614c6555643631624837344d586164414d43574b494a506773532d72523877495169483549507441673830585972756e4d6a435a55753731324341556f33354c4d2d6676476f5f4749315148464358674c644332474570463033315a4c5361526356496132774b3355686562325731344f35622d32356466532d4143414b327067387764627263546e32463035344e527637306a75566b384633623444367961707845737855597066374f3561526d43624f595a7754524174713873586e59744e4a4a46347a6f696230305142466d4d7661454d437946764a6e764a6c5647486c3352494a715641785748697975647466325735497573486f43366363436f5f794e707249336b4f4b326e4e3363327644794b524f62735336644f6b616f6e715644444c486d792d386e71326d4d46397146347155563463674d516d764b725578546269724a3939516b6538774e6c6177653132525f4144554a416c6d4a576234567767764a54654f7a3065746f72376355713970646a4d78686c796261737972364d69724f4c596f386b69756a41414e303266716a7855324e6c455f5236446e413273426132325539786e5177393378787430396f5875654c74316551727330442d53726134316a6d4863734a6b384c754d4862674251635139566e414f484647435a67364f75795f6a3044576576575538614353456d7563513333506b5a782d5973426d362d374e51424c6b4c48615972494b535736625675797349746f503742734b796c506f6c6c736e35457047596e734f72685f4375763057675957586f61444d6b6e615f416d6c6343514630456236474d3641314437487a317a6c35486f786b784c63305258455673364a6e5931	1479	claude-3-5-haiku-20241022	2025-12-27 23:32:32.779936+00
07e9cad6-ec9e-4130-8675-e37cb3cb214f	bcccb076-8f87-4748-95ab-d96722e5f254	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055477935734b6a564c724353797a54547764424a2d4d376a57687546556d6874704435597a425239735a7330447a63745058625f6656524261766e4b563476465354544a2d4f6652784756365130475953737975374f64466743642d714b3354514b5a64767055666855756741556f3d	0	\N	2025-12-27 23:33:13.004221+00
55b41a6f-d753-4100-9ea8-5637bb846a92	bcccb076-8f87-4748-95ab-d96722e5f254	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705547793541713251676759636b5258446b373168755a36736b6d343831314a6b32594964774465706a5a5a68346e714d6e6742324c3459495f565045487844566b7a63667a3265614c76444b61505878715a576a45395a356a714f59494e4f51743041455047764845316c42306a7667452d4645635178775a31585f3368655467493658736a7a6f6f3077386a6437364563614e644a433666305f346332343868396c597051586e76695f627469636a41642d6347473230426879643755487476536d61764b664f30737065316933596d744752305957484839415775796e50654d6a5177623067426b516263474a576347475176476447574e6c53567061457a4c72484e47667a426f4a75325770626e7155725635784631724f464a474d686f4f73586e39723853745068665a324c55654d2d504a526a4f7836395752446546517a7677386f434d49515a65576d4545316a675a4937754c6244684b436b46524646316f573765353238305f4379496d44574571346a74466c3854766744576a5675716f4f2d574a56584d63546273354c4a5535647930714b524a4e4b67513653425673715a59317342764534756f4c3748436471475f5f4e5342327576566532625261536e616b41764570725937587a6253554172765f6145536574564e3767654869436d7538583530396245574d77393776305270624156337364796d5976686d726341686a57504f725546795852796e70504a5062627269323771567250633855617044356e6664457a4a68663242766279317471453970585f484942525a5a374f68496348525259767836504c485352793464784b615933766f52684e446e71524b526939364a7334645745452d736a67496d484c4442786f3432674e3172334b4c7472584d6b315371685338484d563368737a6e346b326c587a336d7664457136576352455f4e53355666624e68474d72744b5a666b57524d3552493950394c4b65504e71416435396b496b5042375757695849726762394c647a38686b3059727337596757384c4f33624d5f326231352d6a4c366143476d79306e62626373497948664442796e69656663354f7943574b772d4147706f557841456a6848536c4d59746d634d356143326a573378376f6c54425177526d6e4b58374a5f7367546f6c3646654157457a43335336356c4b7131704d41755867777648314c484a3331476b345f7a6b59526c596c677a365a6f49712d5872303876656a525f	1750	claude-3-5-haiku-20241022	2025-12-27 23:33:13.060152+00
61b8306e-15a7-4436-912e-370c5525118d	bcccb076-8f87-4748-95ab-d96722e5f254	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055477a39335a504277666139452d375252712d31304a6c572d6a4b6f5562776d34704e4a597866437851547369476761435931446456535562373579627747326f704572306135697049626b4c44684656475659336e64423857355f4138366a6177384a6f6a704f7473717a566a6b3d	0	\N	2025-12-27 23:34:21.681904+00
b2aea8e0-8364-48c1-86d7-11b3eacd3e63	bcccb076-8f87-4748-95ab-d96722e5f254	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055477a39567a7a36346d306a504561446741326a61734f36596234374c6f5150677573743337427266616b575279797869336a54567047796e377956326a5636594c35794857645f4d61597563544e53364e6a7458756d694e565a66532d5175766f65345468626e74794c6e4c45364b724d464d3068373772565754333255413373533743446d2d73386c49646252324a6878706b3643664d455f4b734c454c594775334357326a7052524c35546373466e496c4d63314d43446c7452664c664b586831526e4d786a64416451594235424a3850356856324f70356d6843386c78526b3130476c714b6d53795879696c6b4849366c65356d4253686f626b6a7246586e62314f4c7643542d4b4b4a61303045644972703539326c6c4a5f53627a72434a5169516a4e523855494e7a646b4b486737487876306a664458474c567a637153477a74446d2d4e5274573137304c495063542d416b754d666861654b7672372d59433657387a387461334653356978624d6a4245792d4c7a51614872695858425a65346d4c536a4f796b49716252664b394d775456732d6f70366b38464c6b427835776a42515f615363696563717151347464734350424d4f427637484f4251426d6e71754f55764874737a68794e4146527477527568783279415656327169367459756f5a6a597047746c34567378756b50336f6374494c2d67564a426c32596d707a415378576d645962757538552d6f5441317349397945667a7862536b79703653557852685335496679664662644a424b6b5a4f6470354e51506c746546454a38584a594b4f39324e634c6f69572d30537336714f5f3361775f4f446a694d43435952593942496744675949644a4d4737315a5650593653545f315a59357a6435434259774350674f6f54336a59365a715364424672564761546468522d714f4352372d2d457a525168554372736b7868613434734853395265536346584f4673444d4f4d366d47722d39443159565932624e3836506f654a49476d5f5a522d4a384f7230555162343841665977774d6636444d4f4941675a4c625970794e6f396b69614859545131675663443765666c31334f4a4f644f312d7430534e596243536b556f6267515641543851684a524370372d65635972646978574158	1927	claude-3-5-haiku-20241022	2025-12-27 23:34:21.73863+00
a0587906-3fd3-4550-951d-a176b0fc97cc	f08df3ac-ca8e-41e2-9bf6-412854ed5c09	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705547334b38582d43314c54444f425976636371334c782d5144615874336a37776b313035784e3554553961596376552d6a696f365f4262326a697163674c4d61376f4e745946557766723934526a6e4163497a656236376178485a386c63615250514a6d4e784f55464c6e6f3567383d	0	\N	2025-12-27 23:37:46.996603+00
783d7478-c61c-495c-b170-a08e0ffcf4bd	f08df3ac-ca8e-41e2-9bf6-412854ed5c09	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705547334c785374425864346d514b77484d61496e5f7a334d74353666716d7130684a4d755132385f726374643032694437537a48317868582d6d5739586661696d54356a2d5641432d5669766d45636c5566685978525f79313069394c42524f734e504a754471527073395177716c792d58446a4456533771475f434b754351667a664448414b676d367a6858426d77476c4c527141557573394672374f494f465f7875554c66614c4c324f6950484c754c43596f32726253314251564664656c41576e4661434747524a6b756655363068686e5868764944756773664d2d4467783774505065575f74524f7a6a35423152385732336e466563573631666e73674d2d5f6e417271376c6a5470543468414e473037506e73414c2d3466356b593839305970795a307149637274413563495f475f37576e6e30345850376f4172657a475f4d6e702d4a4736565872414237474d334d724c75774b543077616667523961462d3062696a364b69645570376b4a5853745752756d367855704c67645f74566957794e33523872743664624b7570554e5644654f41413d3d	1484	claude-3-5-haiku-20241022	2025-12-27 23:37:47.051381+00
43033cff-0cff-4aa2-8f18-822fd5095ff8	67f3278e-7223-47d7-b3a4-ff13279354b8	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270554734504d6f6e7871576d77796359795a5351746b7947515573675a73426a396a3932752d6a5656594339536b7568664852554f395f4d69516b773359476e4e6d636f4b6b504a424165743858366543687338494c4764394d4c2d306c6e5a413747553759524d5471504f7933504f3649566d4c6a49674c2d48586d42316d5769782d327462647a466567523669523857526561327477745246566a43586e4a7035594a7555316946765737365770596d41752d38737432667952525a714338694a66576877344a312d4939553368635f6d6c2d526373306b413d3d	0	\N	2025-12-27 23:38:55.676131+00
82ba8b97-ba93-469a-9e51-382d1d21f1e8	67f3278e-7223-47d7-b3a4-ff13279354b8	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270554734506449584146626d357641746f595061435a316b7176503275664241576d3052494b772d6e33396868437232367148515938563762346371646442464e644a6a6e374453305245384f3272636f465359464e577143392d596e564f4c65464f7a3158304e77566c7039503632502d6172545a56576e547753535f3358496e4277365343627743726c457446744a62536a5737673171375453346635646859797171665730396d7a6d34456a745756684679544d59666d30446456366871523552502d68527a4b623875632d3274383052487552314e743952727664494f70473043707a77623243636e6d426d346e325a6261727178466b6b4e61372d5a3551595f533044647164545458316d33365f4b7553786635693073515a6d4a5462464b314251444458464c473959652d68635873566e534779717839314f4c6958374d306c42674473556c7437787139345632614c644673364e4d6f4f6b35772d7448794766743466656562705838374442484e3142456c7670787054762d384d654a6b79484b6e646a7953424a5935534a6532425576676368736c63735f47706e65776574445738546e645337537a6555733061554b623044634575312d5766556f316a71694c6737393956736d45565a46473656726f70626f5a46766d334439365970305f6863436d2d734d477a3244536e6a4d52466a583536575835464e33565461424653572d416333786768624457725279356a43645670436f6661544c786c5030536e67694d4b344f75355445584773615968336135366e5a54634242444432732d39564547784c3768666e31306968544e4d334a37526177546331775965763973504f7372427251714a545a537a796c43753879454e726d575a52354f704c47492d2d4c393335324c53636e4c6e63385352414d4d624751544f3974306865436c4956465675414749346c33416a794676674f564d4d4231716e6e5433472d322d555a51467331574741707065794f6e7842554d76766b464437504f6e53506e5945627955656f46513d	1596	claude-3-5-haiku-20241022	2025-12-27 23:38:55.731821+00
b2ec6d3c-8d60-4f51-b197-daeb353f736e	67f3278e-7223-47d7-b3a4-ff13279354b8	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055473475625561375f42586943506b30484c6e75654e5a7979444342555849616b4530454e76634a304278744b4b6955524e494e6e647472344732365074495a5a594b7878444247626c75766365516a706c494d346c49387853733330546c6e4a334e78572d474e686864416546513d	0	\N	2025-12-27 23:39:26.622978+00
cbd84f96-5955-4fb7-bc2f-72abb9463592	67f3278e-7223-47d7-b3a4-ff13279354b8	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270554734755a76364637565f617265666b7a4155383359345f6c464c717451416a626278766a643663714b556c71384f725934515a4641704f394b68305a42754931785239715959694e444f3272623465436c73524e493844696f356775635a71546c527a366e696f78344449582d4a687347476647665257796242775169656934546865505f343854596a4f792d566d7064664b62485832534b534354526f626e4f31464175675637755f5878305f5f5047485a4448334a68774b555634597a6e4f43316f54754d45613972726857695768385f48544449764b4e694238584545357878716d77394c4b776b6f386379447979314b34707a6f44384b6f524c374d6e4c6c75655a39376a582d417676677a636161364b4d5f6a5245766f78653378384e5854675a62554c3834375f735a4438746546506d4a38734b4e6959736b794d49775170303179635138674c31617a636c6d4b434566474d47456f6374445071472d67757368362d556335324d4362727261493846733839376c55773772356e2d5f423050792d5f5a7436786150493641317067727a41524d4d6778572d3733306c79624b46676662386457496355695662556d7075316e334a3048655472594b6d4e6d784671335f53586a6552626c6d783073676c5448574546377a7355654a4c6a7053346d68503063736d6c6957594f345f6649525759753335517378374a4763324c513368395946745f41554d6f71322d49737a6c3433426d3362624f4f396162486438587734446d6a3267562d4d4c6c6953526d5a4a577178574838456152383839356379564d355a6643693875594a69484577644d324c69686a77646a6d64416a6c766b437241623044752d546e4c6e3543704e72496a2d5032355f4b4e61674276396839525848706937646c61306c4168374a48363433435766577263447a5136394f42744678716a3578314f43583772394855516263437445646b716c466e526279454349426a305455546f4f736d31453039307a6f725634434a39626e4d7477356a2d4f6a5771324d634578783937454632646c7278757164494c4d7465626c324f586d57617649634f626e2d4b32674c6a41563158593841443837337a6632454761726746766b4e375a74505a69714b5145793079494c3848457063554651534b6857664173596d4767717637446168616d334175592d78735652446c4b78613234622d56537761556935746152652d6a75756b55546d583461726f7443476e30346f7236553953545730303645513179616f5449546b5a5f5136776272675632766c3647576d4272496171716c4e376f5478574c556c5056556b45476f684b4274414164494e797149366a726950384e544a7a684c65304966384545556453306f31544b4b73457a43504f547057704f414d54336d555743	1841	claude-3-5-haiku-20241022	2025-12-27 23:39:26.677931+00
9f223e5b-84ab-48d4-854f-d7ea7d48f249	2d4f8b0c-2c91-4381-a526-296d583e04a8	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552426a363973615f52444e664b736f4430585a6365326451747659615172376738624133584369316873356a2d43596a2d77494e694a7451323475354b454672526e62554d2d6f61504e78364d63324f6973566d50424576714339434a495a662d44654830454142435f6a3858343d	0	\N	2025-12-28 11:11:31.628313+00
066c34a9-9029-4f80-b8ea-24d12c8eb9a5	2d4f8b0c-2c91-4381-a526-296d583e04a8	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552426a76334d63667537524f56476e4c4f703842474a64466d716f6f7874486d31582d5752687a4575515573556a4e6a4846484279587857553937624d445158356172797770754d47563975303257362d4a454b68705950754e4a434c4e595f6634446c632d326d5155346773332d655f644430722d48545f664859484a5f5074783770793332615272654c6465453234305a5669694a32435468746c44364e4457583650374762316269783354483249486b333833466d38733359336b635163576768555650676a44316a794a5a587a6d6650414a75677051307836356835457535663254334259454535347652647433433279587847454d753378653361484a67	620	claude-3-5-haiku-20241022	2025-12-28 11:11:31.686064+00
15a4207b-3423-4bc8-88aa-4232400d2cce	2d4f8b0c-2c91-4381-a526-296d583e04a8	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552423779356a3168587a6e3153573357467875787436756c4b4632504e536d33773979535371544365375553744b376d504d394e42696130504751464c74596b316341706e56366b794f4b6b5a77424d54574d3076316d6e71415f4d305f5f743267514475506662396b7a375f7951676a5554564c4d5a4a5143744b4c4d6e6c64325970346b4c505875654e50766d686d714b5130654147773d3d	0	\N	2025-12-28 11:11:55.915354+00
5934cfda-6db1-4f57-b3bd-80b7327851e2	2d4f8b0c-2c91-4381-a526-296d583e04a8	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055524237423333494846745f5547456a4b497272793248565574435049576e46476456697a31476c337a36755f32426c5f536135503446793078626249626f4d6b6b6c6f5a344c376c313859674567557337352d327179415458637861315f676d54537a734d6c38756d7a5433306f464942556374355737527a4a717a4e442d463265714b57644f486f31485856576f42426c4d4556755f4c354e3851506d4571774a43444a3848563578566e7873616b366a48654564744570776362366c7238714c765a77416478494a6b523573754d4b76424f71423472483874437a79465f674a79754c445a6347346777705a553533504c48704563493251645f724a6d6b4e587a684870636e6b75704548705f2d6a47706c646c39397561514c315774417647497a5763703939664b2d3033427158464e54503847686a3531435345325636676a34484f423238646e7a344b776376417744614a576a59596f534c35517a6a736a704e4a3561626935444a42566347564e61727833595a6138786d755369744977	716	claude-3-5-haiku-20241022	2025-12-28 11:11:55.976442+00
046ee100-c5c6-455a-bf35-ba6dc8522f62	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552626d6845516f7475576c39517374494a6966505f3861535962596c4e317957415844516367557a657349476a335f4d7a6f4235476e6f4a76324d474b6138396f39546c7161536c65466b32426e6133342d704b492d484c3667303363424f66377a4d68526667414673423679355f6e6f35516a47372d4e31666730576c55546a4f6a4e327a454e4241394c7249444f74334e58386338354e7539574a617448424b516d43426151525a716e56733d	0	\N	2025-12-28 11:39:18.702318+00
6d80a712-e326-4512-a1ab-66065ccd9cdd	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552626d387232597069612d733136376f573275563561364f6171575946563274664c6c31636b4c65767073353078744e654f6a434e454939682d423077585256764a44416d5441314f426344525a4c71566c56553237577468416d4a416b515a393938745067314f4270744b65664e7138564b39536b6d34353167684d73507857484575644e425f5676564d64756462444948596a574c6b7a5a71503674464149714b494d63364f465863327149367630484c53387a6e6552497a745565377967783035494a4a7159496f56624c4454627a39685575705753316b58615141305142577661774951424c643438464362493056657737556f376b536b4a66506b6654695271617a6134443567696150365368586e746944566a6f556f376c31577a70554a306a4b7a4c305265795842564f426b7570325451545a5452697a43494f716e474379703350686d486d4b634e464e59614b4b7a6876334456725450644e34536274766d6251426135686b38516b6b2d466871674e4c6c41654d376d314b654e	2433	claude-3-5-haiku-20241022	2025-12-28 11:39:18.763355+00
7278a911-c0c1-43fe-8051-96362fc6fa87	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552634168415955396330325f534573515839522d7a6879636677544b7a724a685f5f484f665a5038494333416453587777536d4c6663615335586c7344686e6147546a48666153554330542d4a4c46436254507a464e305a4b4578505039574b71465a6149793168524a59346b4d3d	0	\N	2025-12-28 11:39:44.673467+00
b0c29632-eabd-49d5-850b-9601ac99c6e7	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552634177394e6946722d764a46487a67486b753342522d75754172697a667961533966734b544d6158545562686851566a5f4a695069547758794d57786f495073585366625670485165566442343354445a7a633568537351612d5f546d4e65617253637547684c4d4f527553367073714a526435747a544e724d4e41426a79715a48506a7363524b6b7346722d396a3063434f773576796f696d4e6c755643635758684c6b646b67445865622d53424b47317969446f726147465973305959454d68474a6a2d543748316e786a5f7677684f67546166357046625271776b2d57664f3945624b3566595f5f593944684d746347774c6a312d64576c514e4d474a53662d686473496a674d614968626a6633653258304733646e56776d76547939504b704d4f48556355313876614b33514e74345a494a4657746b65725a6441764a784371504a4b385f37474e3341796434562d4341326261716e7142454a5943586c624d35774d58477747536a666d34397531694262316a3672664f6457747366352d42387a2d476c7174636d56335278517259423351644163446d644268356138365f657671666a566e514d3d	2560	claude-3-5-haiku-20241022	2025-12-28 11:39:44.733074+00
47f8a07b-b068-4f70-b09c-f3dc1313d011	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552637262384a72526b626b74766f4d59385f4430452d614257516c6b714d5f7a48424b344b317a61644762475a455a504674464d327557624e7369504f67394650775879586d474856515f41652d3147384c7234486641795a38544c7855527276554830434966587434734c504e34304b374d507967654a786539727041496a416f73	0	\N	2025-12-28 11:40:27.199592+00
b5defe1b-48c3-4625-90e2-863be405a80f	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552637259482d4b5936625132677a5474656a5f42484733796c716e687a7a7953436b4571675749716e6736344e4f335575317775323979647265543849442d78626d6d32647450513644436856705f6169473471484e797a5148634b3536584e68396d5a355377494f6a4e585a726f48314d6e582d5579666d6965464e55723357477a334a4c51564c6d6b6b65384d6d447068476e6b614c774639726c4a45393677327530793542767a4d415543546f5a6f3471354632384132334e4e67706477355a676e6e665054677934493879466d437a3655556a774543696166736b584a375a654142426b336459483770567576736e7870716638594c7763324e6e4e772d36315f5f595f6676475343614b46385275414f794173336c67776541325f497077466d67587a4f314963526351504f33485173614d384b4271707751484e613935414465666e543774326438454c4733396259475f766d4d377546656755724636623055437755792d376b6e754b65724754434a4c6b446d4a372d4241643632776f49524b5a35676a523547667a4636683847535179673d3d	2654	claude-3-5-haiku-20241022	2025-12-28 11:40:27.259586+00
89907cd9-300d-41c6-92d6-e171dae8cde0	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552644d306753484133366166453132306f4b656e4c67777163337873484f357448636f666750344a373465377a6c5f7266443251504a345a4c446270523762314833795858773476763275384552484a6932353357424264756762527277746e6d4b4e3554647350646e726e476b3d	0	\N	2025-12-28 11:41:00.995411+00
d11b55e5-4e0a-4f45-9933-7cc03579b587	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552644e507035614a767a7053764d51634a766753635f686d474c43774b43764f316f4f386e4c76334e6e703971376c3164787033465a453338796f6e4577555a774b5f6152346c7a6f6f37622d6a394e707a6645365a5f54714761634e625142466b597a6c4f566a4b6a6f6e4b2d48477758465a546d4b68636a68787655534f513068647165374b663668414d395f5658583758527638355451773375663951617069522d4f664b6269444656556471534d6b564366655f6c6b4e364d63444b4d6c453774625a6d5268664d6530354c78562d665242793153545932754751787054695477686a4973495345543978567136477a5a453654442d77304f6f46306b6f504e5f596a6e434e49705557766c6162674879466c70494236507343434970716d745f614652574b70624b656e6d374d31332d773169396d66756a443876365f624c6d4b52596d565a54444a4e5355614a7342686b484b586a57776c696b7874445f6d787a715059433275594b334b4369567a434151645963312d6b723378632d676b784848614d5252505168556669644c6b536a62773371396a446b73583838765932624d74442d5233597844717a5f6f6e47724659514257796a7359715a69	2749	claude-3-5-haiku-20241022	2025-12-28 11:41:01.055987+00
4d4d7549-cdd4-4e24-b46b-5326fe6267f9	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552654d6a716e47653739592d30564b4c7263423774456c797873657731615f6358564e6a73315154746e707a77334c6e784b414b31676b72333164307061435332364769522d42327775724c7a47616f6b324c716d334c636239743461592d636778663447594a5253596c5842335048653836335f5f6447625f486c5a4648544151796c4745594f5f49554c65727a6831497933303332764f782d66534d655048676a46713259334669326232633d	0	\N	2025-12-28 11:42:04.921343+00
c61dd9b8-f0b4-4327-83db-6800f0561891	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552654d48575647433149394b42356a447154614578725a336b4b3753554e35725f59764e47785f48534347524d7169377338782d54334d5735663859464d426b734b4f694e4770707179304a47436b3962324b376241516a366e47366462394a58507a766d43366b4d7a69476e62692d6c516146626961725f4e6859346e54726a39316e4346535a67555f565535306f736b56746636796c5349336b4161337a794d734e695a39565a3533446c52306e7968774545635f3167326276576a666e5363374d6e364f317369355f35505348574b6a53554d7a625a4c41703371385049654e4b48754c614e517a45756b3048664a63773865796e3358525a59376d41694749755176697139697834745569364e6934675032675a61355a2d65704174494c336369755077757a52526c747135713764766559517a725468513476555066444250714f744b4158636b67435337353656754c336657305a37506f775a4253336d665f68474c62694e6b782d673363475647424153504837726f4f684950397938645335446356596f7167414f535677566b6f5263793457545152584953434d646f3265484a4e6f6956306547305f3155657265754d37684e33666543797948387245484b7a31744b43774f574258726b316e716935706d5970756f3369544651556643484f36545f4f6e37326a773450533746676f6e4635343346714175637a7744574d6957474858376e55793664493165315237773d3d	2871	claude-3-5-haiku-20241022	2025-12-28 11:42:04.983812+00
46498f32-5dfc-42a7-8920-f56c3e014bda	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555265356275597038784262646d30754e71516f49654d3170436e4f5733336957575a306c2d534248414c775476695561476d4c3069384f4d4f71326f714c41383571575634536255586654584d436e474841436b514c3942785164583270437941336d4f616a647a3056384130633d	0	\N	2025-12-28 11:42:49.376088+00
d4e414a0-f9be-4683-b42a-a53b1275d31f	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555265356a426c5851714a56487365684636697037706c46526f66583945724e646347534d6b4e4e5f464f6f444143384d76455a6847304b7443575442497039686f6d416e4350514163537877535345414d55797763676b37537861435742395f65786541474137346673393936506335684f695470465068334361393237764935454f3535513753356879783332684d5f375f384e386d4d5f73766c5675714d57797a773149625830484f6e695333466242643353514c485f37714848492d5a7a4e7a795038564e7376464142316a564f6c7453685f394779556d747055624b4e5259356c416453754c6c52346d5a703870524352505f6c394b754b33435a725a4d6972533049725768426f6b4a356c72775835617938444353332d4376487a5164726b3859534c6c56784d5f6f504b6b4c3233716d4568774e357072313374544e6a61574767377a2d3863655a6d77786e726f646d4933554d35546b39624d71705341466e425f54454f67382d3859306d5a53674568525056625152705f425133446f566b425a632d615655656c6e74556d555057554b5468574775715231484449655a336d696a4941714234694c414d2d514b5f474c655a476730682d6c6177336a746e4e7133627a4e5748545752304a75332d69326866456577343247594679596d6d3050674a654b78563677514b6e5177496a723548703235556232695731744a5153477165334a717a754a4159713035514f626b5a30466c595a65346b64733469303138434f69647031483177336b6368417936636450784c55645867444932783645417a774b4c3438496d505039636b624b773d3d	3261	claude-3-5-haiku-20241022	2025-12-28 11:42:49.441119+00
4c01cf83-0891-48a6-9ef1-47db6f6f85a6	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552676f732d5139714350527564692d754b64385930653746776c66496973426331754d5a4f4537436d38746242724f6b4b39334851595958516d5f32495563484b3862694d6261342d5330335f305a767532396e4c3265446a645136666a37666433666a774f6e7930714c466f4d6a3534465f756454715f5759485564397748576d6e6a436242585f53376f3055635737384c5659664b35376d436a756e636a626e494f70467578683346356a316d6d374d5174315a48764f6265326f7455745857727a59637342616677726b38724b475774354342324173575972703044734a4a77596738346a4f4c3063387076676e6d764b5a69507642727747464b66746462536a776a544e7a4168576f735a5753333056702d364d4358584954334a473254746545376939464a615663493d	0	\N	2025-12-28 11:44:40.589921+00
c4fee637-4413-4720-9d08-bdffdab24674	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055534c482d70426f744f4e694771536579323952394574375a39744e4a623939656259687a6641426c75393452443045416e53506a4541793854634f77434f62675268334e4131774632416a4c48385645445a6a2d414751586948476e7136564d6e64532d7743726f77696b4d5778683145616f6a4744696970784d46585677426d5359	0	\N	2025-12-28 12:29:59.40971+00
52b4a011-c326-48f0-8f93-a778c1059faf	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055534c486c68716d79793854654f38317773517067454364586975685546747051755a546f5f576b484c593763306d2d695064466e316e504b4868767061582d456652766a6c3544624146466d3170784d7543365a32795f6a5970594d51514a68414c322d6b3558587052617a714f53453338316d3061584739617956645f7a744b684b457a4a322d436c4c6765465432767a784a304d447a4438304f71626869534241467643312d526b613176613165676a47774555347a7353754b777a566c7752574153397a30504b2d7672365536654f794e56577252546462743545677752356f4841506c563636394e684371595963354f346379792d337766435533415170515349357678544a354d47754b72466c53433563596b34414c676e666b4b596753456c68306b335a4c415035774276365a5175455230447049694a48705f635558646d2d55693735506a5a4f63526e395f6b4268535067473038344f45476e4f662d615f554e694f5276365f706768396568754e5257485265544b774a364d5948426334514a34417643364e7535514c374c6970474561355755316a4571636f7752483478484667686d4b6c2d537642414f726e5638567444757944636435646237394863594352624e384c4b626e4d47744136314a5179547a784e4d79427275474d7a4659524561754a42653757386966506c5f31756851327a4e7450394d51794745636d33776e5f3958737a52326c6a4d6948706b4f4e486b7a594e6174705955714870566b366a63303d	3292	claude-sonnet-4-20250514	2025-12-28 12:29:59.469812+00
3cbfda06-6106-4190-bdca-5ee0dd592e46	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055534c3352434d445f6d544a62525a65534c36684832473365415676655676706f444c39353459634a43764674556d314d5751326971614a6147584145434457476c6b614166446e43725a357262773856644e336c596f53376a6b6257756c542d73464876744a5f386163777853336b6b416c39346f726d65534574655669414d32574251586243625f4a524d70763533756349625a50724155417a6d7438745474704b42562d35503068436a4b673d	0	\N	2025-12-28 12:30:47.664402+00
c4b09dd4-1e31-41d8-b886-aad0620ccdd2	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055534c33515246704f5a6a32704e67724d76616f5044616d414b507a7559374a4a5237343842466b49514139783977774a42576b7868553153354677434a637769796b4551546648636630393531464c564d6f6f2d4176563951576b7879677350565f7342517762496d77626c424e566f37415976787963626279347233515a32765263326d456d7872666a3368585331496564534a7a2d74452d583049726d5a586b547a49616f50436a70575f4f73775a36434d4c5130514a69626f4154545f35692d384745334f46356e6a757a77663852334275742d53432d6d7152686e38596b4767424f367565473263327563595770584857743073626f485a5732674a4c397248643054744565717032504f373871444874526e4359614768356a52795544705447505a5668775f3130732d596b4a6e62366c4c6867354c52746e77464b49736b304437476c774675316d6e7565344c7772794a67355341667071305f77564c44777a7a59747054497863417a6d48683154646d775a4274625574746679783269656c59796734614172554150537077525543332d6653735a554e4d4942536a4b3453445059773566674e51373967457647776d37425f6f74377a724255496a6d51617161526b4e7138436937475672515371413239366b557a5a437278312d676a7a3933387a676d495a456553455769753366554431467855665052517637	3452	claude-sonnet-4-20250514	2025-12-28 12:30:47.721735+00
c7e403c3-95c1-4a52-aaf3-ca81bb6f0869	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555351467368495266454a5f3778464863646a57674f4b6237394478785a4b5944386f5138545545526449433439714957716478376a6e4b75496a6b4e4d333930726e3162777162784969445a4a75773545745a6a78422d436a5435596f50735a46393936753643435a655479315637533558715f78787942535768625061554c5648423070376e6a7a6d6357572d686544425569555071716d79754b59733530536547454e33334963737551796f52786f34566c414a2d31644e317a697679686961436f71727a506e6c776b39695a5537354d5356584a74617a68594d424369587a38726173396f36666b6742343d	3038	claude-sonnet-4-20250514	2025-12-28 12:35:17.384085+00
a752af37-d582-4973-9295-2e235d010625	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555351646535424e58786b664577446d575a555456473949387168426f50494f656a394367675f44344b452d756947437879704c384236756b6730614c50757566776252475333534763653445344a41434448743366394f63427a6d39304e4a7477625757422d36386a32497242733d	0	\N	2025-12-28 12:35:41.290394+00
111e36f3-a1a9-413c-8f6c-0261b50c322f	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552676f535f457472766a2d496b7731783341474a4f787736567a6e6a77434152354a373543727655434e6c486e367039555251554e633973464f7148705674776c304a2d767a676e57736a5432517764377661314953692d796b6b6957426836704546305a4d3655315931534649564a7966544a484b675273685a422d6755385465534a345850426630727450714d3247464f4935694a786731547451563536554f503878673437735375674148477a4255425f51784c7662326e66735a434b666d4e687456425171584e5f7236494d7168774b36624f796d5634706c5535673032504f64347a6736774c4b626c3841582d56644a473534384152586c5148586950476c6842494c386238696c4e436e4f67675465452d5957736d416241545a2d554a544e70446d78534c337562315649694a4178316b37594d697a766f63775177325049594a6c6e2d4e486b6452754657456c4b6c626b37522d734c4d4364614673357661766234337432424f4e6f475663336931536943316941417777713738484c796461474a68596746553974346561426b5a71327133464e50374e56725250557376495f474f33464a39774534587856457576554147755655686552336e6e3178506e38624265766945496662375f487a735f5137704b71614f6b6c4e65512d506970375f7a4366645252445831336f585135396d70566a59797373313943384747625a497658527635413351796d624b396c70635f6974515f346c754a2d39655f585778577632573678694e50736f4c424e4b6570433553786376432d5f4177592d786f4141645a676577554b6768644a47447545684977616930327066587164763661743977324370582d4d6a6858366a5944774e527971636b775a61	3484	claude-3-5-haiku-20241022	2025-12-28 11:44:40.650525+00
10effd41-6a2a-4617-b474-04a91d7e7915	8e708c2e-b928-42a9-81dc-8a9c55f2bb58	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055526955324b5234454d31644477464b776a50417456494f5876565964616643435264474c6b5744397577576d37777070574736436449504150686743695a7650476e6a4e454d5245447856672d4c6a6a5f36625a63587061325a555738435547544f61315575316f3267554630524c7a3867632d46766f4a4670677078374934513369	0	\N	2025-12-28 11:46:28.290913+00
c98a1463-a9fe-45e7-adb6-1aa4c7d4e8b7	8e708c2e-b928-42a9-81dc-8a9c55f2bb58	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055526955783530345737723952686834517243544d6d685470515569654b7a70315874676c6161663466717971487234455a5f59314b70735771722d6f775f6b4e426e62704b5a556966364d46312d71394235544e51795579306d306764496565767a734a376d696756556563396b76676c544c76334977484c597753426e4b5849676335495974415f676f5856716c35737a4c5441685a74563970526b6350324877336c336c794a5f7a78744b515731447076577959754433504f4b3349344b6d787033503553326a365434377745685f456d4c4152304b596968696a347643416468624d485f676b5746396766397854394d386f4e3945364a4c6a3946476e356e3255376a625278696b48474e376f336d62377869394735764e566c5250764758324841744a7a46655559634f6376706a4478726a317133796466474e6c596d564755617264696c6f4c703672566571397a7a764f6c525f41675f75627341564d6b765a4e377770616277544730427855504b306c56753878487a6d3841497a4656634349394543616f592d5f69556c7053737656323268675653576c2d6e57416d7769535665484e66372d4d707251734a5643625f514141524a34316e6c484773	3076	claude-sonnet-4-20250514	2025-12-28 11:46:28.351372+00
2bf7871a-3938-4ac9-9d07-7ff5e550976e	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055526a3059746b43516e2d2d574869456d39306d4f51694f355f6b7a6166634d68346f44544a3972747578484f50364d5269356c3047625841626c414f37477170473068567350666b5f68455334707076755a366738794a4d506b456633584d7333486e50464238706671716c31303d	0	\N	2025-12-28 11:48:04.21776+00
e8da2844-3987-426e-a709-f43c2f37457d	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055526a305f4d6e6937536d427a424c7958467974363363752d31466756523158674f6932366c6b2d594c56574f4c7668677739346337736253355042713938663633415f456b36614e5871724a7052536a706d4d6b5955314172352d3745465a504b394a516f673138444c46735367614446657a4d78666a6f626e3244315f4f5570505365556e783737496a5955585f704c777965754e5632586449344f6135517a564630304c417a41664e336778736b70756843364c704c374961347266415837505a4e78745959316e624c646c51764862717259713467584a4d786e48423451554b4a7534334e574b6c446e612d4b696b5257536d4c794752412d394d4b5441446779616173766a35654a327535767231535f7a54557a4d4a6f59596b2d457842483048786f464364304e7055707967536d52364444766f38307152637245726775355f5170434c5f4249547a752d2d304169624c5035546570796f7452532d5454326d73557866544b56544d39574963624f595a3648476b70484b51696e6559315f7461564c7048356b6275364f53526d4e553957703236596e6978314a363354786678464771584f414232684e3261617572424f424d7a4c6e30734f734b7954	3028	claude-sonnet-4-20250514	2025-12-28 11:48:04.273168+00
87e0a891-f7f0-4edc-bbe7-2c076bc72047	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055526b51574d6c764f314c59564f6f4d496330706e2d643664474b4132686f34733341504334614b4f4c6f4d4a6e7730634d4850546b55682d477957475a6c476351515f5f4d45677255556464706d6357443077424f31736d5479684649697458597463716c6a52616e7a765837633d	0	\N	2025-12-28 11:48:32.506448+00
12553fcd-77f1-49d9-af9c-431da2ef97e3	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055526b5136595f4b4e643936774f51646c556e2d5a45474c6247615f614674776f44632d6854536c63653636757377443562432d7139444278315f44515868766c5835396652344a707050514f524345575a793444637636516f335672355755787664755f5669433642314849446a2d6c54774e4138637a6c652d72365a38437149304478337153675873754c585f39446252554762454a5f35775a4c2d5352566b506735646153305f43745f396a3550636f7a4b314b4c73475368547351564c4153454b726b42533474793951784c55776f5474525054495168304a64427a577879716f374e376b724a666e794b694774494354455f7731654a426532437162664f3447484641624e697663557546446d57487a386d354d497572565834613349587551797764656d384162516c615833355955412d664757484744347a5f4271777368756e35415075384e665a7851484f554a337335344a747330786b79424a384652553466445466394141496b7066336461626b46466d79635841476e476f5544334c77653048516673707751775541456876533143724457586d5041366e7a354f646970374c2d4d5963493d	3117	claude-sonnet-4-20250514	2025-12-28 11:48:32.562911+00
97be5740-c5e0-45e4-a6bf-0fe3facb75a3	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055526b317a4268583337596b33545a49535830394d30597374576251724574474c505471383265344c4b2d6a347746694556684837764c63365935774c4f2d573842586977626965676943576f4b616b4f4e455631347133314d6b4234765841695032794f77554233575374737478684f4b6c745753725653745366343144395a794438	0	\N	2025-12-28 11:49:09.056737+00
6d90b107-a625-4ad4-9f89-287a267e675c	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055526b3170343162363455555747433163316c4b436966542d7047594c5a5a436754376f7a465533696b436c7030326e724e66534b2d486c6f674969757642575767414a657058364662334670757a316a5f65714b6d526f677141347a4e6851585957386743714e6a3034375855784e34345836585362736c72745849304e576f79586d484f333537396c6663664473355f4874382d6c5f6a7846484f71726247436b4d7843726a52555973577649543459396435523171417876442d7877623933324a457a786a577562585737373836506d477a675763384866554b6579384632736e6f694e5f785174386e4732726a3569574631595f3872434f61333448444462446e4479385a79794e766956346e727934634e4832524359776130767848316d4f6d7242577567424b52545a564f774c7a51674f7955757a6f615a5833573859554c684145744f35387a3633717537694b726c693854673d3d	3198	claude-sonnet-4-20250514	2025-12-28 11:49:09.116312+00
fbf97a63-6b91-4c50-9741-9a2801ff6390	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055526f417730476848573232452d647864484d596f776d374f5861562d7938355a3330417171576d626e3366384941546a356b6e7a46537939444942337941724b7769697a4941306d4f487a4a596156644e4f646f424558365249436b493856516a5a464c52705370646b627934473139384a474969485267735167303031514c4a514e5650626376314a793843565062326350537842726c544c716c4e47304c674968446531684a7030373230443661316f5166396f42777537427a6a344e655a78526765473554353870695a305f4459426f4d38506a77726f4c446d77555f4b6d3659443774305f414b514d50344a63477738444a7133644e32423746475f61616c56515172746e61415f3179393563325a5a624d33526862646e3862754673486a6a673970365f6438654b6e74627049675a6b337a70314d536d66506c6b2d394b6a7873614d774b624f6966465359723669534a4a5a534d4231684750334a78616730456363334e464a614e50545f766473324a30557a625533456d333270495f5a513661444e717455364f56614f344462474f7050323951776c375f33665f456f356b616a2d434c48674c5946434362456b5234465378594b78456d6e694f5948774e765a624e33432d6d5478637a417a6b536e5f78387358346476753668663677416b4b704e55545a4a4d356263396a367a6273486b7264516e31674774357643787a754672563356695a743376575955384a7a373571796131586b46336f33625a506e417768376a5a684f4e5f70423946453944597341716572536654656b6643584f316547534d636b43452d4a717453365932595f786d39553576455154694d38536d754344586f3d	0	\N	2025-12-28 11:52:32.300609+00
415d4f77-ccee-4259-b03a-7ee0b9bd85ed	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055526f41716f585f483131376d3747414751677968734f5a63556e2d42364d38636854324e336f4344366c663433484e53554f35714d773442773371336f6b5a5a454659576f345f42656763736e5538636f3934422d644b2d4d332d6f706a31304e42527a696e72376c6a5a78655f71485f61357552724f677a486e45534e6a446c746c5041715a5930474671716c73584e39454654583544317566683856794c4c764b4d6363624f48474c4b4d37696a4a61726a58666d64316265764250475177436656584d685246764e4374722d7a63715a6b6e34736a32315643706a70676c3849614c553056556677445941573034494f6459506257773373524c315847694f72713155433036764b6f70756c334b6144347133705365626d313847446e6d4e5f3269567643613366394673676549514d58565f4b7a6d4f5f74585f324d413149774d5931514e49634a656c45577151482d6f6b44566671365554545742576969623733676a5a376a7854694467717a3856315a6133723242726c726b38475f627057454a6d6e5f5534332d6f5a3962423149504c645979743572742d596e6835624d773157644e6a3271527552537651586e397a6e6b726b65704e4e347364343765677a79657856384644476148783561354c4b64506946474c375a6e776c5243714d6e416a5177547054474637684f42537777485967545f55334656645376434c4a584a67463175646151504e787a68663344552d4e726d45705f6f4e7965716b684574787a5948316c36453233566e4851584d715f546b70344b50414d7a2d4b4e385877384d307a6b78365552314b665945623972327a68364c695150485f5350384d7a3753384b464b4432597549344f76566d51774f39363468693535495548304549746c6d686867594461394a6f2d59583565504f5261534e714d4c31693164504e6e6a525158702d4b444d36494d62364d364b3252765f77692d4630573952755f4e494b394a313633745f717636576e4b64586a45376b43685a5a636530466c453249717856583733623761395a6c456157363262376c5f76666b387079694b345a4d793848356e50796765746d78557a6c5064364b3332394a374455456b5730397269652d566470466a3361626a51337857464551754d69783637345669767468536f6b6750635f7953376d62516d6b3558324a6a34377a4d4e45414b79517877317a4d5f465350506b584c76536d51496a36552d4239666f7a59424e746f4a384f6366586f6b435242437661764f6353504c4c727a4f56774833626646484e6d6f49533332626158796e2d36746d61734e50784257427a58494461657a6d426662545a316f52535a586d41565467345946394236564e6766315763564a35514c4e42647055537a502d52797072617978716141483444534554	3587	claude-sonnet-4-20250514	2025-12-28 11:52:32.360763+00
d1385090-173b-4d25-bac4-fe33007f083f	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055527141553574683237736b592d456145304e483464336545346c47573276654455634b70515f78657267505a6351304a38794f4e63634b6f6957727077754d437566556c4732447045475676617a594d557879613867386a6c584f4556674d6766775a5f464c63446e6b4147354b516b677a78414e7a67646b6536303430637932594338465177486a45305f485f57673333326b4745626e73785762646244336f41667858634234745271645a7062494662676b7172586176796945432d3676462d7034456833775871323578714f646f41394465792d52767070735866764b5333716a4e4f534c5168536a38535f3775627049616a6c6f4a784a4b6c666379676144784e354667556432424553437037694f4b4f5a5637595449427141394d4d377167706e53613647726e426d44346c43454a5f6f6f6c6d337879766d613638644f7330484979646e5a2d43524832744b59344f722d3171364b5052565a54444b6459635a595f5858536f4468493047704b7046687735736a45626977353331734349636f374c6e5076784d33365459563172355233747133446f4554475a46447943315655393374462d6d74723164315077784541467432422d6868576d6a4453	0	\N	2025-12-28 11:54:40.873174+00
807d0956-6da7-4fa5-8dac-bf9904b1866e	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055527141314c6a5f306d377232445163553247446d757177646f4d555839506834504c5a4a767a747756686837706a3131395f6d4d4f4e5a684651394e7479436532634b6c6c4733555675417a5a4950556544496d507676506345585479686b72505a4f52645448644f64725659634d775272544e4d7430526955374b416d6e587541694c66743542476b4c664f474668755577377874796e4e394f43616557795a6b4c546155694432375168434f683335773764676f4f524a63326d774966565547666934594b667047583657706c662d6845524d5f39576c68586a624e764c3147336855766633786a6a4959656953396f6751453953767942736c3763714e6a4745396867435f5462793333334e675366704a6e6e6d41754f4146706577636235373773745a7367545671774f6765445647755f50506e4f4a4971714c5462624e57514d41534e535f38354b5a4f446e3359746b666b355534357153526f6a75436f41364b2d6e6d365f70377333467a4b485238455f6775425467524a5456772d5150726e734e43766a3967633075582d7341565179344531666a74674c714f71746c5865693055655f4967544c6a34792d72706b5051354548494b63534a6d695f4363514c504b69305270334b776358592d6e7361726e595f6a30726c663254676c454450666a5a65317052573833515171417679505469436d2d48544d4b5f79332d454d377548395f77614d30484654735737474e5f337837492d4c4542764a7357495742344d4a644d774570694c5341777849436d6833686f4c39414f3967574b6a78646246623752494c62455f62724c53544c4675712d587548464335664946696c526478493457656541786d7537494b3858746f4636426e462d55526979684c7a5a6f7343765144746d4b784c454c623637703257376f6b644f3165716a3974553672683256676b7745397357685251415943744d4966765a38396a6f6e63696575667637324f4c6b614e5f6c584e4d7436413d3d	3836	claude-sonnet-4-20250514	2025-12-28 11:54:40.932002+00
d0cd9ebb-ffba-494f-9413-1db79e8681f5	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552736c53735f345931795f714554712d574554726830684b50327753434f4c4e477645567130654e7864476350656152586d5f334947624b4568364b6847715752774c6e79523465554975464a4e647a5433357965682d75506b546b654e6337627764677a6d6b696a33657767734a2d6d4435436857457342716b5263532d347434694b35543663647a363474654c466161474830333772504f592d6369344d5939757574394c4667504356616e784d31616b55426354656d33303879616a6962463242426e4f62506273313434745230436c504e4d3168413d3d	0	\N	2025-12-28 11:57:25.910067+00
195f630b-5a93-4cff-8b46-46983f5a77dd	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555351467037535f53507452574c4d5f723455577050464e79556d5a744b5a6e615652366d7833666e305066375739326d65774a39664231424e3731364c2d79426a3967646b3244485a4d4879585730394653636f7041533135424f3653594454526d5f5a3236506a6d4e4d7a49513d	0	\N	2025-12-28 12:35:17.320623+00
d6cd0578-2643-4ee3-9bb2-d2d66f02949d	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552736c504b50445a477155536b4d4674723037524d55646459684d693775494e62695834526f523768497a46756a583353554f4f593967344752544b714e6f486c4372626f337a356138444c5775646231316d504459566d3871794f37764b63714767656d78544f4e75436e6d556563775968514f3533504f54417063726954776356726778633344722d465961676c336d616d784d2d444548514e69644b496134414c4676774d49376e71734e394b5274376e7556736a6f4139546869395f3838626d3361714448644764687045725366524e4239694f464c682d795277485232524169775f634d56306d3441424f4a54365737313065666a734a36736b6363326b654d46622d6969764552787968726378513675506c646f3330424b67516d316149346f4c6d6637427730435156336b7a6a6777567273565135656d7347384c6a5550527a6d477849716e77767077634b316f2d46645954776453525738425545784f457638386c59726d43486c756f4168424a384179524572796d7831594678714f6d633966704954355052614f6533654d6b396a667a65697069346d707446776470503968636d495f49624367794a3065454b716b795053654739684d4c525176484c735f4a45514f515f676550674366683036344a6b43785f444567556d472d716b5873786a69365a5558682d65725965596f773651354c794a5a65576977304b482d3034786a68355378324461443367366d5f57572d725a707a52497237566d2d556e3665472d7241795751555438696f695565613869655a6c64785357785a545f323557474e485f624b4348765676394e385750566d3841434f6b35497048767664386576386a744a44486d5845424b777749797368656678657a475a4f382d7542316d7753305273706a65324f675166673d3d	4297	claude-sonnet-4-20250514	2025-12-28 11:57:25.967507+00
a7bd625e-2f30-4d6a-a17b-58b03ffb837f	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055527570534531764e413148455a3165447a555038324e6145766c593364365a62497a6f7a4147585966426e423237366665354c3143704a59506d336f4f695869656a644b726457334246554a2d2d47455273313951665148706b517554365062364f42723574775157724b426b444e78386e446a31783158634d2d384d413333304a4f34764441394c715a644935316879724b525938737646316e5f597965717563667a47546f466932624f64453d	0	\N	2025-12-28 11:59:37.748855+00
3e08aafd-59d6-4417-99a0-c4926b150572	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555275703675666774475a714c737a5f337043546e7843364e61684b31467733647153747a4747715052374e335043412d32415633385a4575475452326b374f7757627941614e3656536274395236494347786469637574455431307441686e39314135564c6862335434794b494452444d535871553651684f734179793766494d3664436945442d6e63345a5a4d5030686f7757424b626f79766333786f425535435768627930424474342d785a6d68466f7872675a4f4373744e67434c735367526a5f49565a3030726f37716342774f435f545a56505749537a76313630355f364a534731482d6b5652516b35314e4f66524e355874453650565a5969644949776b616d3744693759746261364d554e386f6d415330617442495f3939737a68326d7131735f5f307235694a6c777878464c4c64434d62526569336e4f5378587870543942356c696b49664674563945314b68687772506847726f537a4d30552d71714d4c6a5f726651645f53395a75457252797743533150446d6c64743630647a39502d535853556c67724154617836715f5244626a6773584656496432663668326f56707345755531524231567a6675347a755478707938785346396f62626266486d5848673166326c50464c58674b7654717a504b515345344651573258423338496177766355634533353153634d3949547138354b6144416d385f38476d586164597a5930304342504f3865715637496e69385a4b5a4a77664449414347752d666c423837314230303d	4520	claude-sonnet-4-20250514	2025-12-28 11:59:37.808414+00
2f59c05f-ca42-4894-918f-0f60ff6af249	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555276634e506a5732787a476337436176345739686a56686d4a715366555638714f4752335033324d4b4e78574f65754545343778624b4c564b336d3545326e7330754c33754b6a4f414f6c42655256446c6f43566b4452764f79786b71393343706f6e6b344e495538614b784d4c5f6f3457524562574e6f3567634b5a32684c347a4d	0	\N	2025-12-28 12:00:28.044969+00
12842c7a-92f7-4cf1-9a72-6d59a1b6cfc7	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555276633963786a38364f4e31305931314a5f3135413874504a7772386b4c6e7742577a684c576b375059434a64746c7148304a646c446d595a39666b524d7536365239627a4e4e4938414d787277526c2d6d6359664f47436954464d586e5075696568436c4f486a4b49766f58496a39386a5a316b6673456c51396c474c356e56336c46752d3937425138474552675a6456616135396230336d4343346e39704f746f397143586b7767794e6762444d7344734b5058534f4e5447726454687644686169336f506d4b526d4d7277584d6971366f7448593677446a324d49727038514a4c3248696b73794a416f75617a6e7742356f32485a5130393750663967392d6d774654336a614d49326a7a376f39644f6464324434714830753148674c4c5f493252737432544333486f6b4276665f6d5770464665445f694a5373446b4e6857416d72656f2d693638774e655f68326a47466b6a5f374c5f364a5564506c3558356861304f7766675150625a6235475878336e4c474335416d55326471446b304738324a5074465666336439443961772d574e3446616238756339685f3354467858512d75334d4234726d747775446248646e70385542586546492d5a63706b455055394a5f5775652d4556615a646f6632544c6350526b72466162525954726d5a63736164584b716836313755664f4e4441385243514e384d6c497a31514379584a364e444465656e624f7a587432422d70505745576b436f675779385a5562546259304142316342304a636c626e375451765a53713758666a5551645f7a5441776c6f545078446f574e352d6d4d7568513351365a306d613162755041416e48494c557a66437758613133754b565752353572675479493042304d377a536d4f2d7370564452455a555430427a2d5854746670324c3154382d4d4a79572d395845737a6f45595535695a6a6a544d6c506b37396961423148775171524b783670696f49526d3264736d642d6869774452574167513d3d	4710	claude-sonnet-4-20250514	2025-12-28 12:00:28.10427+00
2ad46d78-2923-4802-9bef-33e7fdf898ca	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055527856682d6e6e35515a614374623253744e6447432d517a5071516c4e4f36386c4773326556703035486b4d446f78394449476257773468736f41426b6a647a554f444d523671796a4d4a5448376f69556a2d4549746659456a4d5f51424a394e7961314a3769486e6b2d32774f49516844727744454c6a2d6d51624d2d77674e6c2d	0	\N	2025-12-28 12:02:29.717844+00
8fe53eb3-5f64-46e4-9268-c3922d5ccfc7	c104e48d-10e1-43d2-8166-d1de7d6fdcde	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555278563258646d734a4b546931453675436347705673765461415630554644764b65797556617a2d31577167333932784757455053694b58757330694f4339566f646d555649395f356133563562435a4f774e74476f6d5a72363162694b694d5852776852507079494b525268733337335f476c5a30553353744178336c61425a44476661517a473151706c74487349374754543079776c59764654466868634f2d6d395362725841466a4d4175684b69444c55444d59336370764659674e4f4256655444696b73524f74333637314a48553546394c625777486b546472696332617946516c4d703869643865474272505749694b734a353335754c4c7a5f5647597631795a4a685a744b4c5559635a5a326278432d4c636f774d6e75677061456b314c6b4831385a552d5937694f2d77534c736778456678655351314c506278786c43513943784f756c4177546c5f566b4e52456f5665566b4e334d30776134756e77796e304b6178495f6a56305f6c4144344f6b74766468373357706c4f48665744766541635a552d50794f36594830766e414f654263634554792d453743636a6370797146424c386a5a6a79355346793249567343462d6f377872566c4a4c304c534451766f654b324f6637474b45495461396d4f6b57322d49444a424f64764e2d506d34393170736d7533316843413651542d442d35704958452d6742697a767446526c4c69425771707547516e3833686247536e6c5a31366e6d53505876442d766462465468424f513d	4865	claude-sonnet-4-20250514	2025-12-28 12:02:29.781423+00
83a5a9ba-e5c3-422d-a9ca-7b4b7cab0993	83deac82-b36c-4312-b2bc-966d44a917f0	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705552396b54493738417979746c434c566b5f6149496261585244666c744b32776452467a6f7a446e7264335171506170374254646a646958346166325869355f324d465f635573744a563865306c706865754f5f475756394b32445743654f536755786a665248756749454c3457303d	0	\N	2025-12-28 12:15:32.984335+00
2580537a-3122-4aac-9d75-4538daf17c7f	83deac82-b36c-4312-b2bc-966d44a917f0	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705552396c797237386365537742746b31352d546c645f6e4c787a3953496c544a766e495577762d6137395847735a627841456b524674504572446f32304239326a3563784555695976344242494f6c6541765a626b715a6b543434734b7966565a4d6648666f584c4f59536539695352756a54524c616d527a63475856345553304f4e576d2d4f556730664d436257544936495a374767676b74325a4d3832425437432d4a774166486c62726f54464863505932706f4e5f33765370417a4c644279737a6c736b447155497449664d324f6a346c4a4d71764c644c71625569626b7855536e6a467a48456779655f6747583363725a4f756567736d62675a4e6361445462	2809	claude-sonnet-4-20250514	2025-12-28 12:15:33.043617+00
0e5faf9e-36d7-4dd9-a5a5-64495732164e	83deac82-b36c-4312-b2bc-966d44a917f0	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055522d666669493565437632734c554b71667637727442674a6971704c34784754316c306f4c446a69356557786870466c314d2d4e48655133774b6c62434575353939702d4b784a54776b5a746162586972567456526e4d51673077637362426f73575a5951426b6738736a4b76447878445a4c68654c61644a474469666e774c47394b	0	\N	2025-12-28 12:16:31.294562+00
f5898de6-3ece-4e04-979e-e647b12c04de	83deac82-b36c-4312-b2bc-966d44a917f0	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055522d6637754551416f4e694d595130743939425065397068557342637369433337656b6b7339676a68475066497064724b4e685768626e424d577474577a5165666c38654b4254784a69587a7638324b386b44424d626f713850507436765f6879487949426f6c6a37737842685761356b6644475758634635354569436e6b42693969647848434a6e67334175733959664d6949335467335f3731313077565661394c42496630536e6646435639527033426a62776737656a586d724a69625f5f3639383241305261456c4473386a5859613166717052477a72676971596b5678366e7942323448655870525a4d3d	2875	claude-sonnet-4-20250514	2025-12-28 12:16:31.350679+00
d4f04e03-9ba4-4d46-95ab-d1a4572fab46	83deac82-b36c-4312-b2bc-966d44a917f0	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055522d376c79705641523959767559514e6e77616d446157574d48735365715867735a5350666b6d4135392d324b6a6a386b42434d4a45336f333873423464767064524e484c6f506d41304d633353577a5978414b5a2d7a617378574e4b574f4d6c5a364270756c70632d4a4750374c49476939646a4933306f4947447237416476415f466b7445555244463461546f44444533754e6f764152655351785654345242756f65346e796f48563777633d	0	\N	2025-12-28 12:16:59.307421+00
7fbdf73b-9b32-4f6b-b177-850319524fd0	83deac82-b36c-4312-b2bc-966d44a917f0	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055522d374d366448375843456239516d4436584347634670504a706f584477326175784e355f44573733744454777253503165466534504c4139673732696f59784b4357476567646151656d7a4d37643854734948416136347648756c396441336d4d5178695453636952377359554c3868636e377743426c385557493679377951784c353746515f6f756c79364747796a7a31422d644e44584a6c3061615a713732365751784d706d76706859666f6b3364375f6d6c3755466e31624861375767436f6a783158566b77466c2d5f3332686b584e475f455a5975776d73484a7936352d456c78774137494f5a5256565434584b30735646716659744a77493977713472	2963	claude-sonnet-4-20250514	2025-12-28 12:16:59.363479+00
c303d70a-1c98-43ec-af52-555f7e022c3c	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055534a53477a304a4263516164546f2d39344761485637692d2d494d6330444e6c59657145587130595879496e75616b734c335a31366f71554b574b67376148416d3241727a563846775a597164462d4a462d6e6f5a79373845706e324b754d6c7678784b48634f6c336b36385a413d	0	\N	2025-12-28 12:28:02.523511+00
0ff4195c-b5fd-4b2b-977e-a567c07f346b	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055534a53324b665250454758596f44556d6c6475756b724f6f433972495761596b6b6f5f47695a48445a316c5430794d786838647767556f345743424d6a657a516f56566146587a4966514e4e5f45773842716f755433533656792d74486f364e4b7a68676c71333741303647734266636f6d4f33736857496e386c394d376170354a536e593977463253775844383349304b65696f7a6c66655878626156456d66634f4b31363676373941707666416e6e4431684c315766794f764a526861724c3044765f735250537564735864386e4b36646c694550786e74646d6a6b6842447563796d31416365576f5f4e7a31356d6f5459456f5171354f70517430796c734535566a3042536b633175644756583435354a56796177744f6164356a6e7064615f6139704b7945695174314c796e6d68576c6647374972386439684b545f4535746479685569584562617a4b6f466464414e3830747555595054786266634c436d7348596c6a7470525473773d	2850	claude-sonnet-4-20250514	2025-12-28 12:28:02.58833+00
7c29707f-5921-4450-80aa-b8b1bc0feccb	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055534a746b482d70435470426e2d756865545947475935586e43544a753032376847564a5036653963664f52676632526e51506b43344c7a4f4e636546346e4e2d304a32734f79345f373738706b7433695f64396c77466a6737664c714d6756636b4d4a53746d3477536f32617a343d	0	\N	2025-12-28 12:28:29.171467+00
ee900b92-fda3-4581-ac5e-c59b20af4d45	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055534a74355f4379746641724d45737562444e44563248484844326b5f6430434770785058774c555a716e4e794b4d5774494a2d463578356f4e7263663465367769454265745670446c77737939347473684d625337725a7167704c4b5a63635a556c646d6e4233763479596374596e684d7056625457585241466b796e30362d3239464e49316d4b437077554132725f696e4b52746e71316f396a5a7133427337507461784338395f37726277497363644e5f464477337a5f45745435726d77496547714b757a45494334677432766e6e6e6d4676435f5034425451326c684e5f69633268784631485a30646331504464763842346c46584a795843714f71394c3355	2948	claude-sonnet-4-20250514	2025-12-28 12:28:29.230986+00
b860db84-394e-4683-b91f-19355562f998	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055534b676b4d4e5133754e695841576f484e4e486f52416a426b4d47594d2d304d584b53616933393953646775434876536f3277304c45444e446d58456e39567471526b7768374f7772776e774e636d5155716a34315f6861626b394379346f6b56624d46566571566c505942314e436152584e3834345a75336c3769456557524b6e746c634e555f5f6b66616c7a7a6b6858306e4564446d7448466569704b423039525168354e3676594a79524951785a6834456c39417433324653594d7659654941	0	\N	2025-12-28 12:29:20.319271+00
f060b761-dce7-4bcb-9f68-970beb33f3f0	aab6c277-a5c6-43a1-8ea4-ea713b561482	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055534b677a62456b38427977437a6b554a624f31726361615770703645456b4746457372464959717439496133764356784d71765f43594650616149745038534b556b62735f674d5351737354495a446c436f67435747624b65495f4b777838375f4f6c4e54566d315f44677774382d42715033536f63336e617356635a34412d736351335f4f6665797077535150336b7047726f654f447152436b573761586c345a73506e5141783759366d792d33546732624f72505f686c35776945584568506b456833367441726e584543776c494139673074504d70764777635666456c4967334630346b657a457952745f6c6571376f5f39596b64432d317752345470752d59524f4e4e70324135527049424a706f526667765a367939515051574a6e7a7a4f547267732d777542534b2d373930432d4164496f546d6934796c4a645456364d367a54577a31747135775a6e554672783272325f6a766b44525f6d777531577a41484b2d393370767674424a772d415575454b78416f6853314f48315a38686352493047416c66636c5f766766652d4d784b71566b6f6f743434644b646136556f53627a466a30356d7574616a4434386656464d6b485138677852394e7a572d	3101	claude-sonnet-4-20250514	2025-12-28 12:29:20.378751+00
5995a9ac-14ef-4941-ab13-d6ec8183e22f	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555351646e35416c6a4d5642384b4e474b64686149375148775032554f524f7469527868556c4a4c4f6e4e6d357556546e734464544838446742756c65783649436c6357644a6564586c48624645534172744e363665495558345370364454483164367072676c517a766f42635061676e783755376e6d326b424c5a526d51794b676d4f666a6d50336256562d47587a39554a763731467254466a485a7a7a516a764a567a69506f41614b4b706377744e536f4830375441346631634b6d4a3962586e4c6d5549576972717378415a4b785371355073684d49513d3d	3131	claude-sonnet-4-20250514	2025-12-28 12:35:41.351763+00
fb7187aa-da30-43ca-8d9c-3ec16397ef69	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555351345f6b6334744c764179727a787a37635245334e4e724a78704746302d52683372435736576c4d74474f546879466e6464794356342d7a6a586f6a4b533950704d6d596a676d504d4954705f3532326e4c337879595f413d3d	0	\N	2025-12-28 12:36:08.085704+00
927de05c-7ab5-4ecb-a4fa-f962c8c6c98d	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055535134356a436d53785435534f3455496a3037456d5161466c38453441494368336b6d64703131364571746d37325a4434784456494e484d6a79696a484a4d65436a53545032477a46395156494631554f514348635f72564c6e754969796b4970344f7238373174413843536d6e686c416a615674456b4c38716b435a37513335503373486262773931374f7968456a47507038454f737752496f62454b4c6e7469515850516343465f306445575330655f633749424b3477386e3558527171453249484c4747326463474f7259714a446b52595f326571726c4232547a7865586d304e59666d6e515446667a42353062576a367667645539524650504233747075554d7030776d454c49336f42337872757a6866737377413d3d	3200	claude-sonnet-4-20250514	2025-12-28 12:36:08.144609+00
ab0239eb-77c3-493d-81bb-c8dc421a43ba	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555352546763684f46646b4d657679427a4c4e3365575f3272786d546d4a525146727a78724a635375336a42767032414439557277746644537175417a50344e6b5a486d61722d633161635f47534d57417275613662474131324458784b5155376c5a5934437834425072476f505f6552546a63735555666767355a43522d756c4f6742	0	\N	2025-12-28 12:36:35.898189+00
5d7cb890-641b-4665-9398-36c05f281c6b	3896d238-2741-4b20-8aae-3517b48ca864	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555352547336524930496b6f544552795a4c547a2d4843426e52596c6e4359556b774f4c5a463155376d2d2d693753354c5f6a612d497551506154716c316a2d746f72754732584e335838666447546d484f4d5270733951585450366c5674686774547746685261506a57777170516e47596a6c4761414d553272764b354e535f734f4e6d455f564d4b30364d464d705a626739487846585f77487255723657354b515f6c4b47396c564f36674a36326b334c475378495f6c37624437516d7031534a7030464d6c63656d735a546f383269766e71584a79504335597046674d777449695f57553442524b352d2d673d	3269	claude-sonnet-4-20250514	2025-12-28 12:36:35.957149+00
0d3f4265-b054-4d1e-9999-e11c040d1c8d	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555367677532756e78437561663856516a39366e685654685052734a73726c7169373350794e7969625a456268456842705564353556572d7655463869764b5366567736526b74666c574342466561734355336f532d33574e6130793048527275566442393349726a6a526c44553832376574414276523138616b726a69477a6136506f	0	\N	2025-12-28 12:52:48.280743+00
537563a5-e7ee-43c2-b1ad-ea70c646bae6	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555367672d72456470646e425369387639796c7573554c726432527048343038756e53333155796a7958637032415662553966706d794a587331574449384374686c426731374d4376373446493163624f4353656c395f76726c7433386d4967634675543271776371776f3950303034794243663056526d59673675535578484a59595164464c505662476a74546f6177504a71336141646a4a4a335169493948756b4541572d79486b7931374a684a74516d425458546c375654396d4a7576766d325a4d547139446c315a6f38344b4c6b6b354e6630516a4130697337594f736c5456626e35536c6658767761736e35756359665f6c774e5467576c544451795751745162442d43577756496f7156366548522d555f5434574178774451303463573330547278336a446e3858384c705f314267637a4c774b485475614264455333786d444c656a54356a634d3675597a7762384b6758355a3948614e2d6977436a4246734270444d4c7947795a30612d38644b666752664753386f2d426b6e432d47734331727776646d3662696175435466757762736348633770316933373733462d43586a5f664a735833624876364a6235505550345243436548637451655f3679686b585655386949514d363741306c52464734475766795f4b457435594257744a733158444d4f716d345955376b612d4a442d594a426d552d4e6b745371476d52744a435a305a7233504d5f75747247467234324c694c6d6b6a5259702d63532d5766374f5743464c6f7362396d645453576c45444e435f4c547676793561333748535273644c3773795f356634487134623846714d6732544c656c2d637978306135304d5f79334f36436951494856725476736141594f2d675f464a73624d683654574668586b4f7450474b6b4e6b645263425f4270795575464b6f4e6a6e69686557764e3777516144426d796e50384c334a4877576137363256424f35325050436c495a6f76415f7072576c4d7471776c555959696457744d3730756c6a4d4a6259314c64496d45706c336b786c4d4c4c5f5a7231624a454a5a446558777448565270765637675379327576754243744558785a6c4b2d65384331482d436a496e726a366b72517563583137496c547158764c6e734653727330696e59517a6b51785667472d454153526167466c69344d545254686f5968593277365a3678545a6a655f41317562306c41305430307731754769626d6d714765336533	4825	claude-sonnet-4-20250514	2025-12-28 12:52:48.348941+00
a1b5e29e-c8fa-4c37-a3b5-c8d2fbc2986b	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555368524c465052765a2d616636385738784354414b6e6a6e643631686c6f6e5967703341645f635869514831447a656d3455385948684e4932333676534274566134747a7430586955716567385132524b72586657504a6848575574523875455a395f703736647765634d4433513d	0	\N	2025-12-28 12:53:37.78935+00
89bdb886-03b3-487d-92fc-481bdbd446b4	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055536852526b776d7169795935444332557276546c4f5232664f327a54684e6253323472503431334f4c656f4951515748517a54543031447838506662694e4d463975694b7a6b6b784b35473436587744524e507a63337067325649696f596f4d325130347a61334d7467525237426f5948636730754a55476c54357975356a50692d344f67394b4e4363523042473842614c434e5a445071326c597a786f686f4245786f3575656a5343494f734c6b694b766365787238574d58435134394747394b7346577a726964344864302d35463233764d4a4e323131514f42484e685a37364744427747414c4d4f4a573133592d2d345543556763374e47376f4569384833314e7555574d724b5f4337714d586d7635493933355464485a314c4647566f7267694650765f746b5f514e713453796131304b34436d393665416c305a6c3945414e7257316475717a343136507169337655387774426f56684159796b7056383744457552536d5744673444525a6d366d66677578335f36686631564265664e55796a30736b2d6f6e433978614866677a725269565468367171664155306970704773497372303033344338566f584f3648575130544a665a735567434258364b705077494144416645676e3761316e434b446b486b4d646c3167425679475f547861544730504d78597a41616a75307153686362645f306b7959325675446350	4950	claude-sonnet-4-20250514	2025-12-28 12:53:37.84693+00
754dbb47-7f6f-4fc4-8da0-f372b95572ff	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555368764f5742716966326c5a313767757379386f76337459375a5a47626256575147586f5171524569786d47384b75785262714e79654f325f6e325136306f517857633975465a6d6d345045455f476457574e56494d345130477843477758414179704b35504944694b65667a733d	0	\N	2025-12-28 12:54:07.787633+00
c8987fd5-41d6-47c4-9d6e-205e6bddcaff	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705553687650596575697a4d314d41726e6e465f446d6b30383833636f3363797a5f712d6a6855787a30505a4f6c59794c37552d767030315f4945735a4b52727a574449463579527067446b585876357047584d677a546c4b78517949564f6d53746a6171666b2d792d52457637596f4748674f4c344b5565424561485a39476776487644434342655244484e52517169634c685866544a58706669704b4774385f52324d64722d344d7a706c5041487531676b4c4868544b62754834307632687652305a4e5458724864745765354351324e4e5a514d5f677a3275545a556b5f62354e7956514c4a5367663634657132594c66387a37456e444f4f6355636e2d3666624e464c77436362376c414475386c34304c59646e5a30346b3667646e3073594a38454163535f70714474386d556a6a61595a377a4c475976385f48552d3548525f4342526859693966504f2d6154684b5670764a32762d787579554e596e32656e4c54615574336938676654363062527156625f4348454f4a2d6a6137435041575659693252546c626e303577524e4276457034435765656c644d2d6d31696658526a424f3931344e48455a7857714b4e575a3864634e4f5974514d375a4935663950544a5079797133647077697075674c36537a6e723047346e7a664e43426951506738713847456b4a327043484a543561744b4e6837364456504a6441326637336d623444414f69554e4c7475476f61664a5361513d3d	5069	claude-sonnet-4-20250514	2025-12-28 12:54:07.847919+00
5a0d1070-8532-4022-b20d-71562a09de19	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705553695937434e62595a5a624e426f79494d5767545774616c715a4e75435555617072595955324370574165325651753935305f474372364c3066766a65785464683531624772563155455f7251426172582d5248684d5847635234724c564539776a53555855474f7574624a70364841562d6e486550744b73493050554a30416b30736975624e45767078496678325944395535734e6139413d3d	0	\N	2025-12-28 12:54:48.95812+00
7668053b-6516-401b-873d-bf573d1b18a1	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705553695a514b43796e536a753478754575396878356e2d346e7873315f73597a38305f5a2d587537506e566e7554506b38524575585f524a325a4b3531733935536e6b35794b37796b72446b534d47787847746557423968674e696e3176715a415f436c7a54523733455952444c736348464f5a674c79773634733836523058516935737258466d336b44527a69316b3058724f68476d306f70534b69396676366f76554859373769444a5f6a776a77595077534b4d3677366d34522d6c587658736e414b52464d43447a5678633931693235576c676c5557486a73706a6c3774714a6d795031625f7a682d7658503172387564685131524834593958754a6b634b52354d794e386f31555942734a615778645a5a477464526341673448724c63676a615f38376b4846316f35414c666e767a773854463648754b5762485f6b377a3046304f7a68705a737445465a3543705f394a374756704b77765644737a486d76772d6464753661564c6b5a4b6964336c4d7541785376364464425630724f764c7679487977737849527965344f3542724268396e6f64523071384738313132394967345930344e4c33687337794b66324b346a454c73336b45617143755a79724650584f6a3966495a6374664d596b554e4b386744735835426b686b41776270756e43454538683366337472326f3559596e663456464578665f474f5553566e544546645f594b783775696e5562306d3544324b41514e6151366b57316a546c5a66374e5a775959515377526c525563696b2d746e5a51446c67716b3749594b4f4b614872656b59306f684a6b4b5a5376386646687770695844613049526f7267313334566e38666a6e51736d4a4d63354a685f6e7a495f563672594a4d2d346e624f6a6c354c6c43446d4773466c324244512d366433505141674c754f6c7532664872346830627a78484d396952526b4e684f4e6f3158614a30594c6b53757545434c496a3065774279655f51796450684752556b364b705932765f6152326c414e4e734b365945316a72454952545138476e5f504f4c36505963544b544f42785937303366654342664b7530555f4c564575504b5144363655726853663161374e7546537937754d567731343445655653683964464457475f3041414f79374a664149356351657631566d70656c376b53586f4a6249736f6e7a39586c2d505a68567470394c476e76594d65435f48514a324437526f36724d424d386c444774414c6879684570464650496130303372545579356a305161724c61476f6c656941353069675f52443639677046393178374e355f785a6c64765f6b425a484e4437304a3634315766363246442d744f724643497a6c6669645678734a2d624a4f782d6b53496e46795748417045655a76674b6c58324a6d4d75724a644e4454	5297	claude-sonnet-4-20250514	2025-12-28 12:54:49.015801+00
27b80e47-84cb-4204-a127-79bfc52eebbe	cad6bcf7-901e-42b4-a5ea-aafe4f673196	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705556754b6a77585068637a436f586846784e6c546d7954395167427a33334e37563133594c5a434b76765144522d39353578626d72676879324c6377303447797a7a70796d5f44415278504f47687535743469544d703948684936455359664867625a395535774c4a7a3163416b5258372d4b4a4d656c4654454e62666377685764506f4c665764577a5345314779586e52446c6a664d456b673d3d	0	\N	2025-12-28 16:32:10.287059+00
00e185c0-3e31-49ab-86cb-01d2d7e3412f	cad6bcf7-901e-42b4-a5ea-aafe4f673196	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705556754b63753646586e5f536a5a4e68724f6e38493951724e6c6a52416d53575a4735627231754d376a707578457843714d4f584b334f306d476f41715f4c6364496f36327635355054412d54774b4c7946796c364a59755f446c5a37716b764149476670734143426471546d596a3446596f636e4f3653634776386f7a6e346835416f5a71542d42616b31634642796f51323362482d3547504a4d72726479755a346c6c74544a3248435546736b7050657a4645556a7330776a626d6f424163726f485478556b514f686a346d504f5a57436f6134736b5850666e335736464d696838394458673064374f4e6e765f764c6545394a4b303142557a7556644334524446302d3934737671766365567752694d794f4f67766e42396f346f6e717146636d4c584b713736306b424c4362356768654139596937323567563630504f466e75694e616242666b67345a78434b62596e6547745454365f36566848414e4c4952356f4734584370424932636c6a5851654f57634a4a4a7a334572424c704a61767569575a336251493038495977426554435769613356507a66325a76564d4761427645484f336244564b3077564872426a395a665441794c31694c595455654f	4218	claude-sonnet-4-20250514	2025-12-28 16:32:10.339083+00
c504c5ac-d96f-4f9c-9795-9995003a55b6	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x6741414141414270555733764751674c4a516a736570356e376d5337495346542d7a652d4179625f4573303646752d2d415a304933634c415a34435a596a4b6b573066526c6a727461576f65624a4138644a716e697a6266374e307267524d4d554d73534a77584d6936364b73444778564d5f7a4542553d	0	\N	2025-12-28 17:50:39.189631+00
559e0cc0-eca8-4653-905b-11fd17415f26	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555733765975532d34616f4c76563475386e656775675149574c717a4235783771516c76797279446b666c6d3353434a32594938354d7a354d315a4d4b7870423254744756583145724e61674d4965424e6d736235534f586a38504a4854575177666c5450425a30414c5f77554871337a7a416452616a3356726e7a586c51686533386634557a7a63596a554d3745332d5875624a72677452657667646f64755a4a4b6e5346464c534250456673546b4258694255446a666b716537594f4b2d684251796f61755156464c6f4f6835344564612d626a742d71436351527662315654474a4e62376a495645686b4b5031795867693853336e2d6d526b6d4552496958635556416548516754444f677741746e502d5a7268587957414a5151656b336c485a466d7a49734b4d554c367269343238426266584959536c4f45425452417676386a5462323772584e42375865317a55634873765945485f6c3144396f7131305579556b3252327a623645483851496d6e7973614563356a2d34302d727a71705a	4188	claude-sonnet-4-20250514	2025-12-28 17:50:39.246584+00
f2c0b0ab-ce68-4817-af0f-847c41cf5754	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705557357855626131646669327a65725f56375f62683243454e374568344161326f31764f397976574f62723332747a532d62724b456b5943335f7a39386432747667316e644b7875794f795837306e7339743150482d596352665051614d6d32437559766c4e71683145546f376e6d632d676547553972632d6939617738384b6f535153	0	\N	2025-12-28 17:52:49.564205+00
7ede0cd0-2305-47a8-b670-04f27a7d2f06	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x6741414141414270555735784473666957394b72664a65327271426e63484a557870466a3174337171576c454b4355473762384d414446386c794d6742495f37765576304b437845746f457639723759427a5152576a386b6937676342544c6e62657475396d5344474d377a626a6e774638586b4451757852684732796d61775069493665714478516c515647776e6a6c444b66496e57316269356273625a5864475271642d5f6c555a414c2d47536342776149373035497265516f75347a73494f62317a4e61756f625251766150647a6a6d49714b42305f7663306d77507a5377576151356f46344b6f7261322d58704d6d5461526466706c663078464b7a5047446d35446843444b73715369524933473152516849564c32515f423633624e7663355147666677576f6559366a796835507965774e636f626f4768494a2d477a4270716c3858524f425a4f7634796c5078496f7537694f70756d5f50636249325a7051326975524b524e51786f4c583543625542474647645967376544324a344c527363474c4e70754c7a386e6f6b536b4e693178534f6245723258376b4e36444861766d6e4d5653494f495774476d72564d714f597369484f4d4c3946384b2d347178566679365865666a74767a6a6b4c594e66426d59327939437a6d486a4c6a6e706a51724e2d6756472d4646314d3646467365755741575f2d74646e2d7a5638333864635776784870332d75523576707a7650717158486356315f6a52446a4f5f763244593535356834597a47714333656b553566744d7557325a6c6147644d30504c635a5067384c7a744b6b5761423571386d354c487a725833753347556331717950785f315958774b504859584c62513d	4326	claude-sonnet-4-20250514	2025-12-28 17:52:49.613798+00
4b3d6c30-63a0-4450-bab6-2e2ee1d76c23	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705557364b36786e612d6c6a424e7373393055573159503536306c65773348506572415a305f78555f624c494751424a57446170454d7955545263444b4443765634623351433243734959686e6843514d5458725046462d35703542446f39327030446a503646696a6f343241636e6b3d	0	\N	2025-12-28 17:53:14.755507+00
0732ad04-b725-4987-82dc-1040a870b239	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705557364b35765338557a67496c4377776f706832332d456d64484c384163517153426e7838717044755068494a706970755a494d3964485850596f57646a314f616e547069356b5a54536e4c44617650756c5441574654544c57395a62416e6a65554634466c734f39515a635a31554d397172343035346a427848516e5a71375f5650655f696f76312d6251336d64415f4a5546384149414d3631534159694d5a56304a3432684b5078644770387057686442504f634533756a6f424144442d62452d507079615877705f6f7963505072334d68796d684d66466e4d464e4477736f7a44304943617941427562705371637a71574a346b466c374f2d6e7959696837546b714a3077305476453541673042622d51786a43466b624f6f474c5f2d657979527831414248365332656575754176716433572d735f78646c65706a4c4933637849444574664d306f5252596c785038745852486834437a5749734f7472655a4a70645a775434534538444831546537585848683745417a31466c6843396b5479756e6f5361774b746444326f626776546e4c6d5a3553316d415469466f5352736746322d33766d6d6a4232337132444e6742694d3854504361773768696d755a36304e6131496e5f6c38734a2d746956354d3769523253505f4d6d4f6338535269726c69697472594473654a34475f6c49685f3368395931564a514f58386162593150756975686a6d4b754c727552684e3843777045534e3248656330655f704d4a42342d7070413763343d	4427	claude-sonnet-4-20250514	2025-12-28 17:53:14.808966+00
bfa6c45e-44e8-4b17-8f0a-e6a4d5ece712	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055573659585054544b74647776585a766f53714d39505472674e53485a4f73506564627750503174366f306736542d3655764d732d497842357a745a4b723859543276626645537a646b714d7743675177756756624673386354625548304d386e4f637433455673374e52355f5f3836614f38412d4e4354496a3143782d386c796f6d4c394147525f5678626e514f444e3537726f57693950673d3d	0	\N	2025-12-28 17:53:28.818931+00
aaeda5e3-13e7-47a5-a339-0419c7e0a0db	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055573659665a664752775f395834594745436a6b4456364659645050485135304447756872497849444b49556341416f4d4642713367644a366659556e6a717a4f456b7a68586d4d2d5530494b51383644775a4b4a5a78742d4d31796a573841797154326f323730774a436a5f37666539796974704d6b523264586f43796435515a7a3437516d724e6166706654365a5752315159646455725677474c564358535837323852484158424e6670342d3950456c437058565f3261394d6b7841787a6c5170383472586539512d4172734938755749396338375a674632355951716158554f586b476755593746553478756e484d42536856313666766857632d747152687271594c76354b7635734d6658343578557467576c507a417870553949467271515361636247714550684b5042384d774c4c3937586b3553514d574d43685a71345f343755616b6f6e6762385a4c6c7953596b7373614467785961687831444a737a647039395a656b656370523666524946343838705333536677683430366a6e555a6f6346714a314d7158663473395047514148694f3952412d517742596f6d762d7a694b794167536758483466734734516355435f6a423355744c6a2d53466e574d6a547a55537a756252643661633649666346375372465a423355536d4368795955543877326c50657a74356f6843535458696a51427a2d333363396e46526d666a45766f536d376773414465666e357a78745953694c75656a5f756d596c6a456e7133466e5070395a4f51395f41522d704e47736470516551444f6f396b4534424566506d50754d44756b664a46786568525f435f4f754f3857383932684e704a4a4d366745363858425056673746775f4f416b784d6f7352386a4e505643616b3677695069527265634f305849346c704e7a4556574867686c784b6448776a387a4e54594b55673d	4587	claude-sonnet-4-20250514	2025-12-28 17:53:28.878925+00
953d96c0-2fcc-437d-98f6-d9a37014bb11	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705557367434394b45514574537055384155367a794d75535439783358345f6e4b30333436444b65367467395567716c73585279503634742d514843586e4f4d48795f685050515846654838356d4d50713254754c306f5a74734830365845466445724275614d536b6d35767a373051517a455048386f516c6530773145576f76366370773939393934774e627934656d6538384358556c6765513d3d	0	\N	2025-12-28 17:53:49.740408+00
f771de72-1a62-4f4f-9ad6-31399cfbb6c2	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x674141414141427055573674715652785f3037567532756c425043722d596d586e6474756f43554976477443304d4135736c6f614f4c5a766a4c4c5a346a58595a4632595237746139554655354d4370534c6357724143723359615f7565486634774b4b4c6f7554346b41694a424e5f46747939657633617a744348304b5761514d68394362376f6a45654c384d524c55545175496e6f6845657264335165596b524169544759433758526d5676614370426e306c5352474f733874667a3247594861727738305373665f497a62594c546d57565f71544a4f3463643144415f313568364174474e64734179616f6a757a442d745155375065727a736875745478474c587a784b696d7651534641646b464245416c4f6833636b564e4470585368685a7259414b6765553832616373644b4645713746756843367761726b65786771726e596c6c5a4e3263462d65584747647444644948686363502d394c36714a5a38575337796767682d55796b625642546c4f615a5a4144577530337379506b3342496c49436932354733464c4f4876642d554f64796375385648476f39776e5a66304b74467a486d772d5a566955487475646f754c4e7a773243325655493751437069545f6877347148716d6d6155704a78424c303530335a4f786c667268434d78387850396e2d6a492d53322d7a3935693976423646704b374d66397975556b703766665a4338507565482d6c6133767a51774a486d6230687263307734415335623863387a6f33755864656c414e6f3269467178644379524c474937416f496e764c396377744f545761797264637471394c7a696e2d73375675516437544338795a70522d5a38677339303145414d6246386f3d	4760	claude-sonnet-4-20250514	2025-12-28 17:53:49.792733+00
2b6c2da5-e86b-41cb-902b-e7451bd88129	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x67414141414142705557374d515774327335746f4b31334e52364a36675a765f37357736375f71465a504d414d674c517738564856334a774a487274397965496d5f3876784d32534e5041744549676432786b69744f616d6f6677357652366d6e7a73654c4345455054737678616b2d51594d45545a5f7458503337524b5358736b6465616e584a4c66794d6b777250567679486c76503563554c6a4b4366625049776950423142377733555952574a614e764f5a43733d	0	\N	2025-12-28 17:54:20.666934+00
d08859b4-5853-411a-8322-3a0108fc43b6	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705557374d324444685872364865516f35346f6d34466c485058676e6d466e2d7976555f4b72424a6a343749644d544c6f41744a457559474b62707878464e353354644445637a6462425359544a3530377577462d596b504a47516253464a76774b5358767436714f536e364f6b594f5f37754e4e54626f6b6a7a4173394374504e7932446a4831474a6f344e50763476303059354648786367584d64354f374c724e4d48724f54426f5238733439787342367776744f79306a4d3154543336485f4c474b7541325f383755674e41594847464e4b7272317a4779435145785656453874526552565749784e6c5161686f596772356142793643684c69553137475f4a4f56702d3270576446583748466170654f4e4c546e34345a54735648494b366c3645596353386a61505959356f5a70317830482d37614b39714956664c52514e4b39783852386c456e46704a624d3343494a454d63767a5f3547574167352d6139784b2d544d487358635a525449336a52534d4b615250454b435a572d687459416b51546f7a716c4f32466a2d59737771336b5044415954524d6f565364684462716d666f6f41395373375a53684b6d774a5541556d7a54554164577a3073396c744a453050784c395f75635065427442434437316b7552756e59335f48357a6365546f6175783165467247463031564d7a5745366f584768784b6c67445768796a6c5f5952332d5630646b6667724b6c6e33643950546d2d4570767279774c79724e496f615f4759745f68463230794f4b2d5473387559687535743135355a6a314b477339656a354a47664c4d316279473252784135325451797565446a476c415734494f7a4c4f4a4d325056474f2d582d6a624e49512d72486659346268446a61655a5645706b3769383664526c77495a7a4e5f344e5764396547556f534548426d5f344f6e5873385230324350566f33367354777a32766b39684d7235767a7734436f54484f482d546c3451715445555849474a716243635153363470306c554b424a6a5555576d62496476506c4e3154705252375a61325965673252513665753062755f586c6b46476f5870526a376c463961734a3251594959706741674c41766e705639354637744a58435942396248464a517639634b55684e456b395a634472415f6461626743774b63644c725662585050314e776342736562674977734d56456666687472325f454665346166544c6b4c555855644b5a756d61463351465a474b734e5a35475364496f5230764f38633456485963456166745f51414b7043464b50355f53784a6d794e7953426d3869635038314363706458546d5a685a635f3266565167656767564c5550627875476137636136627645705f55517a633030655169683442766849664e422d4f35744536344158686a4d412d384750684d6345526f704f6f5747527943552d6e4877413d3d	5244	claude-sonnet-4-20250514	2025-12-28 17:54:20.72172+00
4c1097ab-26f9-47c0-bdae-c9b779968149	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	user	\\x674141414141427055573774716f514b71314278354e67362d36706d6e7a7875644f546b702d576a51395430655931437962596b685a396b5576664177504b555a32706341335f775f652d583435326e6c483541316d34666a476d597849567149595874635a566d6949427767535a574d58593045457a5f617335383062566b6132343731713644416b6858596a4c4d34506b686a32624649486e54347679465a773d3d	0	\N	2025-12-28 17:54:53.350977+00
7a16243b-96a5-4d20-9556-e6ed0d5f2520	3b48bb25-c428-42b8-9d26-fa17a550f210	aac61923-7730-4691-895f-8d14aaf2d473	assistant	\\x67414141414142705557377457486271446b6174567936637166646a6a36664c55714d366e714c6f356a717577474e4c6461736133524758347a63486f5f4e44326a3572732d74555f4b7378797652344972364436773963745867637163752d54426b616a652d687042456f6c746e35653154532d4f7130476b3366374a514830344e46706130483554646a424f766d30416c413756706b6d4950596f3755385a74324336734c7247786865763759647a47346a7635395142676a663844467961512d587374614a624c6a7556614f4475417058314b4375573857375074456976513743483445562d77324e5948334f336d5831586379773866715f726d4b66466c356d53626b4b4247445379567746416b72657052427a66335f314a695f397a787a46455f4d6f44655538697a354f3577496c4b537a4431646f4349494a347059354a52394f63504b50436a5048714b762d384b54327746436b4f2d48416b646d4c514c6276746b4f66684346514a483063785649792d4152516e54444a487069576f325832562d613267346e78336c56714c5054435a6d7a54724d596c4b3744307a5f6e70327975417373614145665f4e54756b497045433871636c6b676844676c464e56656e4974334c704f4e38346f5951447047654268386a49377a6e7a4354326b685145726a365f46494573486b576477356a6e744b49374278713664337a464f64567a656a693447704d5f615736615369417764395561564a756c5366564a715f6a595970685241373534366741586c5633752d6c6a497359726e4a425949735a63515059476c4342727778565f4d72524936436c4e54427a3476676e62436b3567457233706a3944354e77566774784770456f7671594859696b4f7638307349663477613533395f3245563139444e5434547a426c5145384e6a6e47366178515a486f526f636a5346385344435167656e79312d4d61584d684c76503357706c4f636c464c523437626c636974505543546e786a5841547a6251304e6c4c36626a4c4b702d466d5a62746e6242386e677279763073486841483461385474426e376b4776375056464c4346483462612d6b49446254785545445f306f636e61575a6e57794762696e5175504b57546239704571683444667035705936563263784755305775445659384a446f433179375a58397071534c5a486b744d43326549356c4e654f33466e63783247476a666351534465646868366a7479445f39496378685273414a63706b4f693262614565737834446676776d594267434575446c2d54793038686a736a59646c6d6f424d3d	5452	claude-sonnet-4-20250514	2025-12-28 17:54:53.404435+00
e7e82924-698d-4bf7-b1c3-a4eee6dfbf59	896a45d9-9fb3-4f58-9eaa-714b34a25235	5dcfcba8-4b12-4344-af8e-e734c68d195a	user	\\x674141414141427055584379353644663551376650793144665353734c494559594e6c4276373963457558656c787942584d6b5a71534549776e34455735415747736c76335f545a4e47536d6f3547576b53714e4f6f69576a6841584c726748633431744e78524d7563766961314f445f3947344569633d	0	\N	2025-12-28 18:02:26.135168+00
057fe01d-42f3-4f81-9057-ac3646544460	896a45d9-9fb3-4f58-9eaa-714b34a25235	5dcfcba8-4b12-4344-af8e-e734c68d195a	assistant	\\x6741414141414270555843794936494c69566a4746306c48343373785276314d6e792d426757534b3647637855395174464733794d663863496a46475f326b384c746f474f59344e6f7a4c7359794763544c7533617332654a5854696d47576e6e4d6e4e6b4e49754c5a4959764d486978337a4351646a5371667471335474694538586b6e3748757a6551677071314d326962364771324e36323561694b7a63544d5155414b4f6f6d632d48456f7744324a454855584c7164363047624e554a3336775930444f4b622d4471645873384f3447627054656836774b6d61725f466d736354314c4f7a6e3173514d48326d74656c494b56414d76484d596b4943596a7579677871716a64324f4d6e754d6f3744495941544a5157566f7448344a7833706170644d684d34676c4c625244445a6b52785551474b62517456765f666c73495a59394d79664a54577a6158354e5839364d515876415372345376476d39344547736f676a635235776d3835434737554d516e54513d	3483	claude-3-5-haiku-20241022	2025-12-28 18:02:26.188499+00
6fd76db3-9ce8-450f-af7f-2e9adb0a9712	896a45d9-9fb3-4f58-9eaa-714b34a25235	5dcfcba8-4b12-4344-af8e-e734c68d195a	user	\\x6741414141414270555844545373416b674167545a73726c415542724652474635786543786a5f7846485857666178443835757141594c48344e6e76494b6c6a5355563130745a6a53356a6649352d7a427870745142487353724633787757414f413d3d	0	\N	2025-12-28 18:02:59.840688+00
375f5c30-7e0a-48c8-94d7-f82934f22f66	896a45d9-9fb3-4f58-9eaa-714b34a25235	5dcfcba8-4b12-4344-af8e-e734c68d195a	assistant	\\x67414141414142705558445472684569775a7951736441737a516b785a6f7948734375645038747274536a3151783956385170796c4b52442d3945497471386d5467475539732d46704a775f5f6e53566c3455656a4266546c674343556433375a4b4a6174306578305075667134326d34616d63774375736e5a5864564e412d3267725730346c525f625667646b53566f59546a31417a486d3138764457527633597a7867625f487869663148416b6f41706a446c794a437a54746535706d5078573775365670784a76424e6a4e6b4635346e73552d57533832444a3575516b43795330356432746c73484f73504548545161665977613339676a5141556f63397a516f5149766b666e5649616c79424e3663787a5f665441366e4c6f736b7837485f5a69434b5372667777326a384658634e6535694f6e7935516e50553068504e6a617451783348626e6a725854373771436364706d364875512d2d5130556f785972454635666639664f4e6d54497043315338644136366a4d626656753443755a61474973706c513234546f6949524f6f74324c547078796b382d644a625865547a386143556451393542724f56316b6a3836545757534455787a4b65707154384f49475357497834655534706b694d76436c5f5544544d6638326d5075733376555a53456631574c6752304b4832724c466f325553315f6b717757746c72625536334e454c4935576f4a5f746b346355337a4d35694469385f4e3736463450726a434e5832756945364b3664726b716d354132555a69577863584c423155334d37614536785f6e4246504f756344395356462d756756746e43556a5354784651715731595a765638794c4949344a77344c5967506d75443661316a774f492d2d4e4179307374327a6d	3442	claude-3-5-haiku-20241022	2025-12-28 18:02:59.900116+00
26a118f2-57e3-4924-ad3f-4c9199cc5166	c19655dd-691b-485e-9bff-8cb7f1156adb	1e868db6-0ae4-46dd-a068-c22f60f5d489	user	\\x674141414141427055584458397a4434624e5169384e7748706b4f3867737944507663664e4f4d533853514b69464534317a54624f42425367625842467364584165374d45513451566f5a7663496e6f347971724243774b797536497869346b4f4263513648754b4979615370774f42374742497052644c627973477974366e6e302d397170725746757573	0	\N	2025-12-28 18:03:03.828574+00
1455f5ce-566d-4a43-b000-cab4b5a39261	c19655dd-691b-485e-9bff-8cb7f1156adb	1e868db6-0ae4-46dd-a068-c22f60f5d489	assistant	\\x6741414141414270555844586e38562d566764426d4c6967344e4838512d6f6337435272412d775848593761376d526d477a55726d754c6a7a673947776a6b4b766c6378736b434d724b617830456b666273346d7035305f48724a33434e6d306c52673533555362376b35676a73396e43526b62494f334b624c5f53394556356e623735597431754f355853715837494635714571394d774d5936386f697871544a657550743165333671465057646f7a6e41424e6a683647366e70746b795568444f673239665f625f67586a53624e5833654d6d38494266523554586b374342334f6456464a59774f6e67516568376d576b5a4e42363370354c75614857414f6579636c745254507857574663635a574d5a665f62354a78496b646734544350694956735f73746b786842486a3765786c4950545a48784468504d59424a306b4f594a30314d664e5773795a4f6d77794d314f6763655a795866494265686250575959577833425431726f397577514962455655445f466763736368594b462d5f78326a4a3976545f703456696c7a34327836443143436671456565414b6932415573335145503361335076562d68774a616469747a31644436744b6d6e61624176466e69775f496e344d6c4c71536838644e73476870453641476f716168456b3646525568365a656d4b765136714d6c75744e684d3d	3522	claude-3-5-haiku-20241022	2025-12-28 18:03:03.886077+00
6f047096-93a6-4046-9268-30e8c79194ec	ecc68ac4-8c2e-44bd-be12-fbb145bcbbeb	94a61709-616f-4999-b4c2-69116dea8dce	user	\\x6741414141414270555847634a6e33595951586d426259734f53514c442d453355684d3749696d7835325059464b75706a49326834646c6f585a4b5767414732462d74354f4d436d7552786f50345555594a67636f316354366d316f337338545a5a744d7a665776766b616f6f6c6d446948314b653470695745337577444e776d793767517177364e30625f	0	\N	2025-12-28 18:06:20.225403+00
bf9fc7b0-8aba-4989-b042-4e310dd0f9d8	ecc68ac4-8c2e-44bd-be12-fbb145bcbbeb	94a61709-616f-4999-b4c2-69116dea8dce	assistant	\\x6741414141414270555847636375354a37727452765138742d4a4775435679506f305072686e336d6a3433694a556f486c685574384e714a68754c5a56756175476b59454d315830734d6149762d6674674f684e5a6a476b704d7173587330517855396c52754377527a4b4d32436e553753583446687649496448593067527a306a57503072544d3857764f6864324d444e4748453062725347546d2d643854356a5059534a66585a7158354734646654306d58774471626d6476776363795758746c536b4a704d304871795647527861513662514a34526254714653714c3279776a51517835765a64794d5f696c56745341566b4c4d58345f3745426a54725377654d774f6b734f7751633279795237326a6548494b526b79744544324f5251743870624f2d30745348346e487770676f72315533644b43666f675641716b45503046764f59434b73344866396b39686b7a74594c757a38424335624265734b6c5432336b586145494378416c6f2d555358553562447a667544472d55355143775678516245533874306953495449444a7041386c384554426945624151684a617a342d6576715345705f30644f5a4858787a513957664569377a427544716947746879425a59717031515f724839756e71445a4635375769783855506e374c75706276544f69337151536a3233474e5a4d655844625f414553503477527a4467524a42747a676f4e6e63683077427577706a514339645f684151364f5633524c35594e6e6c777838416b75387769674e735461595163672d696c7a75317043776a6c773772714f4b715f	3552	claude-3-5-haiku-20241022	2025-12-28 18:06:20.280749+00
231b7d8f-db6a-4e92-982b-e433351e6f8a	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	user	\\x67414141414142705558506a3153577a5030396b4c6d41524f38664f6b454f77465973385765304a71777572336e5f7a734756495864674f4b504c5a5049446c75632d6b4f366b39596f5976374c4a795971786c4471734c6e4f6e2d4a32646e6d6d4e5a474d4f7a6931624a4d6e5161374f643666744d3d	0	\N	2025-12-28 18:16:03.438002+00
98e999c4-17b2-489e-aaa6-301eef35864e	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	assistant	\\x67414141414142705558506a37386c6170514f5f7558446466634f73724839386b614f3735485f4e625a5668564638306e665a72704a594b526a51346e624f484f4830455f316b7649734e5379646874326a65674e64517a5735416b49416c2d636d68446a746d4a6b6735734341447a723668534332716377753963533378374d714944397651462d534d724363586c65677a7077626145736470595a4c5f41616534396a67476d75386e30367546413457776468312d4f6756444242766150545673306a5246336356437632474c693866356a6e4f373934715356552d79654f6d6e53723262573441304952496b344c4449647033675a483252625269315137583658366a52585a4542346577474746353739464e49797258516d564a6c326e6b4a4c624731647876414f446b5f66585a31587a62596d385f33755f3662762d34506b5936594b357354376a31417a67464b5f496e5a6c47784b4d504a6c434f43614d6a546663526d613353666c716a656f44545064593557674c6e68334f6b436d41696a5f49644c6179	3258	claude-3-5-haiku-20241022	2025-12-28 18:16:03.495854+00
44e77486-9fbb-47fb-8f79-e39d23cabda4	ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb	5dcfcba8-4b12-4344-af8e-e734c68d195a	user	\\x674141414141427055585141584a696f3235387549626448545f4d457275546a30734f54534270415051543269524271347668384779386d7446487344716c3576465665307633556f7a305f496d424a61736650764e316962587077477047324c655447547656503173396968346f65474976643570587965396d4853512d4d6153733437426b49577a4873	0	\N	2025-12-28 18:16:32.833253+00
cf707ec7-634a-420d-b73f-2749c7c120f1	ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb	5dcfcba8-4b12-4344-af8e-e734c68d195a	assistant	\\x6741414141414270555851414a544f6d796d66536d747363615931347365593072566879376a5550786a644c484541303369783663525947627455614179387747516d4d6d68356c336674495f655437685146526246716131546e77306967616e6c61365a35414d62763737626f6b39626c59323130776f36367578704c675f33567047514d704939376133645a3463325338747751476e6167373434796b714e4b6732466737474858396d49507159494d4357545568647863634b6368456244754374554d4f77573152354b4b7143435064505653665356732d7777314a576948334f6969502d464e4f454873337878726158354839577a4b51364d4f387a6c636e53576259614f324d5a79314b7a3746677978545772665635473730692d73436c7638377941454551546f32615f6e63367579624e534f583559414e425a54584c743359525473545333307863494c4865314d764e5f717a594a4f4e6a3246445468503462746379557864535578736a554141575370475967364374504c61765f46425666433562634a674f67574f6847426e4c53457239747833756c706c566864784b52417944525f4b635f6d4a6b566b4871496b7837567361556971426a5559646659466a374e747054546c4143496c3179326169784575385a69467973764a74387144757274544f554d444d6171454633556e336271374d5668485a3562334271416c564f4352387154557645364c3749496244475239737568362d62755663463237516546334245422d7a7178774266505449437a5744314b545748487072395a756146366c6b4f6862356e51497371435a635478534f354473696b67563042694c533046557852336750385f3235685469753230334e30315931477134466f6c6766793864316e454b6163574e702d6e65417144473034364143546e674a4f492d576f377a31635a30353053475a4d7147754f46767232306f675338393633754272676379476976415a437555303368584b7164613737633056716f65504474504d426534614b4576786e466e49733435564d5964766c32527533753032525073754e5357446c316b68444274496a6c7a44714855655f786e2d446c414d43585a514d53307035452d566a41646c74324b7967337a5f717a53435274323461655774624f4461365363704c4c3659414837652d5545674955727239647167443370624679784b612d573643496b6e4a5071444d563542726638627a464c46304e3744424753416573346e65326154694431376571626641535651513d3d	3458	claude-3-5-haiku-20241022	2025-12-28 18:16:32.903462+00
25d8bd42-d9e3-42c9-b201-cc1a18391844	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	user	\\x67414141414142705558514f655f78746b67376d4a49636a775a434c6e68734f6268454d6b4b494170487862342d72524248446866794339596544536a595232307252554b4865533376565963522d5f3874676b6c5a314d56544153497063633772667839555a586d302d63537477374b6568734165553d	0	\N	2025-12-28 18:16:46.005936+00
02036672-5746-4987-b438-5e240217e729	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	assistant	\\x67414141414142705558514f334237754169546371464751414c4c355f435f484e6c31476341753346655455506f69646a5661672d48612d7349665066706f536d3762336e43383245306e395a5f5f525258324b6e4f7a4a706d6d57695f7878546952516336556e6f78616c764d746a327976576b6a3366726c3649793755536f6b31416e524a5f786c795a366649714c324b64683163464e3864704b2d376f4b74323754655048415855536848487778723437467064536771735473726a476e456b5a47583057776b504e3773782d415261326d54665356737668614a44635a7a303576744a5276743932586e6a456c4c6a327867774a717762566a31713039455634517566473038304a326971466f66555f6c4467723071504f4f7357445876524b723177472d38305379565252506d674d3576704f4a38763975414235706931516378625956374230526434353138716a79427942396838414c3475585f576134504279314579745267723933614655664a6c6f664f71435166415738314e58366449786339664b477536566f537469685234467a4a3141716377346766785f52454542397a76525a3665477377474e595f73414c59586b7738464a4b7a5972366d684639356b775a6641526937363839552d38517270496a734138777833445130696971326e506d7452655944775552704d3754474d77356246675a5a6446624e7138686669745a6e61485f4d78567a78734e6a734c415735576b7345526a43657751514654485a4a736b65384774766d7151393378446246364c66474550356e46376356734c465f67764433683568566b746f517747757a3357466466724138304b336f79394a34384e2d4261656b345232636d337a615f375859576969537a35592d74537344	3452	claude-3-5-haiku-20241022	2025-12-28 18:16:46.058775+00
90b10792-3ea4-4271-9157-608ed5c2212d	ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb	5dcfcba8-4b12-4344-af8e-e734c68d195a	user	\\x674141414141427055585161616c6d7775577767676b6277367735637571415079456166706a645265316670434a356c4b516775335f5456694259624b6f324d385a5f4a55365179724771664b53317046326c56467845477349336e51626c76334544624c5f74496e6d7157553750544a627234424766476768686c3745614a34354a6e39454d48583130326554564e66495053686a4876415673646f30665351413d3d	0	\N	2025-12-28 18:16:58.174457+00
de73d7fd-b928-4ecb-b558-58fb0380ef15	ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb	5dcfcba8-4b12-4344-af8e-e734c68d195a	assistant	\\x6741414141414270555851612d3970475a6a653475593249395a636c414e4d79375a7a7a5a746b62316d58712d54564159497574313164416374703171764f7a4869493778492d63364974576e4c516376326b357948633769382d684f314c74576534616544656631456f7044694153384747326570513667544b6e316e486759744775424d34363766654d4431424f6b6e74784b58334138627865576a615f59345249395a4b3339717658615058544e706c534f5a304a6d6a3855515548536d654858457152595a4f36395f596956626c5a6873446452384a43464c486f542d78444a6851632d76516b45476470304662457449445069776570424a485133706d6e675a69352d386757465736612d3434474e75506c6c6663793965326f37314f765f49316b353851487a35534862466f523038327a626753497a6e6e695732716f61415a783446546345654a6e57584b67514e6a72723864326b7761327a42415a5138705067797346624f6661667353522d68537358693861363873736e4675324c316e7631556d56566148374757686952375f7033327a2d5456556a6933716a33743663395a386b64634b4d4b5a4d6b436a61774e674b336b50545555565156515056425a7357766d4d2d4942474b7366775a73747a6e7a2d577942744e56384361704c6b746f2d56514a7663673976434868537575423662734f6e44514f536575424962612d5a476a56456865666b33524d5f41757a30764b59567a4339314f6862636c6450486f49764842697a326b4e486138784c5766414731516f34796643656d3950503941	3609	claude-3-5-haiku-20241022	2025-12-28 18:16:58.230333+00
5c2b5e75-b0e9-4f4c-8b25-c29ca9c37632	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	user	\\x6741414141414270555852555651684f3956375873383731353161323677364c7149386849533333416e6e6b7144494338474d514e7961646646636f5f41626e72306778694b623951634a5367515338425365464776547942564f4976482d2d453039786a525158634332747537685f70586e474f63583573466d7555714e50513442585875324946396d695f4f52454d543776674f575f557639515365712d52724b62676e5f45614e7947446544476e6e6643724a4d773955366b495052583537414c636b6b736163706446535f43715a6c49636763616d764a4b59326b4a79386b4d52623867436f7a6134374e35723947344c5262756a53355f585f75734c5159726349475037614651444250346b426f524d4e65666c646f3072544e635f683169764a684c39524a5731374d54357a596c6f437a72424d526d4a51315a516333465a51516b334d3355	0	\N	2025-12-28 18:17:56.289405+00
20a7cbb7-30aa-4a9e-8303-38f05609ffa4	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	assistant	\\x6741414141414270555852556b4267375f777148656167374959744539447135556a71524b773662305048544663366e5257415952354f63474c30494f6c5559444d4a693750546d385655784f4d6a4c4170437359687949596a654c4876335169505a72466c57415a7339384463745936506a634d5737696138556f69715f783450773979597a6b6c314c6d65546749764f715f7633372d766e59426e75365f396e5171417048454e55634f63553956504836637a55646850635f7430366f4f7968374f565a78617564577564356a664b2d56624f4571666d50427053314b69756a30615a4d396b31454c316b6d7a463952727353575f64774c454c357170335454417a4b517542574255764c5f377741655a7a373067345757594c3970566e4f6d30657a793850414372376b544c73724b6f2d4d376f4564757677516371474a574a757643466949392d616d376c32703172446a52726a696b4545757a5173784a4d623866414b624a4a727742696e4b306b44614c49714c387446743862636b396f444c356969437033793450732d426e495255414a36367a79484844523550674b51426f65633875596855454459416c4b53424d6d4b4768794b56496246386e525069636a415a4c6f596266385076505754346a646972704b4f53654868706d5454726730664e6d754f6467634f334d6c2d39416e526f717343486f5f2d48444268554935654a4d41786355504346762d4f4e337a53374b46647677506a686f76684448734b6d63427754506d5965734870354877785736336e6a6864487a6c3549466d583374766448446e5677364e6c584a6f33357357507255354f7068496870515466436e4b43316236687349596c5674544a633943514d6448375a45355075544f48673736314e4131306d7a6b35696e506132336b32554e4272577949784f434d303647485371373079656351624f49654e61364f7466322d5673327a705568584a63436a58656a496d5a4f7a54485a4173685948712d4d3955797862504476755a43514a2d4f48476150316e6a624851504143793861624c574f6d6d66446c714168626d33305069354c5230334b5f397a6a626e7335525a535643754c6e78532d6b396d545f6b67726c6d624b524d787a4b65315963365773716b4a6a4e63526a4d766c66624e45515650336f3430344c53506c6655764a56586663574474685a6e79306d4e506a66314158756c77657239453235796a53505f2d6a505a696e775552344d757662764c555932397a614f4a376239495766775238666c566b6533433664336430486b57595f656d756d305f4f6571367a76535569597a33645471544f73434962494833784c6972584b4f4a33662d5f6f6b6f394e71455a704f3143703464613447344f336f2d636d73776132692d696b4e6662444a416157416e6d56524842526f34327773525938774670323554697972615a6578545a4b626a5a56344d5955554a54417947645544763959474e7557616164486e353339613836353753454d6f7079764833546d374c6558306a3933316d4e2d696b6557394d67457a767a7758636642387267686b3776644964376931496b2d7647694549734c41695f477546356a6d443842325f443669536f7a30575f5956673d3d	3761	claude-3-5-haiku-20241022	2025-12-28 18:17:56.345675+00
ae16cbcb-f24b-4682-824f-036d6a99e4e6	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	user	\\x674141414141427055585379422d7a4731394a5467465375576c4a426751557a6e374e5a796b376b5f6c3059664d5a6574634e52425a5835597042744f47757a694b5535466d714275444b4f3343655233396f4d585559667239715769457750347a444d79505665384a6a755f313379536639734778776a75797254667a67493838345a765549417977345a56483963627638766377364150386b455f5345665557616b55556f384c4a5f507958615f6a5a4372726c77354f307074317051385a774169647a3231725133624355426875546159464c30505239503941794a5861476c457130356e51326d4c7035704754463761756f436731396b37766141517771635254484e6e53697434654372763376752d417147686d70425a7146594e5046416433524252462d6e696d4e7966497037742d6c67686b676f74692d5576707274764b5763496a67546a726f753742633650302d5337624e4d557832533064673d3d	0	\N	2025-12-28 18:19:30.533396+00
49382d74-8ba5-458f-9976-71de5537dbdc	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	assistant	\\x67414141414142705558537978354266586a3869736a64646735765261366a734e703853472d5576685a544d4936376a7371756366526334714d6a655541476771434d3567734b4c2d5070715049746f6d44654d39427a724733317830565a666b42584e4b7a6c5233464a43694377574c674f54366d5232442d574b4c71563330584f653447334a6458623238384f476a726777786a495548714c4f4765794f6c793046396f67394c4d6e426869524964354a34465543324632542d76465676567433567a6b4f4b4c654f554d66394d3469574a36457a65736a36347a67756f6e795a533763633068654d6b41745a73684c6848326954584a78574a6836744e4d3773335838696d744e536868524b724d6c3063434d3872566531715966657a366254753344767234674b6a4844327274425f5537335943445150664670466c36696c4c4a4d4e46646f66497279414e363359463872697737496f36704d456c744456694b595664626c452d532d76545243546f5551746766536237556b33686c6578656238744d486e59557638394c5950354c50723344785644334a306d3550394f416148343955433361586772564968716963443856654d5f6a7731504b5639745354646d525558375139726d30786876623736744f5158464d75676949707939366e7135744464436f45463277515f5758525a374e303741674758444354446b714931685472755753336f77723972744b727a68525873475048495f546d6f77665a714a4d464b5431475f736166524c6e364c6d644753336a645576474f315a654b535343713671744b36446e736a5053766e6f32625f765951796b486c3133487649703378754b4d51756c684b4d66445469346c766c36513031655652564d524269376533617639333546753149525a754c4c47347644685271477a38446269384539635362514938494170774d5a676369454347566f6f58634939555f34464b5549334a395f3156467738593361464c6c6f64365038463530364c4c504d4d307146695965504b664b4832457a4c796b51462d56594f6630635846674a374c4d7271304e5f6a414c2d7039755079437778624e474e593376324a79683946696a3139584a6636646c30526e615952355a56785157317570786d41545a434e4e323977394e516c3562794966636366434d316a33714c30534a6c79543636584971752d6f76622d3533675850322d6f4c63756c7064456c4c3273666b4e414c69744a736b50466e4a4e6b54456f69516e4a7170725859595f6f4b6d527670463976775257543772673656654f7a452d7135506a6a6a7a5a32724c4c61314d63434e5f697139775f6c2d716f4277777036514932756b3556666b6b4f617536643049343355507a764a435533706f64364f66513468684c2d64776f474e4d6e52694a695935485846694b54432d69666c4536524957614f4d6b495677694c6c42656c697075336a34693437506f6236644558396e69366a7a5269393450654c357152394a574d704f2d5353685a535137652d66716d35357666526d6b2d583358633847324b68316d794b39546d684468443575667875526b3851415f556a7763455f5057732d4953376c3048484c5a4f5943556d594e5f5f32493743375377796c5f527357792d6d4d6b516575305965475f504934454a433831767a617032435632542d31476b796746637852346f716e756c52456e556166616d4d6d697264507166395659774b306f33644f7162504e323538316857326f564f733038466c444b7473393557727043766b644a303030326b6646426a4e723075554b705558784c414c5f2d704d5532426f4435694d546f65553d	4132	claude-3-5-haiku-20241022	2025-12-28 18:19:30.594468+00
5978ec58-df72-42d9-bdf7-6a29f3af22a6	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	user	\\x6741414141414270555856457a4f56674b4f32635f6f5f69756366784e6f513655434f4c2d574674494c6f5834584e714376626d755230657239524a4a6847714e4f49547859725256697a415047755033484a324c3843576d6b475f395265305f74526d55584646544e6c7155724e505638397a4f6e6557587854742d707271534d4b6f3979416d42755a76655376666a5254657455397970704b74366371486d4d70735a346f325339327754597a67574c6132494d4f4350726f514a6563375339565675596a30374c4266324c564b6273464537446b592d494f517545394849463978434658333261394d544f30694f50706a48704a426f6a574368426f5f586b32357a336d5a367a52723355484e304a77744f4377494d386731796f72716973514b724c714c34646233727a544365323751646e695f5f635551374f49737a395a693341626f4b4350316d395058746c34674e61435f4c6d76744369446b717641676b5741323041524f484464466451464c6b4b443431484d64704776334a65384f466a342d44453136734e6632305a6e47745a3963455f6730716e66336a755532635557734b556663726e5f644362545a763434514461347a625f6e43746e30315a7366584f4d526e68566a4550415a59724c52594b58575f5a38455764424e676657517534776f7156544a3367664d49725a52484f6a6f3556676630596d543050584a364473792d727561586d456e6b6e6e3676766437474853306a657955596c3557356f5f7334314732414e55653957476e4767313545645a5036515075416e30634b536d5a5679695739703845744864544f4f4b733262487639565a675f4965654e2d756a7548557a644770676c3170673d	0	\N	2025-12-28 18:21:56.939533+00
fd8dc523-d3d8-411f-970b-0e5f0fdb025b	e9a5dde9-1c00-418a-9e78-b9625da95bad	1e868db6-0ae4-46dd-a068-c22f60f5d489	assistant	\\x6741414141414270555856456276457661706c64396e6741346c783239716858756e795a3538334c546a5a6170597532463438304e79517776524930655973656675714f32696b314e7a616a44414e306e4e3579664542304c456c62434c4a74566e78675a4f4673596d6d6d35686c446d6e42584542557770393364464b634d676b4d3034457a3777645649664e395f574634564a3544586170427a704e375a637851325f336976636c586f336a676561434a706c5276724967766c34584c537a3835466b7473356f4a4d304854414e6663546c55657a3152337665754d2d6854524b39696149666e5f53394b306c4f4454714c7673725a485838676b61755050666e307457796a6241375f775f6b64416d657069736e5a4f767a665148336d68682d3041306141426a6e4d4436436552795342544f4a6d63335167354973516c734c6f2d5944366e35733132326664386c4b66464b7036444a6f68384b6f7442346e44786f4835577046673067763947316d7854415476576170375431716f7151424263514b6c41776d737835516e5966664d3136645841425a7444584d735344716131597148463379565863566b443444436d654d56584467436b384c556c7842524d5f7548677558453335665957686a6f6247597656536241504c64314a596644436a2d4f4a6e574d32744b6b726a6c7565387439766a3053475a6e35726549647a6e396c55514366564c4b7738374756612d4476705473727654483147306f4b49316c6e6944474f36375a5644515330447a4b736631654a5f4f50487a374b3462394d466f4e616876454d6d5430573753324d354e505553534b486c376d634c746278737930624b6972437a49343676416f354d7139514e555766586f414a6b713159592d76565241392d736b646b5779614b39714149514d7057385079505f7057467a50436b415f4e6568735f314255354a64694b356b4465355450763765704b3259384c474679634e734b6c75314f304a58754b484f397a4c72332d4d684c706e4664456f5a49535f7076744b4d486e4f4f5f76635050765943747a613234686f474b3671306b695274456d63436378543330562d4d3572794b7250434c7963326e7063363843496d6134574f46583962786e53775a2d73686f5a696a63616e346d31523445763447505569525431737637755a574363397074443534704c514161544e7068736651467a707149595332316a664658484c6956376e7751746b6a6c38704f4c32775a64556d2d456f7a3830483879466f74676d70506e5268522d4270585452686470466178506e766e67476150516d66494c5f7030666b367236446831502d7a3852634d455354585952634e72495436615f672d6665512d47757a68555068626e4b7a6e657978545f44644250675275694f484e4f656d757845574950795974484a5555417151726d525835772d65436935497656525257336a744d59762d705f696d397933345562536739526e4435514538735a5f476b7759657436372d686f51746e362d34615141345a656f536a584c474b384a7a50537466456b4b7770584c59324c6338494c7a4f306f5a6a4f336274633546456b61746a686638767a5871544146646d45734562614973795278357273502d4a793761645a347833354f574f6e3439746d4d7458624c69304d6536466179465a4f7841307539306e68476164776a785376314962736b567044767044337566526551464c6a757270343456615956476d726f675a6d496264704541575a3852426e56687a665244336769536c595a472d6f4c754e6377485a5658354d38326875635f47374e4363717770436457473030582d673d	4590	claude-3-5-haiku-20241022	2025-12-28 18:21:56.996717+00
6e78538b-178b-45d1-9be0-28d65e61d207	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	user	\\x67414141414142705558586f43695f37736b566d7572307773564f79555764686c436e5847623042694a434a4947686152396d36667a53636f417833345746474b59386832645359416b5462766c586837677a36596d2d497a52437177615958667856694b3033774461424353354d35303236336278746a4241504574564c47615034587259375a7a716152	0	\N	2025-12-28 18:24:40.274621+00
120ab84e-5ca6-4a74-9a7d-a25611d8cce4	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	assistant	\\x67414141414142705558586f646d4c476e31476a37764a4e4f6454786f72346359702d6a75796c3038666b7164617131457a43706b2d4c5a764e3367554a72744d3139656e374b6a3974316e6e6e6f5f3675367051564d474261436f3535367156386f6650744a3655424b614f647854746b4a52767a6f704a6b2d656b782d707662636d7a36726949396a556f784e507a53336c63644446684e2d4c39713931333376354c523872344b333571504f7472785172476238456657366a6a416a6137424b6b6c67623265325354586d3769457457485a7638564f484d6d2d574448706741794e70463041564a72594a6c6c456b6752466b6d4a34594a513938654b647955345f4c6c6a385748676b62614d5556666c5a546c7a647869764b76745639796c6c375942437261795a386e787a7a2d6f7437304356797755534f6132594c326e344546344455557166796147635f5a435149656d6474626763706a63305f3032674433786442385f38624757574d384651625f5a584a30476e4879505653597573504649305831506b705f705943614338347a6b365861625f3864386e79715331455645787a31756f3263736a62655755326f2d5f4c4a634842776f65717953383152466d4d44486146496463546f2d474c6a715a47697279625044735875726d4832346156376d6b694f6a4c6f5f786752634f6c735a3934533254586c4f437942493956336f73492d425961345a7a6d34755a5368336b4b6d6a51476f514276462d78463961306e68723272477434465175724b5759563744704d66536230306838495a6b73594c797979366766315a642d6e45574b7869644169555f643876614c62515665704e57647849714b55787758666a78685552796e7a33584d59376a5a4b78776244534a3964495430756e4a7265534675653369326832334d427a576371574b4339694e63554a486530516f47596e6f6465374d6e50557431756368503268367263396d5a4f594171424437485139344f73774d4378307774513158582d5f426f414550497a376a3062596a6a47644344736d706f52785f4c45436c425f5846785471484964754430464338634c486b5551633465594f4b496155445a7664727352734c6559564f366961534e596c364b4144696b306d354664706d4b595a616341637455727a4a37614377346171535272584b7a54487a764e4f30764d316d6765495358307772764a49434c56546b3432635f2d6b366351494847746c544c695674646f6f444a353544766b5070366a7a35455739774f513d3d	3853	claude-3-5-haiku-20241022	2025-12-28 18:24:40.328039+00
6cb75361-0ea5-4dd3-99fb-c1bfd1ecbc31	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	user	\\x67414141414142705558633637716e5374714f5a4432776f5f544d5a61515a3164435f515130475430477645453133703864386d536c5a6c69316c71396e6f70676d547048433572795a5658356932596f5230505968396847444e543363765564306e455a674c45355a636f696733315046654a6e456b3d	0	\N	2025-12-28 18:30:18.699616+00
8df155e6-7826-4feb-a760-bae51bdc7b63	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	assistant	\\x6741414141414270555863365047464354615752516e75503370775f37646134484a51715a6639314b6f7050484f54635f67626a52496e4a703462484739777765444d396c6d4f65752d4d4132693162625a346463475a63714a69474f645359356b50797168756c7462385850694f7479424c38577839634f6e712d5a79346256454e415a6944446877594963626d306230354b31586d706f58504c316338327634457937694f6c49564c544f5a4a4e77546649446449435a50424f62713857495762535376545574526c446f4f305942554d5f77317456474f6445396e5632586551426e45674333304a756e4745576938633368695f33557350756371764e45346c4c6e7475647358643758684167683841314439697a31335f344c525f722d75674f4c5a454565365f764f6330376330656b5f71697972747863446141794d624c65737a534f71755a396b427642773468547052477a724d544d576b4b43714766474830575f47734e3549624c53617868694a503633676e32684b62574a6938556a41766d6f566c6330613838727744553375785f4a4942564742535951684e4e4a76534978645963355a434e5f76754459596b68526d6e6d335f55716f5467455f475a56515761785f49344b724f614b3232754b5538655531396c68474548556c474e7664666874316a36366871633856305645714b33626276367a6f706f51705269574f4e784c5a33593851324130497a747171624a507742686f38624f6c5373373055392d4731386f667a59526e73424942725f48622d5a4f4868374c7a376b6e6873764a6b7075634b316b765773325839476b6c694e6f6e4f4838716170575a6f782d6b45654b4e30364e4c6f4a4678733d	3806	claude-3-5-haiku-20241022	2025-12-28 18:30:18.75526+00
78e7d3cc-4d23-4573-81c7-19a9e5c0301d	a61dc744-e991-4545-bd66-4fcdfcb01b1e	193c910b-629c-4bdd-8302-8baf50a73e33	user	\\x6741414141414270555864345362587371754f50395f653233363776784639415957594567794f4946573575666a75474b6956435f49725075734f7750786d6b58613166574f5a794750386a697943356e756669726a707631326d78655232547463652d4f57795a6d6e4f7264325330447753526478775f756730544c4b486c4e633542735064596874616d	0	\N	2025-12-28 18:31:20.807517+00
2650d3e6-5492-42c6-95ae-6e37666ba280	a61dc744-e991-4545-bd66-4fcdfcb01b1e	193c910b-629c-4bdd-8302-8baf50a73e33	assistant	\\x6741414141414270555864344f57447970565a646575497a7762553466344c47326e35737479614e304b4c64455f5042555a6c7077532d6b4d68596a7575745744716a79666e5f4b734938656f43723674686d744d575a73744a4c4e3653466d5f364c3658436172494f736f5378457a686c6b47303970646f347a5843625442354c615956696c394446627732426d717767523830436f77303872686351583272617436495a6c7a477954574b43304f64625a41757844425235676a67752d5072633141642d377a4a63714f704541396d7a496e476963704b5f467646576144534c6f7a4a6b6d6555353032336e774e6852305f735f35514e56663242506c4930414357414e65344b47785031324468525167686b425a7575526c636d356f4a797248304634492d4e417379524b6a4c545756437569497037306431716478785f42746672314c7636646c6538554b6f4b49695068775f6f4254686d5433385653355548516f644b572d364178783452337534696d376d384d53775f355556656f5275366f4c757159414b6249574d78624e3365617a4c66777176444e496853355879344a77456445317a4471693732533877355a4a7875695053625a7668754762784b784b7252724758484a323855557a677671305847356b5565316267554764546a337045333573766b475f6257737979725865534971344f357545426950705476596d334959545a574c6b7230556370382d774b557461797441303776614635365a46737532476541773245505a586f6b7478515f6651454a573868774a6c4f4b52424c6a3841485858557963794b5f5a775a6a47584c567573734d2d47415076377a723541356142724272744564776972776c3235302d59505852435678766a4e6e626b477352734b645f5553304964476f55547a7a6749352d6d514c4b707158594c5f57664e6e6b383647376331455079593d	3546	claude-3-5-haiku-20241022	2025-12-28 18:31:20.864652+00
7c6d6b50-1e5a-4f06-a4a5-d00cac9ff31f	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	user	\\x6741414141414270555865756d49595368546a476e334a62614977554e51574b4f6f664a4c674565534a4d306d526c6151324471394642594564787334336249616d556253462d327a6f6e667a5239337a334b6c766537684374657269586b6a457578647458534947556e42723572346c744e5158436a6d563648304376314d675f6b586b5f4e51384c4a702d6643486b474d3977444a3054697750734f3341426177336a7241677538746362342d4f594e5a6c566d446f556677697165765f693643534735527975393434	0	\N	2025-12-28 18:32:14.64749+00
9fe7f8e7-d776-418b-a3d5-2c734b294d54	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	assistant	\\x67414141414142705558657569446c515a7470653275724b456a396d6c58513237737a765f704163334a3539575433396b555865646a33754f766364325a5a6e5a636f7a5933797037696a2d68586667472d577333717a4f65344633705a5f51454c6f4d6233395730694666445775684b4c692d544a5355526163684d696262563777765a72786753544d396647336b3175704e5257484a5868365f5244446463594b3068763364456b5563705a384c766f6c776d2d41303132664f47695f67326c675132556b6444454c4f61746e385954686d6832304d7543646d446e6b7267616253423953536a49735079315948444b353541494f5a654463646c533251345331785a37624a6d6b695f4c626577746851756e333763715651465856574546303369425f645055384e616944635933686174445946316432386d4c314a4f57317958714c376f6b4a636d3065416d395f6e6e4c4774317a56525f3178624851335a76566d4a31633869694a3250416f39786b594943566e5a44635a445839696246496658633169377a49585a4a45665846436b4b6d474973477741766f56316954665744623769355a4c4e614c37764b39763837536a464b4a395a794f597875336e434d5858634c754b2d5a54774b31437233686470586b5f3130535042686a51467876666e4e4e6568454e6b78643053725348317976484e6132594d54333541464a2d446e5162396f765568533233676f6a4170443650706c46684e3956595932674a6433704d4365704676447037655333745065443074356c566763444d6b63574161396b4f48454b747170455270677144624b48624a756969307136792d674758776a4433584c6b6c5a747175503842585a614a37722d735f52644c5f53697544427564466d5a566653496b4f6266367a744b446b4c74456b776f4353382d6a53326646527777717470647a4b464b62794d3d	4001	claude-3-5-haiku-20241022	2025-12-28 18:32:14.700194+00
9c708d05-e94f-4069-afee-f6d8d6d75fda	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	user	\\x6741414141414270555866597543726e737778744532426f475235644e5763416f637033524e54514b46784d71586173706a57354e4a6676492d63303257592d6f6a4678332d5336665336535f38784b66516f6233786c787157783377736e6b6e4c72514a345f345438556b59665a4544373744523656574e76757a3834345839624f322d4964774f50677a4b54724f793948474d553058584f6351767a32735a5f4a4554524152496f4e555332784454486d6b386e513d	0	\N	2025-12-28 18:32:56.97581+00
b94c31e9-dc0a-4c6a-96db-5ef8245e517b	cd8769e5-569e-4adf-8635-5103d0541172	c980af15-468d-4433-9515-c4528ef452f5	assistant	\\x67414141414142705558665a733532757956573276646b793330706c566f56335168584b353253754630664b70655038564f2d4e5934565a53474c3138315170695a3941715348795f694a4d4437674c326e69724b65787053754a5654356a4477636747374f4c676f62587241712d41315a356e51747a6e666274344d6136394b7379704f7066795036716c5665686433644b523662334c4851574f505934374e347758337357524342366167437654473166734a4361396456544f723369495f39685243644e67446154634e485245442d41494441636b4b39306e6433364d6d5a304f35646d614b446e355f4f735f6848414d5869756b68336e4a7158735044366231705371774c31584e4b73573175656e4c7379725442367478346e5a72523431616d55514e76685532764132663375676b7a375a567a574f3663546439654e337779697934434a705f4a635068616c545f766d6f693734544a63647251305f74454c4b2d68754555337a4d39526b59733749623843323351344865426e7141677a36435536436935684559636934424c49782d625f584d522d593147626248384e6669475f4148376b666e334e4455543246326d654c6b50616e526e52794a6e5947456f427539704c4a644156416d4f4b584e4367665966534a33482d726850654e73514c436b44477172436637657a343158336d63666876715279546936545a68672d6b4878656f495072582d756e7a684972586b4a4475447668524a764262484864657361656f37384e35616d785a707634706c67566a42786d66645747486b783271625f67363645444839426f744a4a4d396c38633443686e492d4d356230663655495266717a5a485f4f6c346e315879377468515765345a6d7a566c704338706d725339764a396b497a6f647679486c31505570624a65466878424439666d765965766e683276594f4c714d517a466b4a7258412d33575a416857427030646b567254637375734871515a5048777a50434b6e70663641616b50773d3d	4204	claude-3-5-haiku-20241022	2025-12-28 18:32:57.025062+00
54338125-22a6-488f-b709-87f13e592d9b	d31b4835-552e-401e-9f72-34649d4c25a1	dbb82c3b-715c-49f7-a33f-5df195a24591	user	\\x67414141414142705558364d7949703234484e686272445a5132546369396f7037703270425a6f594a2d39485579702d5370474d4743394f4969624d58793956464347487243426b4252736957594272307a7966765050775f47626b4d44346f353770786d386f6c734d714234564a584a666b4c7976773d	0	\N	2025-12-28 19:01:32.508744+00
1f5860cc-f832-4161-8c50-26ca3450ed8d	d31b4835-552e-401e-9f72-34649d4c25a1	dbb82c3b-715c-49f7-a33f-5df195a24591	assistant	\\x67414141414142705558364d4e41784b467867384c4a766e6f4841504d4d6c4d494877726e777654656854504d56483466625956425a5449442d5a474f7168686d4d61755573344c356d6a4942573933307437324555467870494c365751767474615a6f7777684256764a78475076444534324550506a4d2d4572384e5577476e35534967505f473458752d32584c3536495354593355744d63665a446575302d3874706132456a695a5072792d4756416d7965645f646e72376c33374f507736357731506c756d4d4b41724151626434796d794165594453506b6a3354705f454d61747557684b65326b4f4f775a4f464e37555f6b3739524e6141795643717a6b78714973554768654536567a6b525756316245586b392d526d78654f633757353747426a70376d767356506e6669446d374c69545655594e576f7347664e58575967785f4a36364f5772573769385a4344376b5638764345456d6f3172763370792d4a4364576c466e30596355384344426e7471513d	3823	claude-3-5-haiku-20241022	2025-12-28 19:01:32.558693+00
6d7a5d01-44b3-457d-8ac3-cf4b30958e7e	d31b4835-552e-401e-9f72-34649d4c25a1	dbb82c3b-715c-49f7-a33f-5df195a24591	user	\\x674141414141427055583745746e6e37395773704d43435975477a4f543067544c75446a46486a483773484c626359746c44586a333242346d355565616763494e6d59634969654174506a415278575f386141736c4e51436e745957704e383743636b776c7a342d546543446436764f567457503344304b2d575432526e44353678697a7a334242496f5866712d43476e497a53664c4264382d61433836756a516444655a41646b7373625a6f4c5f5851565f5841706c426f55474667415861727a3662376a6d4d78767a486b316b5642684e6434454352534764335569643154684a747754623045633857664b6c5f496555656f74597a7a557a492d6d6b64436565545434455f6d49396f496a35426651526333535068525474454f66626e48773d3d	0	\N	2025-12-28 19:02:28.834785+00
51212982-e51f-416f-95e4-a3a6d2c6f16d	d31b4835-552e-401e-9f72-34649d4c25a1	dbb82c3b-715c-49f7-a33f-5df195a24591	assistant	\\x6741414141414270555837455744614d716664494956324a526c73774c57766c6458774f424659325575614e766236373365764b6e715456566d37365365775957503034467858706e3764672d64534d31775a2d315f302d496e6d475a783047614b7835504150685357706b3566634f576c467670736b57327a4e6b7239416b396e68704d4d7744427072336f69653668376d696670355062536355615355326d687275524d797378663657446b526a776d7058526a3348785672425a56436f42354f5852616e44335f3455634155304868715146314779744933796f636a6d69696c71666f70504579534e373050374c43504c4c7136686142746b5843747136573238716e6d57683038725a455f6e6738664453345545634b36575134664f47675777506e52466e547457586761475263544354556d34684b38624e5f764567486c7936513858536b74584a6f74465f37316a317a4876504c78514d6936466b6b78545274576253583246796f67506848663142616b4c3538572d4c3675477a51726d3359486731634f42386e6569516e774c706837706b425357614b6638704e4f5a6e766b66696477347376355535324250745751466f7174356e746f69535539384965674250723932304e4b4236315939354b4f54414b7a2d675f654b4454786b4733665f696a4a596a573958744a414b5871724c654b5f776630676b335f2d37424b7975547557507139453731593136363941344d6c7132356e2d726f705f554d65382d327154557a70704754444e4734616e3041346e776e5959505270446f44306c585a616e2d36744266533134487846684b58556d744d7137564a51444d31625f584265443479594d7767325a4649325838424a3850586f67504843354e4d6835694a34414633722d435761533833597965564f484a4163564b3561535151396d35644b465646396b75674a705f7a4e41653243674e6452484645546c79576351774f45335574666a75325974544d6e664d47356376746d6c4567366270384d416c4c38347252304234364e7546314f5448687a73667838737334486f66354932395f4835394c4d4d4e443754345f41346b30396f625368734d66734a365f75687335347966367a45514a4f4d38614273746d633842374461354b4a5266556f454163326130	3800	claude-3-5-haiku-20241022	2025-12-28 19:02:28.884718+00
5474b203-5422-4e89-8138-6ff4db97a858	07b6e5d6-7858-4fd6-a6cb-f3ff73074dc5	94a61709-616f-4999-b4c2-69116dea8dce	user	\\x6741414141414270555839766d4c674d514a6436395542755f4943495f374e643437383747425f68746167454e634a73655f545872493630422d746b3039394f32643378333435366d697047686e5f31794a666b386c4b797a38555a3855686b32413d3d	0	\N	2025-12-28 19:05:19.849802+00
c9a89479-1b19-45b0-acb1-34aec078344a	07b6e5d6-7858-4fd6-a6cb-f3ff73074dc5	94a61709-616f-4999-b4c2-69116dea8dce	assistant	\\x674141414141427055583976327253475462686d63545138544546737262346854574b2d737032303456703731644e6248616e6d744a3946795a496d6135517a6f414a5a4f31623575486f43634a6d6465336865327651354b49764d713834694a76424a414e306d4c697a4e7962426341314a75346267494f4373754b384d4b59364a717952696c6673516f53424c424435487367794352366f3651654238326e774c556c4862364f43702d436445584250766f564e344b354553536431312d67477267696a5a565941674c6d587466334e765a38396c6231345a4e727a577178616b75715f434374673642306147496b6e6c59612d6f687a395034474d616a545467493178674b37674a4f6f6b4a6f78564f4563516f613550652d6a6f3930585a6279427131784173626d6e354461466b327231395434614c70745a5a5355643839486872356369767336476b363637743670414341343761366c59535a3669326b4d585666673931624b462d555a4145774c4f36475443797a724c5239714f61634f6a6a446174653452747179533054413651506245526d39524965756334477771334b416b4c7355316e426d54625250734f7135342d32756d6734583675777557523057575353624939657a79366f6a6a6d5a504e4a62512d676157587a4461377567616261514d586973515f504173466f4672536e726932676c7641692d57305f5a324c745472786b73546337506741456e445061305a2d684769426c374e6e47454a7037335163386d7847547056574a4130534a414e4d70684e4546786b79506f54496e6f44372d306758516c5f766b633547646f614934723862436b77375a59765151324c4b6d5676496b573870317a794c41504d4a304e594e676d5643495539455a707a57733554486f75595041546c5663734c4544667463503879426d77376b7a31594e336b4d4267707048474a574e337946715a71766b6871415f6b45656168596e53	3683	claude-3-5-haiku-20241022	2025-12-28 19:05:19.90068+00
0c28fb79-5a90-4179-a6cd-517fd32d367b	d31b4835-552e-401e-9f72-34649d4c25a1	dbb82c3b-715c-49f7-a33f-5df195a24591	user	\\x67414141414142705559414b6d716d3574583044434d337479426f58496a38685666544f4a4648323454536142564a69585461374a506f4e674456725a3641334a5f434c6d744b417357425f545064584e77464e5038485433696f5165326359656a584762624a36494865445455444e32736774425f7847436b6e4a3237735568345347544f487057552d4a	0	\N	2025-12-28 19:07:54.449842+00
95a0d1eb-7de0-44e5-bd35-a53fc494e9d7	d31b4835-552e-401e-9f72-34649d4c25a1	dbb82c3b-715c-49f7-a33f-5df195a24591	assistant	\\x67414141414142705559414b43425a4c587654674c69674362593268534f376c4779676e3758487344527a6e575776594c39576267597850473841467068443848636e71763277386d43414275536a735a456c70445f324178544c616d43314c38556a4f6b566a464a7749554447366471425f4f46365a5275676966454845775f6c657544354d5f664f506d786d4f43694962644856506b386131707256454f6e744e7535716a2d63544a435f5476715677624d4b49507555785049486f684a4f56774659645850364333343452743259334b7057682d5733626455544c6a714f52504650646956334846614d3163543953654f3433666a67396f5a64585f366243566b5852744455644367422d545453354d2d44674249334d4b4b666436596161584846686f653159337772346974343066344a4f6d442d5f4b64447a6f655f6651526e4a5537494b5f5f49774f335143553834774837414a4c6636324179754c6a784c506e5a4d6a6b7444795f397462396f39386859666b76425333633979784766416f7345575350565a72436d313253514174644638613070696c5157437a325a5164435875473454654e7453335f33744161494d69364a7a583671484b5f457736517642343539496e37523033487677795a2d4b4b5150636d50566a5a4b5a33464c64795f544d6830477968314c41596c5155686a34684b4858584a48666d344876536f387066417a487837317a5a635a675f696e592d6a714a584739744e43677253423577786646507436737a575063687a5241677a6c3163757359654e74664739316670364d3149346e7250464235586c594f634c3134436e4f4d796e5864313169476b535173556e794f78764b322d66705059506e77395849724f4c355a474363396b6b76756c5535714c57797070446e693170495578737742445052646b3733466b70546333776d41524d4e315a75624e577974357a532d53744d5536442d4142756230505a674672786559344f395077504b62456c583465654b4b73775a4c6757354f7278754a6d6139496457795a485277664d387064387a764132735151785177486270456d4f5f676a354e396c7a55475539417435355563764b35587975745f3376737165644f5443715675495046344c706f5759707545777a59796362323565426b655358384f4a7150785855584c304845726f536352504d6b4a6f70656c526e6d52673333684d765f54387a536c4872457366315a6f65635a7244526d41574555714d4f4c544b685f645f78332d553566514d666d3335515430384478613938736b38316a33545f436a4b67644c454769536b5f734f364f414f736a51546131454851397349335f524f362d79516334386f6b4f6e366c785974356367575749524133646a6b7a5935773d	4143	claude-3-5-haiku-20241022	2025-12-28 19:07:54.504162+00
\.


--
-- Data for Name: prayer_requests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.prayer_requests (id, user_id, titulo, descricao_encrypted, categoria, status, data_resposta, testemunho_encrypted, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: saved_content; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.saved_content (id, user_id, tipo, conteudo, referencia, nota_pessoal, tags, is_favorite, created_at) FROM stdin;
\.


--
-- Data for Name: user_devotional_interactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_devotional_interactions (id, user_id, devotional_id, lido, lido_em, salvo, nota_pessoal) FROM stdin;
\.


--
-- Data for Name: user_insights; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_insights (id, user_id, categoria, insight_encrypted, confianca, origem_conversa_id, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_memories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_memories (id, user_id, categoria, fato, detalhes, importancia, mencoes, ultima_mencao, origem_conversa_id, extraido_em, is_active, validado, created_at, updated_at, status, supersedes_id, confidence, payload, fato_normalizado) FROM stdin;
10958ed5-1882-410a-91f1-d2676f0676b8	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Sente insegurança por não ter controle das situações	Expressa sentimentos de desprotegida e medo	8	1	2025-12-28 17:54:24.846406+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:54:24.846406+00	t	f	2025-12-28 17:54:24.846406+00	2025-12-28 17:54:24.846406+00	active	\N	0.95	\N	sente inseguranca por nao ter controle das situacoes
c81bfbc9-6954-457f-8aef-6b6757dcc0e1	aac61923-7730-4691-895f-8d14aaf2d473	CONTEXTO	Mora na Florida há mais de 10 anos	Considerando possibilidade de mudança para o Canadá	8	1	2025-12-28 11:44:43.88173+00	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	2025-12-28 11:44:43.88173+00	f	f	2025-12-28 11:44:43.88173+00	2025-12-28 12:28:06.088834+00	superseded	\N	0.80	\N	mora na florida ha mais de 10 anos
d5a7c8a2-7277-45d3-ac64-59034ff7fba1	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Passou o Natal com os pais	Família reunida em casa	7	1	2025-12-28 11:39:21.696103+00	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	2025-12-28 11:39:21.696103+00	t	f	2025-12-28 11:39:21.696103+00	2025-12-28 12:07:11.885957+00	active	\N	0.80	\N	passou o natal com os pais
bcccdb31-2fbc-4348-88bf-acbfda85333e	aac61923-7730-4691-895f-8d14aaf2d473	EVENTO	Celebrou Natal em família	Momento de reunião familiar	6	1	2025-12-28 11:39:21.703175+00	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	2025-12-28 11:39:21.703175+00	t	f	2025-12-28 11:39:21.703175+00	2025-12-28 12:07:11.885957+00	active	\N	0.80	\N	celebrou natal em familia
5c1b1322-dd86-4f02-b56e-1e54513669c3	aac61923-7730-4691-895f-8d14aaf2d473	IDENTIDADE	Questiona informações anteriores sobre sua localização	\N	5	1	2025-12-28 12:17:04.331919+00	83deac82-b36c-4312-b2bc-966d44a917f0	2025-12-28 12:17:04.331919+00	t	f	2025-12-28 12:17:04.331919+00	2025-12-28 12:17:04.331919+00	active	\N	0.50	\N	questiona informacoes anteriores sobre sua localizacao
2ad6b419-2f31-4f16-a768-3c41684979c7	aac61923-7730-4691-895f-8d14aaf2d473	CONTEXTO	Mora no Brasil atualmente	Ainda não possui visto para outro país	6	1	2025-12-28 12:00:29.203967+00	c104e48d-10e1-43d2-8166-d1de7d6fdcde	2025-12-28 12:00:29.203967+00	f	f	2025-12-28 12:00:29.203967+00	2025-12-28 12:22:57.237202+00	superseded	\N	0.80	\N	mora no brasil atualmente
0a7ef6a2-6c17-4bd5-8219-9bad9194bbe2	aac61923-7730-4691-895f-8d14aaf2d473	EVENTO	Vai comemorar o Ano Novo na casa de um amigo	Demonstra disposição para socialização e celebração	6	1	2025-12-28 11:24:50.931609+00	\N	2025-12-28 11:24:50.931609+00	f	f	2025-12-28 11:24:50.931609+00	2025-12-28 12:28:06.084958+00	superseded	\N	0.80	\N	vai comemorar o ano novo na casa de um amigo
693938bf-0c59-4033-943f-e55f7b0af100	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Pais moram em Recife	Não vieram para Florida este ano	7	2	2025-12-28 12:28:06.099538+00	c104e48d-10e1-43d2-8166-d1de7d6fdcde	2025-12-28 11:54:43.94305+00	t	f	2025-12-28 11:54:43.94305+00	2025-12-28 12:28:06.099538+00	active	\N	0.90	\N	pais moram em recife
945f15cf-4281-4721-952f-3baffcdec7e0	aac61923-7730-4691-895f-8d14aaf2d473	EVENTO	Passou o Natal com os pais	\N	7	1	2025-12-28 12:28:06.103786+00	aab6c277-a5c6-43a1-8ea4-ea713b561482	2025-12-28 12:28:06.103786+00	t	f	2025-12-28 12:28:06.103786+00	2025-12-28 12:28:06.103786+00	active	\N	0.90	\N	passou o natal com os pais
1ad456b8-9923-4e43-a67c-48b0376e3388	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Passou o Natal com os pais do Junior, não com seus próprios pais	\N	7	1	2025-12-28 12:29:24.690412+00	aab6c277-a5c6-43a1-8ea4-ea713b561482	2025-12-28 12:29:24.690412+00	t	f	2025-12-28 12:29:24.690412+00	2025-12-28 12:29:24.690412+00	active	\N	0.90	\N	passou o natal com os pais do junior nao com seus proprios pais
5a71e619-e216-41b8-9d8b-e96688c7fa35	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Tem cunhada chamada Jeniffer	\N	6	1	2025-12-28 12:29:24.696182+00	aab6c277-a5c6-43a1-8ea4-ea713b561482	2025-12-28 12:29:24.696182+00	t	f	2025-12-28 12:29:24.696182+00	2025-12-28 12:29:24.696182+00	active	\N	0.90	\N	tem cunhada chamada jeniffer
46314194-aeb3-4a60-ae8c-ad7acb45c5a1	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Filho da cunhada se chama Thomas	Mencionado pelo nome	8	2	2025-12-28 12:29:24.699381+00	c104e48d-10e1-43d2-8166-d1de7d6fdcde	2025-12-28 11:57:29.153129+00	t	f	2025-12-28 11:57:29.153129+00	2025-12-28 12:29:24.699381+00	active	\N	0.90	\N	filho da cunhada se chama thomas
9118e5e1-8aa9-41b2-89f5-f2ed39b147df	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Cunhada se chama Jeniffer	Mencionado na conversa	7	2	2025-12-28 12:30:04.37221+00	c104e48d-10e1-43d2-8166-d1de7d6fdcde	2025-12-28 11:57:29.148312+00	t	f	2025-12-28 11:57:29.148312+00	2025-12-28 12:30:04.37221+00	active	\N	0.90	\N	cunhada se chama jeniffer
351a2c84-7b0d-478e-bc72-f72b074e2100	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Tem 4 irmãos	Informação sobre total de irmãos na família	7	3	2025-12-28 12:30:04.365984+00	c104e48d-10e1-43d2-8166-d1de7d6fdcde	2025-12-28 11:59:41.69422+00	f	f	2025-12-28 11:59:41.69422+00	2025-12-28 12:33:53.01489+00	superseded	\N	0.90	\N	tem 4 irmaos
411a5ca4-b03b-4c46-b892-40db27f7a0dd	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Paola tem 2 irmãos: Max e Juliana	\N	8	1	2025-12-28 12:34:01.568866+00	\N	2025-12-28 12:34:01.568866+00	t	f	2025-12-28 12:34:01.568866+00	2025-12-28 12:34:01.568866+00	active	\N	0.80	\N	paola tem 2 irmaos max e juliana
158df264-24f1-4e3f-972d-febde21417ca	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Junior (marido) tem 3 irmãos: Juliana, Fabrício e Jeniffer	\N	8	1	2025-12-28 12:34:01.568866+00	\N	2025-12-28 12:34:01.568866+00	t	f	2025-12-28 12:34:01.568866+00	2025-12-28 12:34:01.568866+00	active	\N	0.80	\N	junior marido tem 3 irmaos juliana fabricio e jeniffer
6933b226-377a-4235-a9bf-bbbc2c0d0f97	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Irmãos do Junior moram no Brasil	\N	8	1	2025-12-28 12:34:01.568866+00	\N	2025-12-28 12:34:01.568866+00	t	f	2025-12-28 12:34:01.568866+00	2025-12-28 12:34:01.568866+00	active	\N	0.80	\N	irmaos do junior moram no brasil
644457bf-8640-4e4b-8cc1-f52d81f05166	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Marido da Jeniffer (cunhada de Paola) se chama Maxwell	Apelido familiar: Max	8	3	2025-12-28 12:30:04.374756+00	c104e48d-10e1-43d2-8166-d1de7d6fdcde	2025-12-28 11:57:29.151211+00	t	f	2025-12-28 11:57:29.151211+00	2025-12-28 12:34:13.773921+00	active	\N	0.90	\N	marido da jeniffer cunhada de paola se chama maxwell
84a4c724-16dd-4f4a-9e89-ecc41cbc4cd6	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Junior tem 3 irmãos: Juliana, Fabrício e Jeniffer	\N	9	1	2025-12-28 12:35:21.735942+00	3896d238-2741-4b20-8aae-3517b48ca864	2025-12-28 12:35:21.735942+00	t	f	2025-12-28 12:35:21.735942+00	2025-12-28 12:35:21.735942+00	active	\N	1.00	\N	junior tem 3 irmaos juliana fabricio e jeniffer
338ceedc-7e5d-4f66-8bef-1f7672de246c	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Jeniffer (irmã de Junior) é casada com Maxwell	\N	8	1	2025-12-28 12:35:21.746306+00	3896d238-2741-4b20-8aae-3517b48ca864	2025-12-28 12:35:21.746306+00	f	f	2025-12-28 12:35:21.746306+00	2025-12-28 12:36:41.706916+00	superseded	\N	0.95	\N	jeniffer irma de junior e casada com maxwell
6e00d617-5ce2-4d14-9e44-f487e9bb13ae	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Passou natal e ano novo com os pais do Junior	Os pais do Junior estão visitando	6	2	2025-12-28 12:36:41.716062+00	c104e48d-10e1-43d2-8166-d1de7d6fdcde	2025-12-28 11:54:43.949186+00	t	f	2025-12-28 11:54:43.949186+00	2025-12-28 12:36:41.716062+00	active	\N	0.90	\N	passou natal e ano novo com os pais do junior
f02e7e40-7db4-4335-b3ca-6cee6404f91f	aac61923-7730-4691-895f-8d14aaf2d473	IDENTIDADE	Mora na Florida, EUA há mais de 10 anos	\N	10	1	2025-12-28 12:28:06.09121+00	aab6c277-a5c6-43a1-8ea4-ea713b561482	2025-12-28 12:28:06.09121+00	f	f	2025-12-28 12:28:06.09121+00	2025-12-28 12:52:54.996947+00	superseded	\N	0.95	\N	mora na florida eua ha mais de 10 anos
90baafe3-d4b5-4268-bbbb-814f2f613e3e	aac61923-7730-4691-895f-8d14aaf2d473	IDENTIDADE	Questiona localização atual na Florida, EUA	\N	8	1	2025-12-28 12:52:55.004846+00	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	2025-12-28 12:52:55.004846+00	t	f	2025-12-28 12:52:55.004846+00	2025-12-28 12:52:55.004846+00	active	\N	0.70	\N	questiona localizacao atual na florida eua
4e558924-7bc8-49fa-b59d-4595b375c7a8	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Tem cunhada chamada Jeniffer que é casada com Maxwell	\N	6	1	2025-12-28 12:36:41.709114+00	3896d238-2741-4b20-8aae-3517b48ca864	2025-12-28 12:36:41.709114+00	f	f	2025-12-28 12:36:41.709114+00	2025-12-28 12:52:55.021164+00	superseded	\N	0.90	\N	tem cunhada chamada jeniffer que e casada com maxwell
a9fbf317-5580-44e0-9d95-cc0cf1821afb	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Jeniffer tem um filho chamado Thomas	\N	8	3	2025-12-28 12:52:55.025702+00	3896d238-2741-4b20-8aae-3517b48ca864	2025-12-28 12:35:21.748874+00	t	f	2025-12-28 12:35:21.748874+00	2025-12-28 12:52:55.025702+00	active	\N	0.95	\N	jeniffer tem um filho chamado thomas
46ee7852-7fd3-453e-8c50-b582af612e39	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Vive experimentando medo constante	Relato sugere ansiedade ou estado emocional instável	8	5	2025-12-28 17:50:43.279181+00	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	2025-12-28 11:42:53.353116+00	t	f	2025-12-28 11:42:53.353116+00	2025-12-28 17:50:43.279181+00	active	\N	0.90	\N	vive experimentando medo constante
adc9174c-f829-41c4-abda-f86bec436dc6	aac61923-7730-4691-895f-8d14aaf2d473	CONTEXTO	Está em um momento de recomeço e transição na vida	Reconhece que recomeçar é desafiador	8	3	2025-12-28 17:50:43.281937+00	8e708c2e-b928-42a9-81dc-8a9c55f2bb58	2025-12-28 11:46:29.621243+00	t	f	2025-12-28 11:46:29.621243+00	2025-12-28 17:50:43.281937+00	active	\N	0.80	\N	esta em um momento de recomeco e transicao na vida
54a8fa06-d8cb-483d-bfc0-d624af922b97	aac61923-7730-4691-895f-8d14aaf2d473	CONTEXTO	Está considerando migrar para o Canadá	Reconhece que a mudança não será simples	6	7	2025-12-28 17:53:35.096496+00	f5c34cf4-be95-46a8-b1bd-3f6dbbb5fc03	2025-12-28 11:44:43.889141+00	t	f	2025-12-28 11:44:43.889141+00	2025-12-28 17:53:35.096496+00	active	\N	0.90	\N	esta considerando migrar para o canada
39974151-4052-425d-91fb-63379096f6c9	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Tem cunhada chamada Jeniffer casada com Maxwell	\N	6	2	2025-12-28 17:53:35.101875+00	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	2025-12-28 12:52:55.02317+00	t	f	2025-12-28 12:52:55.02317+00	2025-12-28 17:53:35.101875+00	active	\N	0.95	\N	tem cunhada chamada jeniffer casada com maxwell
7898f279-2eff-4295-8865-0c46e75b7e3a	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Passou Natal e Ano Novo com os pais do marido	\N	5	2	2025-12-28 17:53:35.103847+00	ca6ce426-c18c-4dbf-8cc3-1b2267fd0a1c	2025-12-28 12:52:55.018323+00	t	f	2025-12-28 12:52:55.018323+00	2025-12-28 17:53:35.103847+00	active	\N	0.90	\N	passou natal e ano novo com os pais do marido
214351d6-506c-4dcf-b979-bbd801a09b40	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Vive com ansiedade constante, medo e pensamento acelerado	Experimenta cansaço no corpo e sensação de instabilidade	9	1	2025-12-28 17:54:24.849522+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:54:24.849522+00	t	f	2025-12-28 17:54:24.849522+00	2025-12-28 17:54:24.849522+00	active	\N	0.95	\N	vive com ansiedade constante medo e pensamento acelerado
62cebacc-2376-4b36-81a4-981d72c363bc	aac61923-7730-4691-895f-8d14aaf2d473	CONTEXTO	Está em momento de transição e recomeço na vida	Considerando migração para o Canadá	7	3	2025-12-28 17:54:24.852597+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:52:53.526062+00	t	f	2025-12-28 17:52:53.526062+00	2025-12-28 17:54:24.852597+00	active	\N	0.90	\N	esta em momento de transicao e recomeco na vida
4a9e915e-3373-4fcc-8722-69565fb2c194	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Vive nos Estados Unidos há 10 anos	\N	9	1	2025-12-28 14:42:57.178937+00	\N	2025-12-28 14:42:57.178937+00	f	f	2025-12-28 14:42:57.178937+00	2025-12-28 15:45:30.827711+00	superseded	\N	0.95	\N	vive nos estados unidos ha 10 anos
9d2c8d35-f438-4cee-a43e-5a68c4022aba	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Paga impostos e tenta fazer tudo corretamente	\N	8	1	2025-12-28 14:42:57.196363+00	\N	2025-12-28 14:42:57.196363+00	t	f	2025-12-28 14:42:57.196363+00	2025-12-28 15:45:30.827711+00	active	\N	0.85	\N	paga impostos e tenta fazer tudo corretamente
229dfaa5-83eb-4a86-b676-c8b234f863a8	c980af15-468d-4433-9515-c4528ef452f5	IDENTIDADE	Situação migratória irregular nos EUA por passar período de permanência	\N	10	1	2025-12-28 14:42:57.193821+00	\N	2025-12-28 14:42:57.193821+00	f	f	2025-12-28 14:42:57.193821+00	2025-12-28 15:45:30.827711+00	superseded	\N	0.90	\N	situacao migratoria irregular nos eua por passar periodo de permanencia
86532b59-b9f8-4966-86c3-2ded9e184974	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Preocupado com política de imigração nos EUA	\N	7	1	2025-12-28 14:42:57.200708+00	\N	2025-12-28 14:42:57.200708+00	f	f	2025-12-28 14:42:57.200708+00	2025-12-28 15:45:30.827711+00	superseded	\N	0.80	\N	preocupado com politica de imigracao nos eua
14f521e1-8558-409f-9556-56f08e1a09b5	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Busca regularização migratória de forma legal	Tenta resolver situação através de meios jurídicos	9	1	2025-12-28 14:46:10.566064+00	\N	2025-12-28 14:46:10.566064+00	t	f	2025-12-28 14:46:10.566064+00	2025-12-28 15:45:30.827711+00	active	\N	0.95	\N	busca regularizacao migratoria de forma legal
d5abf82b-4fbe-4950-8ca9-a883d221abb0	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Está experimentando ansiedade constante, medo e pensamento acelerado	Busca melhorar além da terapia	10	1	2025-12-28 17:54:58.08524+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:54:58.08524+00	t	f	2025-12-28 17:54:58.08524+00	2025-12-28 17:54:58.08524+00	active	\N	0.95	\N	esta experimentando ansiedade constante medo e pensamento acelerado
8cb2ec23-3869-467b-b5c2-d60322090d1d	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Está experimentando ansiedade	Mencionou estar se sentindo ansioso	8	1	2025-12-28 17:50:43.268731+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:50:43.268731+00	t	f	2025-12-28 17:50:43.268731+00	2025-12-28 17:50:43.268731+00	active	\N	0.90	\N	esta experimentando ansiedade
4c70384a-c135-4fa1-bf57-8aeb3433642b	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Vive com ansiedade constante	\N	8	1	2025-12-28 17:52:53.523192+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:52:53.523192+00	t	f	2025-12-28 17:52:53.523192+00	2025-12-28 17:52:53.523192+00	active	\N	0.90	\N	vive com ansiedade constante
cf2406ad-0293-4c32-a87e-1f55fee5c910	aac61923-7730-4691-895f-8d14aaf2d473	CONTEXTO	Está em momento de transição e recomeço na vida, considerando migrar para o Canadá	\N	7	2	2025-12-28 17:54:58.089286+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:53:54.777826+00	t	f	2025-12-28 17:53:54.777826+00	2025-12-28 17:54:58.089286+00	active	\N	0.90	\N	esta em momento de transicao e recomeco na vida considerando migrar para o canada
0ffdf39b-5816-448f-aa5d-bd8534eb65a9	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Tem esposo chamado Junior, que tem 3 irmãos: Juliana, Fabrício e Jeniffer	\N	7	1	2025-12-28 17:54:58.092557+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:54:58.092557+00	t	f	2025-12-28 17:54:58.092557+00	2025-12-28 17:54:58.092557+00	active	\N	0.90	\N	tem esposo chamado junior que tem 3 irmaos juliana fabricio e jeniffer
55efd9cc-cd8f-4d4e-8b2e-b8c525fafa58	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Vive com ansiedade constante e cansaço no corpo	\N	8	1	2025-12-28 17:53:35.088768+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:53:35.088768+00	t	f	2025-12-28 17:53:35.088768+00	2025-12-28 17:53:35.088768+00	active	\N	0.90	\N	vive com ansiedade constante e cansaco no corpo
458259cb-c5a0-489a-b194-4f4ca2c36af7	aac61923-7730-4691-895f-8d14aaf2d473	FE	Vai ao culto às 6pm para adorar a Deus	\N	6	3	2025-12-28 17:53:35.098087+00	cad6bcf7-901e-42b4-a5ea-aafe4f673196	2025-12-28 16:32:14.093475+00	t	f	2025-12-28 16:32:14.093475+00	2025-12-28 17:53:35.098087+00	active	\N	0.80	\N	vai ao culto as 6pm para adorar a deus
ece76f7b-7a1d-485a-a8af-54f9ff2f4b7e	aac61923-7730-4691-895f-8d14aaf2d473	IDENTIDADE	Questiona sua localização atual	\N	7	1	2025-12-28 17:53:35.10612+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:53:35.10612+00	t	f	2025-12-28 17:53:35.10612+00	2025-12-28 17:53:35.10612+00	active	\N	0.60	\N	questiona sua localizacao atual
d4cb9238-6c0b-466c-b66c-a24be8861756	aac61923-7730-4691-895f-8d14aaf2d473	LUTA	Vive com pensamento acelerado, experimentando ansiedade e medo constante	\N	8	1	2025-12-28 17:53:54.771991+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:53:54.771991+00	t	f	2025-12-28 17:53:54.771991+00	2025-12-28 17:53:54.771991+00	active	\N	0.90	\N	vive com pensamento acelerado experimentando ansiedade e medo constante
e19d50cc-dcb8-4f16-bc08-255480bae620	aac61923-7730-4691-895f-8d14aaf2d473	IDENTIDADE	Localização atual incerta, questionando onde está atualmente	\N	9	1	2025-12-28 17:53:54.779557+00	3b48bb25-c428-42b8-9d26-fa17a550f210	2025-12-28 17:53:54.779557+00	t	f	2025-12-28 17:53:54.779557+00	2025-12-28 17:53:54.779557+00	active	\N	0.70	\N	localizacao atual incerta questionando onde esta atualmente
bdf56c77-df43-4275-ae34-2e7ae7e1f028	aac61923-7730-4691-895f-8d14aaf2d473	FAMILIA	Pais moram em Recife, Brasil	\N	9	3	2025-12-28 17:54:58.094766+00	aab6c277-a5c6-43a1-8ea4-ea713b561482	2025-12-28 12:28:31.689192+00	t	f	2025-12-28 12:28:31.689192+00	2025-12-28 17:54:58.094766+00	active	\N	0.95	\N	pais moram em recife brasil
bdc6711a-50b7-4b2b-95a5-b2e09133a0cd	5dcfcba8-4b12-4344-af8e-e734c68d195a	LUTA	Está passando por um momento de ansiedade	\N	7	1	2025-12-28 18:02:31.583316+00	896a45d9-9fb3-4f58-9eaa-714b34a25235	2025-12-28 18:02:31.583316+00	t	f	2025-12-28 18:02:31.583316+00	2025-12-28 18:02:31.583316+00	active	\N	0.80	\N	esta passando por um momento de ansiedade
2d2fb85c-3d36-41b3-9ad4-cc35fc25e387	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Está experimentando ansiedade	Menção direta de ansiedade, necessita atenção emocional	8	1	2025-12-28 18:16:07.727246+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:16:07.727246+00	t	f	2025-12-28 18:16:07.727246+00	2025-12-28 18:16:07.727246+00	active	\N	0.70	\N	esta experimentando ansiedade
e039addd-dc4c-4370-91eb-c33a143ec3c2	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Experimenta ansiedade relacionada à maternidade	Preocupações e medos sobre ser mãe	8	1	2025-12-28 18:16:49.602612+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:16:49.602612+00	t	f	2025-12-28 18:16:49.602612+00	2025-12-28 18:16:49.602612+00	active	\N	0.90	\N	experimenta ansiedade relacionada a maternidade
81a2328e-9caf-46f3-877c-2aa3c1609b84	5dcfcba8-4b12-4344-af8e-e734c68d195a	VITORIA	Está vivendo coisas que sempre sonhou	Expressão de gratidão e realização pessoal	8	1	2025-12-28 18:17:03.206992+00	ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb	2025-12-28 18:17:03.206992+00	t	f	2025-12-28 18:17:03.206992+00	2025-12-28 18:17:03.206992+00	active	\N	0.80	\N	esta vivendo coisas que sempre sonhou
a008d195-d9bd-4bff-aff4-0a4fb102eb88	5dcfcba8-4b12-4344-af8e-e734c68d195a	LUTA	Continua passando por momento de ansiedade	\N	7	1	2025-12-28 18:17:03.214102+00	ea418f92-b3f1-4c8b-b4e2-fd0e171bbccb	2025-12-28 18:17:03.214102+00	t	f	2025-12-28 18:17:03.214102+00	2025-12-28 18:17:03.214102+00	active	\N	0.90	\N	continua passando por momento de ansiedade
05829eea-491c-421b-aed9-51be31832bde	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Passou por perda gestacional com 2 meses de gravidez	Gestação ectópica que resultou em cirurgia de emergência	10	1	2025-12-28 18:18:01.580568+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:18:01.580568+00	t	f	2025-12-28 18:18:01.580568+00	2025-12-28 18:18:01.580568+00	active	\N	1.00	\N	passou por perda gestacional com 2 meses de gravidez
e2090475-2bc5-4eee-a830-ad0ba5c9ac4d	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Passou por cirurgia de emergência devido a complicações na gravidez	Rompimento de trompa durante gestação ectópica	10	1	2025-12-28 18:18:01.59373+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:18:01.59373+00	t	f	2025-12-28 18:18:01.59373+00	2025-12-28 18:18:01.59373+00	active	\N	1.00	\N	passou por cirurgia de emergencia devido a complicacoes na gravidez
63bfda68-9680-4282-8dd9-9eb525e3cc94	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Casal está tentando engravidar após experiência anterior de perda gestacional	Menciona dor emocional profunda relacionada à perda	10	1	2025-12-28 18:19:35.933626+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:19:35.933626+00	t	f	2025-12-28 18:19:35.933626+00	2025-12-28 18:19:35.933626+00	active	\N	0.95	\N	casal esta tentando engravidar apos experiencia anterior de perda gestacional
99a16feb-f748-4ee5-932e-5acaa68214cd	1e868db6-0ae4-46dd-a068-c22f60f5d489	FAMILIA	Casada e desejando ter filhos	\N	9	1	2025-12-28 18:19:35.941186+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:19:35.941186+00	f	f	2025-12-28 18:19:35.941186+00	2025-12-28 18:22:03.228676+00	superseded	\N	0.90	\N	casada e desejando ter filhos
5646681e-00a8-42c5-aa66-755866be6c0f	1e868db6-0ae4-46dd-a068-c22f60f5d489	FAMILIA	Casada com Erick, seu marido é paciente e calmo	Marido é uma fonte de apoio emocional	9	1	2025-12-28 18:22:03.234728+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:22:03.234728+00	t	f	2025-12-28 18:22:03.234728+00	2025-12-28 18:22:03.234728+00	active	\N	0.95	\N	casada com erick seu marido e paciente e calmo
f2bf435e-8abe-4e34-b70c-d03820eb9450	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Experimenta ansiedade mensal relacionada ao ciclo menstrual	Sente frustração a cada ciclo menstrual	8	1	2025-12-28 18:22:03.237593+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:22:03.237593+00	t	f	2025-12-28 18:22:03.237593+00	2025-12-28 18:22:03.237593+00	active	\N	0.90	\N	experimenta ansiedade mensal relacionada ao ciclo menstrual
02e27e30-eb61-47a1-a39c-28d703e71a64	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Casal está tentando engravidar após perda gestacional prévia	Passou por perda gestacional com 2 meses de gravidez	10	1	2025-12-28 18:22:03.23961+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:22:03.23961+00	t	f	2025-12-28 18:22:03.23961+00	2025-12-28 18:22:03.23961+00	active	\N	0.95	\N	casal esta tentando engravidar apos perda gestacional previa
fcc42431-6e00-48a9-9ae5-e0564ef7090c	1e868db6-0ae4-46dd-a068-c22f60f5d489	FAMILIA	Deseja muito ter filhos	\N	9	1	2025-12-28 18:22:03.241426+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:22:03.241426+00	t	f	2025-12-28 18:22:03.241426+00	2025-12-28 18:22:03.241426+00	active	\N	0.90	\N	deseja muito ter filhos
4855eb02-0f80-4fee-9149-4ea0123f3f50	1e868db6-0ae4-46dd-a068-c22f60f5d489	LUTA	Sofreu cirurgia de emergência devido a complicações na gravidez	\N	10	1	2025-12-28 18:22:03.242971+00	e9a5dde9-1c00-418a-9e78-b9625da95bad	2025-12-28 18:22:03.242971+00	t	f	2025-12-28 18:22:03.242971+00	2025-12-28 18:22:03.242971+00	active	\N	0.95	\N	sofreu cirurgia de emergencia devido a complicacoes na gravidez
076fe9f2-a3b8-4cbe-9cce-7b0f21a79032	c980af15-468d-4433-9515-c4528ef452f5	LUTA	Está passando por momento de cansaço emocional	Relata necessidade de forças para continuar	8	1	2025-12-28 18:24:43.855151+00	cd8769e5-569e-4adf-8635-5103d0541172	2025-12-28 18:24:43.855151+00	t	f	2025-12-28 18:24:43.855151+00	2025-12-28 18:24:43.855151+00	active	\N	0.90	\N	esta passando por momento de cansaco emocional
f079b2d9-3348-4218-8db7-569b9ac10882	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Enfrenta desafios emocionais durante processo migratório	Busca regularização legal nos EUA com perseverança	9	1	2025-12-28 18:24:43.859636+00	cd8769e5-569e-4adf-8635-5103d0541172	2025-12-28 18:24:43.859636+00	t	f	2025-12-28 18:24:43.859636+00	2025-12-28 18:24:43.859636+00	active	\N	0.95	\N	enfrenta desafios emocionais durante processo migratorio
e244748f-a2e8-471a-9ed3-2be830102865	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Está em situação migratória pendente nos EUA	Consultou advogados e aguarda possível anistia ou ordem executiva	10	1	2025-12-28 14:46:10.56286+00	\N	2025-12-28 14:46:10.56286+00	f	f	2025-12-28 14:46:10.56286+00	2025-12-28 18:30:22.422336+00	superseded	\N	0.90	\N	esta em situacao migratoria pendente nos eua
78acf81b-de9a-485b-8336-877d65b47c5d	c980af15-468d-4433-9515-c4528ef452f5	LUTA	Enfrenta desafio emocional durante processo migratório	Momento atual de cansaço emocional	8	1	2025-12-28 18:30:22.431633+00	cd8769e5-569e-4adf-8635-5103d0541172	2025-12-28 18:30:22.431633+00	t	f	2025-12-28 18:30:22.431633+00	2025-12-28 18:30:22.431633+00	active	\N	0.85	\N	enfrenta desafio emocional durante processo migratorio
031725c8-8bf2-4d37-ba6e-98de8d67eb50	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Está nos EUA em processo de regularização migratória	Busca fazer processo migratório de forma legal e correta	10	2	2025-12-28 18:32:17.699076+00	cd8769e5-569e-4adf-8635-5103d0541172	2025-12-28 18:30:22.428606+00	t	f	2025-12-28 18:30:22.428606+00	2025-12-28 18:32:17.699076+00	active	\N	0.90	\N	esta nos eua em processo de regularizacao migratoria
b1c5d0eb-1f68-4b17-ab29-54458d503dc5	c980af15-468d-4433-9515-c4528ef452f5	LUTA	Enfrenta desafios emocionais durante processo migratório	\N	8	1	2025-12-28 18:32:17.706456+00	cd8769e5-569e-4adf-8635-5103d0541172	2025-12-28 18:32:17.706456+00	t	f	2025-12-28 18:32:17.706456+00	2025-12-28 18:32:17.706456+00	active	\N	0.85	\N	enfrenta desafios emocionais durante processo migratorio
70cbfbff-6784-42a0-b60c-c7cc2fd6ca2c	c980af15-468d-4433-9515-c4528ef452f5	CONTEXTO	Paga impostos durante processo migratório	\N	7	2	2025-12-28 18:32:17.709508+00	cd8769e5-569e-4adf-8635-5103d0541172	2025-12-28 18:30:22.433589+00	t	f	2025-12-28 18:30:22.433589+00	2025-12-28 18:32:17.709508+00	active	\N	0.90	\N	paga impostos durante processo migratorio
9e967fa5-db12-4846-bb0e-370b9600ab7c	dbb82c3b-715c-49f7-a33f-5df195a24591	LUTA	Sente confusão e conflito interno sobre doutrinas teológicas de Arminianismo e Calvinismo	Discussões teológicas estão causando angústia espiritual	7	1	2025-12-28 19:02:32.697777+00	d31b4835-552e-401e-9f72-34649d4c25a1	2025-12-28 19:02:32.697777+00	t	f	2025-12-28 19:02:32.697777+00	2025-12-28 19:02:32.697777+00	active	\N	0.90	\N	sente confusao e conflito interno sobre doutrinas teologicas de arminianismo e calvinismo
b9682c5e-1f4d-4dab-9417-ac42a8afffff	dbb82c3b-715c-49f7-a33f-5df195a24591	FE	Está experimentando dúvidas que afetam sua compreensão da fé	A disputa teológica está gerando desconforto espiritual	8	1	2025-12-28 19:02:32.705908+00	d31b4835-552e-401e-9f72-34649d4c25a1	2025-12-28 19:02:32.705908+00	t	f	2025-12-28 19:02:32.705908+00	2025-12-28 19:02:32.705908+00	active	\N	0.85	\N	esta experimentando duvidas que afetam sua compreensao da fe
81134310-bae8-4b90-8ff6-42b7df9f3312	dbb82c3b-715c-49f7-a33f-5df195a24591	LUTA	Está experimentando dúvidas teológicas que afetam sua fé	Conflito interno sobre Arminianismo e Calvinismo	8	1	2025-12-28 19:07:56.446019+00	d31b4835-552e-401e-9f72-34649d4c25a1	2025-12-28 19:07:56.446019+00	t	f	2025-12-28 19:07:56.446019+00	2025-12-28 19:07:56.446019+00	active	\N	0.90	\N	esta experimentando duvidas teologicas que afetam sua fe
\.


--
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_profiles (id, user_id, nome, apelido, idade, genero, estado_civil, filhos, profissao, cidade, denominacao, tempo_de_fe, batizado, data_batismo, igreja_local, cargo_igreja, tom_preferido, profundidade, usa_emoji, horario_ativo, lutas_encrypted, notas_pastorais_encrypted, created_at, updated_at) FROM stdin;
c193db7e-4781-44f7-87cb-6a9e738a55e5	c980af15-468d-4433-9515-c4528ef452f5	Luiz	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	equilibrado	moderada	t	\N	\N	\N	2025-12-27 21:48:13.299867+00	2025-12-27 21:48:13.299867+00
64b75df9-af54-44f7-9573-de5ef9afbef1	aac61923-7730-4691-895f-8d14aaf2d473	Paola	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	equilibrado	moderada	t	\N	\N	\N	2025-12-27 23:32:18.971563+00	2025-12-27 23:32:18.971563+00
baa278f3-8e64-410b-bdab-d819b6f2acfb	dbb82c3b-715c-49f7-a33f-5df195a24591	Manuela	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	equilibrado	moderada	t	\N	\N	\N	2025-12-28 13:18:19.771386+00	2025-12-28 13:18:19.771386+00
b8e9bd56-c1b7-4d94-9d07-6d112273a6d0	5dcfcba8-4b12-4344-af8e-e734c68d195a	Jeniffer 	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	equilibrado	moderada	t	\N	\N	\N	2025-12-28 18:02:19.544715+00	2025-12-28 18:02:19.544715+00
4eae6ddf-98ee-4da3-899e-90d26fef4988	1e868db6-0ae4-46dd-a068-c22f60f5d489	Júlia	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	equilibrado	moderada	t	\N	\N	\N	2025-12-28 18:02:44.839509+00	2025-12-28 18:02:44.839509+00
059370f9-de3e-42a6-94c9-440cf32bc5ff	94a61709-616f-4999-b4c2-69116dea8dce	Izilda Santos Silva	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	equilibrado	moderada	t	\N	\N	\N	2025-12-28 18:05:05.777624+00	2025-12-28 18:05:05.777624+00
ce61079d-838b-4b55-98db-2bba82314d93	193c910b-629c-4bdd-8302-8baf50a73e33	Maxwell	\N	\N	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	equilibrado	moderada	t	\N	\N	\N	2025-12-28 18:19:45.116271+00	2025-12-28 18:19:45.116271+00
\.


--
-- Data for Name: user_psychological_profile; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_psychological_profile (id, user_id, communication_style, primary_needs, thinking_patterns, emotional_triggers, coping_mechanisms, faith_stage, love_language, temperament, emotional_openness, self_awareness, resilience_level, baseline_anxiety, attachment_style, accumulated_insights, recommended_approach, last_analysis_at, analysis_count, confidence_score, created_at, updated_at) FROM stdin;
7726ecbb-6639-4bd2-9b96-bab80e478e67	c980af15-468d-4433-9515-c4528ef452f5	emotional	{validação,orientação,oração}	{"black_white": 0.7, "mind_reading": 0.4, "catastrophizing": 0.8, "should_statements": 0.5, "overgeneralization": 0.6, "emotional_reasoning": 0.5}	{dúvida,culpa,inadequação}	{autorreflexão,confissão}	convencional	palavras	melancólico	6	5	4	8	ansioso	Indivíduo experimenta forte ansiedade espiritual, com tendência a duvidar de sua salvação e sentir-se profundamente imperfeito.	Oferecer segurança da graça divina, trabalhar na autoaceitação e desenvolvimento de estratégias para quebrar padrões de mentira.	2025-12-28 12:46:54.292004	0	0.50	2025-12-28 12:46:54.292004	2025-12-28 12:46:54.292004
d708811a-8d1d-49d5-948c-f88f69e39a48	aac61923-7730-4691-895f-8d14aaf2d473	concise	{validação,escuta}	{"black_white": 0.3, "mind_reading": 0.2, "catastrophizing": 0.4, "should_statements": 0.3, "overgeneralization": 0.5, "emotional_reasoning": 0.4}	{confusão,mal-entendido}	{correção,esclarecimento}	convencional	palavras	colérico	6	5	6	7	ansioso	Pessoa com alta necessidade de precisão e controle da narrativa. Reage rapidamente a percepções de erro ou mal-entendido. Demonstra complexidade familiar e emocional na comunicação.	Oferecer espaço para clarificação, validar sentimentos de frustração, escutar atentamente antes de responder.	2025-12-28 12:47:22.912397	0	0.50	2025-12-28 12:47:22.912397	2025-12-28 12:47:22.912397
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, password_hash, created_at, updated_at, last_login, is_active, is_premium, premium_until, trial_messages_used, total_messages, oauth_provider, oauth_id, stripe_customer_id, stripe_subscription_id, subscription_status, subscription_start_date, subscription_end_date, cancel_at_period_end, accepted_terms, accepted_terms_at, accepted_privacy, accepted_privacy_at, terms_version) FROM stdin;
193c910b-629c-4bdd-8302-8baf50a73e33	maxwell.ciriaco1991@gmail.com	$2b$12$MKfi0KBcyh5cofBRpeL6tu3Zw/b8W5SrbyCX9QE6HxTQwCwsR46Vy	2025-12-28 18:19:45.110461+00	2025-12-28 18:31:23.397568+00	2025-12-28 18:19:45.478616+00	t	f	\N	2	2	\N	\N	\N	\N	\N	\N	\N	f	t	2025-12-28 18:19:45.110461+00	t	2025-12-28 18:19:45.110461+00	1.0
5dcfcba8-4b12-4344-af8e-e734c68d195a	jhennysama@icloud.com	$2b$12$VG136gy2V5uYXiaRAL4LmuD9UhbCAcLzFMRFqJ8w70D7cQHkEK1py	2025-12-28 18:02:19.538769+00	2025-12-28 18:17:03.215844+00	2025-12-28 18:02:19.943976+00	t	f	\N	8	8	\N	\N	\N	\N	\N	\N	\N	f	t	2025-12-28 18:02:19.538769+00	t	2025-12-28 18:02:19.538769+00	1.0
aac61923-7730-4691-895f-8d14aaf2d473	paolapmf12@gmail.com	$2b$12$w9rvvWK8lrOPkRRopS521.5X7RpUvRy0qO5LZhJD2z7cMhby3RFne	2025-12-27 23:32:18.965685+00	2025-12-28 17:54:53.4084+00	2025-12-28 17:47:08.119871+00	t	t	2026-01-27 11:46:02.281907+00	64	64	\N	\N	\N	\N	\N	\N	\N	f	t	2025-12-27 23:32:18.965685+00	t	2025-12-27 23:32:18.965685+00	1.0
94a61709-616f-4999-b4c2-69116dea8dce	pra.izilda@homail.com	$2b$12$Lrnc5qSes375Dz9l/nVI3.u0J7ji653wWyAkyD.H7FqEEeTF423ry	2025-12-28 18:05:05.774754+00	2025-12-28 19:05:23.000246+00	2025-12-28 18:05:06.135607+00	t	f	\N	4	4	\N	\N	\N	\N	\N	\N	\N	f	t	2025-12-28 18:05:05.774754+00	t	2025-12-28 18:05:05.774754+00	1.0
dbb82c3b-715c-49f7-a33f-5df195a24591	manuelafs12@gmail.com	$2b$12$JQGpDKq.hO1bl9YLDZskq.yo3AMx7mXR067fLpA38vOA1lRNwCW/i	2025-12-28 13:18:19.763452+00	2025-12-28 19:07:56.452071+00	2025-12-28 18:51:58.722283+00	t	f	\N	6	6	\N	\N	\N	\N	\N	\N	\N	f	t	2025-12-28 13:18:19.763452+00	t	2025-12-28 13:18:19.763452+00	1.0
1e868db6-0ae4-46dd-a068-c22f60f5d489	jullycat11@hotmail.com	$2b$12$421WgnCSxr/lWfMEbIzXs.xdD/LQxUk9kSNOH7le.QRPoxtSy74My	2025-12-28 18:02:44.832466+00	2025-12-28 18:22:09.036197+00	2025-12-28 18:02:45.357521+00	t	f	\N	12	12	\N	\N	\N	\N	\N	\N	\N	f	t	2025-12-28 18:02:44.832466+00	t	2025-12-28 18:02:44.832466+00	1.0
c980af15-468d-4433-9515-c4528ef452f5	luizjuniorbjj@gmail.com	$2b$12$WhCBhKiLi.uruuR8XzHR9e46VVs9ZSMiz3jhliGM.CHUWSu//oVNe	2025-12-27 21:48:13.289794+00	2025-12-28 19:43:21.034543+00	2025-12-28 19:43:17.102588+00	t	t	\N	0	21	\N	\N	\N	\N	beta_active	2025-12-28 19:43:21.034543+00	\N	f	t	2025-12-27 21:48:13.289794+00	t	2025-12-27 21:48:13.289794+00	1.0
\.


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: devotionals devotionals_data_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devotionals
    ADD CONSTRAINT devotionals_data_key UNIQUE (data);


--
-- Name: devotionals devotionals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devotionals
    ADD CONSTRAINT devotionals_pkey PRIMARY KEY (id);


--
-- Name: message_feedback message_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_feedback
    ADD CONSTRAINT message_feedback_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: prayer_requests prayer_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prayer_requests
    ADD CONSTRAINT prayer_requests_pkey PRIMARY KEY (id);


--
-- Name: saved_content saved_content_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_content
    ADD CONSTRAINT saved_content_pkey PRIMARY KEY (id);


--
-- Name: user_devotional_interactions user_devotional_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devotional_interactions
    ADD CONSTRAINT user_devotional_interactions_pkey PRIMARY KEY (id);


--
-- Name: user_devotional_interactions user_devotional_interactions_user_id_devotional_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devotional_interactions
    ADD CONSTRAINT user_devotional_interactions_user_id_devotional_id_key UNIQUE (user_id, devotional_id);


--
-- Name: user_insights user_insights_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_insights
    ADD CONSTRAINT user_insights_pkey PRIMARY KEY (id);


--
-- Name: user_memories user_memories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_memories
    ADD CONSTRAINT user_memories_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_key UNIQUE (user_id);


--
-- Name: user_psychological_profile user_psychological_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_psychological_profile
    ADD CONSTRAINT user_psychological_profile_pkey PRIMARY KEY (id);


--
-- Name: user_psychological_profile user_psychological_profile_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_psychological_profile
    ADD CONSTRAINT user_psychological_profile_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_log_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_log_created ON public.audit_log USING btree (created_at DESC);


--
-- Name: idx_audit_log_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_log_user ON public.audit_log USING btree (user_id);


--
-- Name: idx_conversations_last_message; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_last_message ON public.conversations USING btree (last_message_at DESC);


--
-- Name: idx_conversations_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_user ON public.conversations USING btree (user_id);


--
-- Name: idx_memories_fato_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_memories_fato_search ON public.user_memories USING gin (to_tsvector('portuguese'::regconfig, fato));


--
-- Name: idx_memories_user_status_imp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_memories_user_status_imp ON public.user_memories USING btree (user_id, status, importancia DESC, ultima_mencao DESC);


--
-- Name: idx_messages_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_conversation ON public.messages USING btree (conversation_id);


--
-- Name: idx_messages_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_created ON public.messages USING btree (created_at DESC);


--
-- Name: idx_messages_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_user ON public.messages USING btree (user_id);


--
-- Name: idx_prayer_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prayer_requests_status ON public.prayer_requests USING btree (status);


--
-- Name: idx_prayer_requests_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prayer_requests_user ON public.prayer_requests USING btree (user_id);


--
-- Name: idx_psych_profile_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_psych_profile_user ON public.user_psychological_profile USING btree (user_id);


--
-- Name: idx_saved_content_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_saved_content_tipo ON public.saved_content USING btree (tipo);


--
-- Name: idx_saved_content_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_saved_content_user ON public.saved_content USING btree (user_id);


--
-- Name: idx_user_insights_categoria; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_insights_categoria ON public.user_insights USING btree (categoria);


--
-- Name: idx_user_insights_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_insights_user ON public.user_insights USING btree (user_id);


--
-- Name: idx_user_memories_categoria; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_memories_categoria ON public.user_memories USING btree (categoria);


--
-- Name: idx_user_memories_importancia; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_memories_importancia ON public.user_memories USING btree (importancia DESC);


--
-- Name: idx_user_memories_ultima_mencao; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_memories_ultima_mencao ON public.user_memories USING btree (ultima_mencao DESC);


--
-- Name: idx_user_memories_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_memories_user ON public.user_memories USING btree (user_id);


--
-- Name: user_memories trigger_normalize_fato; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_normalize_fato BEFORE INSERT OR UPDATE OF fato ON public.user_memories FOR EACH ROW EXECUTE FUNCTION public.auto_normalize_fato();


--
-- Name: prayer_requests update_prayer_requests_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_prayer_requests_updated_at BEFORE UPDATE ON public.prayer_requests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: user_insights update_user_insights_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_insights_updated_at BEFORE UPDATE ON public.user_insights FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: user_memories update_user_memories_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_memories_updated_at BEFORE UPDATE ON public.user_memories FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: user_profiles update_user_profiles_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: audit_log audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: message_feedback message_feedback_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_feedback
    ADD CONSTRAINT message_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: messages messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: prayer_requests prayer_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prayer_requests
    ADD CONSTRAINT prayer_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: saved_content saved_content_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_content
    ADD CONSTRAINT saved_content_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_devotional_interactions user_devotional_interactions_devotional_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devotional_interactions
    ADD CONSTRAINT user_devotional_interactions_devotional_id_fkey FOREIGN KEY (devotional_id) REFERENCES public.devotionals(id) ON DELETE CASCADE;


--
-- Name: user_devotional_interactions user_devotional_interactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devotional_interactions
    ADD CONSTRAINT user_devotional_interactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_insights user_insights_origem_conversa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_insights
    ADD CONSTRAINT user_insights_origem_conversa_id_fkey FOREIGN KEY (origem_conversa_id) REFERENCES public.conversations(id);


--
-- Name: user_insights user_insights_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_insights
    ADD CONSTRAINT user_insights_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_memories user_memories_origem_conversa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_memories
    ADD CONSTRAINT user_memories_origem_conversa_id_fkey FOREIGN KEY (origem_conversa_id) REFERENCES public.conversations(id);


--
-- Name: user_memories user_memories_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_memories
    ADD CONSTRAINT user_memories_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.user_memories(id);


--
-- Name: user_memories user_memories_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_memories
    ADD CONSTRAINT user_memories_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_psychological_profile user_psychological_profile_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_psychological_profile
    ADD CONSTRAINT user_psychological_profile_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: conversations Users can view own conversations; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own conversations" ON public.conversations USING ((user_id = (current_setting('app.current_user_id'::text))::uuid));


--
-- Name: user_insights Users can view own insights; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own insights" ON public.user_insights USING ((user_id = (current_setting('app.current_user_id'::text))::uuid));


--
-- Name: messages Users can view own messages; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own messages" ON public.messages USING ((user_id = (current_setting('app.current_user_id'::text))::uuid));


--
-- Name: prayer_requests Users can view own prayer requests; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own prayer requests" ON public.prayer_requests USING ((user_id = (current_setting('app.current_user_id'::text))::uuid));


--
-- Name: user_profiles Users can view own profile; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own profile" ON public.user_profiles USING ((user_id = (current_setting('app.current_user_id'::text))::uuid));


--
-- Name: saved_content Users can view own saved content; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own saved content" ON public.saved_content USING ((user_id = (current_setting('app.current_user_id'::text))::uuid));


--
-- Name: conversations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

--
-- Name: messages; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

--
-- Name: prayer_requests; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.prayer_requests ENABLE ROW LEVEL SECURITY;

--
-- Name: saved_content; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.saved_content ENABLE ROW LEVEL SECURITY;

--
-- Name: user_insights; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_insights ENABLE ROW LEVEL SECURITY;

--
-- Name: user_memories; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_memories ENABLE ROW LEVEL SECURITY;

--
-- Name: user_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: user_memories users_own_memories; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY users_own_memories ON public.user_memories USING ((user_id = (current_setting('app.current_user_id'::text, true))::uuid));


--
-- PostgreSQL database dump complete
--

\unrestrict n5hLkSdkiu2sctpgi9hwztFIik84V68Xa9RtdKZOfJhM46HcrcNzI4BGTGT00sk


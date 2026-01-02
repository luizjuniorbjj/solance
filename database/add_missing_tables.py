"""
Script para adicionar tabelas faltantes no Railway PostgreSQL

IMPORTANTE: Configure DATABASE_URL como variável de ambiente antes de executar.
Nunca commite credenciais de banco de dados no código!
"""
import asyncio
import asyncpg
import os

# SEGURANÇA: Usar variável de ambiente - nunca hardcode credenciais!
RAILWAY_DATABASE_URL = os.getenv("DATABASE_URL")

if not RAILWAY_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não configurada! "
        "Configure a variável de ambiente antes de executar este script."
    )

MISSING_TABLES_SQL = """
-- ============================================
-- FUNÇÃO: normalize_text
-- ============================================
CREATE OR REPLACE FUNCTION normalize_text(input_text text) RETURNS text
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

-- ============================================
-- FUNÇÃO: auto_normalize_fato
-- ============================================
CREATE OR REPLACE FUNCTION auto_normalize_fato() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.fato_normalizado := normalize_text(NEW.fato);
    RETURN NEW;
END;
$$;

-- ============================================
-- TABELA: user_memories
-- ============================================
CREATE TABLE IF NOT EXISTS user_memories (
    id uuid DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
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
    status character varying(20) DEFAULT 'active',
    supersedes_id uuid,
    confidence numeric(3,2) DEFAULT 0.80,
    payload jsonb,
    fato_normalizado text
);

-- Índices para user_memories
CREATE INDEX IF NOT EXISTS idx_user_memories_user ON user_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memories_categoria ON user_memories(categoria);
CREATE INDEX IF NOT EXISTS idx_user_memories_active ON user_memories(is_active);

-- Trigger para normalizar fato automaticamente
DROP TRIGGER IF EXISTS trg_normalize_fato ON user_memories;
CREATE TRIGGER trg_normalize_fato
    BEFORE INSERT OR UPDATE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION auto_normalize_fato();

-- ============================================
-- TABELA: user_psychological_profile
-- ============================================
CREATE TABLE IF NOT EXISTS user_psychological_profile (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    communication_style character varying(20) DEFAULT 'balanced',
    primary_needs text[],
    thinking_patterns jsonb DEFAULT '{}',
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
    last_analysis_at timestamp DEFAULT now(),
    analysis_count integer DEFAULT 0,
    confidence_score numeric(3,2) DEFAULT 0.5,
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now(),
    UNIQUE(user_id)
);

-- ============================================
-- TABELA: message_feedback
-- ============================================
CREATE TABLE IF NOT EXISTS message_feedback (
    id uuid NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    conversation_id uuid,
    message_content text NOT NULL,
    feedback_type character varying(50) NOT NULL,
    details text,
    status character varying(20) DEFAULT 'pending',
    created_at timestamp DEFAULT now(),
    reviewed_at timestamp,
    reviewer_notes text
);

-- ============================================
-- TABELA: learning_interactions (sistema de aprendizado)
-- ============================================
CREATE TABLE IF NOT EXISTS learning_interactions (
    id uuid DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id uuid,
    strategy_used character varying(50),
    emotion_before character varying(50),
    emotion_after character varying(50),
    response_time float,
    user_message_length integer,
    ai_response_length integer,
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_interactions_user ON learning_interactions(user_id);

-- ============================================
-- TABELA: learning_feedback
-- ============================================
CREATE TABLE IF NOT EXISTS learning_feedback (
    id uuid DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feedback_type character varying(50) NOT NULL,
    strategy_used character varying(50),
    context text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_feedback_user ON learning_feedback(user_id);
"""

async def add_missing_tables():
    print("🔌 Conectando ao Railway PostgreSQL...")

    try:
        conn = await asyncpg.connect(RAILWAY_DATABASE_URL)
        print("✅ Conectado!")

        print("🚀 Adicionando tabelas faltantes...")
        await conn.execute(MISSING_TABLES_SQL)

        print("✅ Tabelas adicionadas!")

        # Verificar todas as tabelas
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"\n📊 Total de tabelas ({len(tables)}):")
        for t in tables:
            print(f"   - {t['tablename']}")

        await conn.close()
        print("\n🎉 Banco de dados completo!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_missing_tables())

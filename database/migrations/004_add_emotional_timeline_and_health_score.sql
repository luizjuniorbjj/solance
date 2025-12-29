-- ============================================
-- Migration 004: Emotional Timeline & Memory Health Score
-- Feature Layer 2 - Monitoramento interno de usuários
-- ============================================

-- ============================================
-- TABELA: emotional_timeline
-- Registro histórico de estados emocionais (uso interno)
-- ============================================
CREATE TABLE IF NOT EXISTS emotional_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,

    -- Estado emocional detectado
    emotion VARCHAR(50) NOT NULL, -- ansioso, triste, alegre, esperancoso, neutro, angustiado, etc.
    intensity DECIMAL(3,2) DEFAULT 0.5, -- 0.00 a 1.00 - intensidade da emoção
    confidence DECIMAL(3,2) DEFAULT 0.7, -- 0.00 a 1.00 - confiança na detecção

    -- Contexto
    trigger_detected VARCHAR(100), -- O que pode ter causado (trabalho, família, saúde, etc.)
    themes JSONB DEFAULT '[]', -- Temas associados à emoção

    -- Metadados temporais
    day_of_week INTEGER, -- 0=segunda, 6=domingo
    hour_of_day INTEGER, -- 0-23

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para consultas de padrões
CREATE INDEX IF NOT EXISTS idx_emotional_timeline_user ON emotional_timeline(user_id);
CREATE INDEX IF NOT EXISTS idx_emotional_timeline_created ON emotional_timeline(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_emotional_timeline_user_emotion ON emotional_timeline(user_id, emotion);
CREATE INDEX IF NOT EXISTS idx_emotional_timeline_user_day ON emotional_timeline(user_id, day_of_week);

-- ============================================
-- TABELA: memory_health_scores
-- Cache de Health Scores calculados
-- ============================================
CREATE TABLE IF NOT EXISTS memory_health_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Scores individuais (0-100)
    diversity_score INTEGER DEFAULT 0, -- Diversidade de categorias
    freshness_score INTEGER DEFAULT 0, -- Memórias atualizadas recentemente
    consistency_score INTEGER DEFAULT 0, -- Poucos conflitos semânticos
    engagement_score INTEGER DEFAULT 0, -- Frequência de menções/uso
    balance_score INTEGER DEFAULT 0, -- Proporção LUTA vs VITORIA

    -- Score final combinado
    overall_score INTEGER DEFAULT 0,
    health_level VARCHAR(20) DEFAULT 'unknown', -- excellent, good, moderate, poor, unknown

    -- Detalhes para diagnóstico
    total_memories INTEGER DEFAULT 0,
    active_memories INTEGER DEFAULT 0,
    categories_count INTEGER DEFAULT 0,
    conflicts_count INTEGER DEFAULT 0,
    stale_memories_count INTEGER DEFAULT 0, -- Memórias sem menção há mais de 30 dias

    -- Recomendações geradas
    recommendations JSONB DEFAULT '[]',

    -- Controle
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_health_user ON memory_health_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_health_level ON memory_health_scores(health_level);

-- ============================================
-- FUNÇÃO: calculate_memory_health_score
-- Calcula o Health Score de um usuário
-- ============================================
CREATE OR REPLACE FUNCTION calculate_memory_health_score(p_user_id UUID)
RETURNS TABLE (
    diversity_score INTEGER,
    freshness_score INTEGER,
    consistency_score INTEGER,
    engagement_score INTEGER,
    balance_score INTEGER,
    overall_score INTEGER,
    health_level VARCHAR(20),
    total_memories INTEGER,
    active_memories INTEGER,
    categories_count INTEGER,
    conflicts_count INTEGER,
    stale_memories_count INTEGER
) AS $$
DECLARE
    v_total_memories INTEGER;
    v_active_memories INTEGER;
    v_categories_count INTEGER;
    v_conflicts_count INTEGER;
    v_stale_count INTEGER;
    v_fresh_count INTEGER;
    v_luta_count INTEGER;
    v_vitoria_count INTEGER;
    v_high_mention_count INTEGER;
    v_diversity INTEGER;
    v_freshness INTEGER;
    v_consistency INTEGER;
    v_engagement INTEGER;
    v_balance INTEGER;
    v_overall INTEGER;
    v_level VARCHAR(20);
BEGIN
    -- Contar memórias totais e ativas
    SELECT COUNT(*), COUNT(*) FILTER (WHERE status = 'active')
    INTO v_total_memories, v_active_memories
    FROM user_memories WHERE user_id = p_user_id;

    -- Se não tem memórias, retorna score neutro
    IF v_active_memories = 0 THEN
        RETURN QUERY SELECT
            0::INTEGER, 0::INTEGER, 100::INTEGER, 0::INTEGER, 50::INTEGER,
            30::INTEGER, 'unknown'::VARCHAR(20),
            0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER, 0::INTEGER;
        RETURN;
    END IF;

    -- Diversidade: quantas categorias diferentes (8 possíveis)
    SELECT COUNT(DISTINCT categoria)
    INTO v_categories_count
    FROM user_memories WHERE user_id = p_user_id AND status = 'active';

    -- Score de diversidade (0-100)
    v_diversity := LEAST((v_categories_count::FLOAT / 8.0 * 100)::INTEGER, 100);

    -- Freshness: memórias mencionadas nos últimos 7 dias
    SELECT COUNT(*)
    INTO v_fresh_count
    FROM user_memories
    WHERE user_id = p_user_id
    AND status = 'active'
    AND ultima_mencao > NOW() - INTERVAL '7 days';

    -- Memórias antigas (sem menção há mais de 30 dias)
    SELECT COUNT(*)
    INTO v_stale_count
    FROM user_memories
    WHERE user_id = p_user_id
    AND status = 'active'
    AND ultima_mencao < NOW() - INTERVAL '30 days';

    -- Score de freshness
    v_freshness := CASE
        WHEN v_active_memories = 0 THEN 50
        ELSE LEAST((v_fresh_count::FLOAT / v_active_memories * 100)::INTEGER, 100)
    END;

    -- Consistency: contar conflitos (memórias superseded)
    SELECT COUNT(*)
    INTO v_conflicts_count
    FROM user_memories
    WHERE user_id = p_user_id
    AND status IN ('superseded', 'deactivated');

    -- Score de consistência (menos conflitos = melhor)
    v_consistency := CASE
        WHEN v_total_memories = 0 THEN 100
        ELSE GREATEST(100 - (v_conflicts_count::FLOAT / v_total_memories * 200)::INTEGER, 0)
    END;

    -- Engagement: memórias com muitas menções
    SELECT COUNT(*)
    INTO v_high_mention_count
    FROM user_memories
    WHERE user_id = p_user_id
    AND status = 'active'
    AND mencoes >= 3;

    v_engagement := CASE
        WHEN v_active_memories = 0 THEN 0
        ELSE LEAST((v_high_mention_count::FLOAT / v_active_memories * 100)::INTEGER, 100)
    END;

    -- Balance: proporção LUTA vs VITORIA
    SELECT
        COUNT(*) FILTER (WHERE categoria = 'LUTA'),
        COUNT(*) FILTER (WHERE categoria = 'VITORIA')
    INTO v_luta_count, v_vitoria_count
    FROM user_memories
    WHERE user_id = p_user_id AND status = 'active';

    -- Balance score (ideal é ter vitórias >= lutas)
    v_balance := CASE
        WHEN v_luta_count = 0 AND v_vitoria_count = 0 THEN 50
        WHEN v_luta_count = 0 THEN 100
        WHEN v_vitoria_count >= v_luta_count THEN
            LEAST(70 + (v_vitoria_count::FLOAT / v_luta_count * 15)::INTEGER, 100)
        ELSE
            GREATEST(50 - ((v_luta_count - v_vitoria_count)::FLOAT / v_luta_count * 30)::INTEGER, 20)
    END;

    -- Overall score (média ponderada)
    v_overall := (
        v_diversity * 0.20 +
        v_freshness * 0.25 +
        v_consistency * 0.20 +
        v_engagement * 0.15 +
        v_balance * 0.20
    )::INTEGER;

    -- Determinar nível
    v_level := CASE
        WHEN v_overall >= 80 THEN 'excellent'
        WHEN v_overall >= 60 THEN 'good'
        WHEN v_overall >= 40 THEN 'moderate'
        ELSE 'poor'
    END;

    RETURN QUERY SELECT
        v_diversity, v_freshness, v_consistency, v_engagement, v_balance,
        v_overall, v_level,
        v_total_memories, v_active_memories, v_categories_count,
        v_conflicts_count, v_stale_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FUNÇÃO: get_emotional_patterns
-- Analisa padrões emocionais do usuário
-- ============================================
CREATE OR REPLACE FUNCTION get_emotional_patterns(p_user_id UUID, p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    dominant_emotion VARCHAR(50),
    avg_intensity DECIMAL(3,2),
    emotion_variance DECIMAL(3,2),
    peak_day INTEGER,
    peak_hour INTEGER,
    common_triggers TEXT[],
    trend VARCHAR(20)
) AS $$
DECLARE
    v_dominant VARCHAR(50);
    v_avg_intensity DECIMAL(3,2);
    v_variance DECIMAL(3,2);
    v_peak_day INTEGER;
    v_peak_hour INTEGER;
    v_triggers TEXT[];
    v_trend VARCHAR(20);
    v_recent_avg DECIMAL;
    v_older_avg DECIMAL;
BEGIN
    -- Emoção dominante
    SELECT emotion, AVG(intensity)
    INTO v_dominant, v_avg_intensity
    FROM emotional_timeline
    WHERE user_id = p_user_id AND created_at > NOW() - (p_days || ' days')::INTERVAL
    GROUP BY emotion
    ORDER BY COUNT(*) DESC, AVG(intensity) DESC
    LIMIT 1;

    IF v_dominant IS NULL THEN
        RETURN QUERY SELECT
            'neutro'::VARCHAR(50), 0.5::DECIMAL(3,2), 0.0::DECIMAL(3,2),
            NULL::INTEGER, NULL::INTEGER, ARRAY[]::TEXT[], 'stable'::VARCHAR(20);
        RETURN;
    END IF;

    -- Variância emocional (diversidade de emoções)
    SELECT STDDEV(intensity)::DECIMAL(3,2)
    INTO v_variance
    FROM emotional_timeline
    WHERE user_id = p_user_id AND created_at > NOW() - (p_days || ' days')::INTERVAL;

    -- Dia de pico
    SELECT day_of_week
    INTO v_peak_day
    FROM emotional_timeline
    WHERE user_id = p_user_id
    AND created_at > NOW() - (p_days || ' days')::INTERVAL
    AND emotion IN ('ansioso', 'triste', 'angustiado', 'estressado')
    GROUP BY day_of_week
    ORDER BY COUNT(*) DESC
    LIMIT 1;

    -- Hora de pico
    SELECT hour_of_day
    INTO v_peak_hour
    FROM emotional_timeline
    WHERE user_id = p_user_id
    AND created_at > NOW() - (p_days || ' days')::INTERVAL
    GROUP BY hour_of_day
    ORDER BY COUNT(*) DESC
    LIMIT 1;

    -- Triggers mais comuns
    SELECT ARRAY_AGG(DISTINCT trigger_detected)
    INTO v_triggers
    FROM (
        SELECT trigger_detected
        FROM emotional_timeline
        WHERE user_id = p_user_id
        AND created_at > NOW() - (p_days || ' days')::INTERVAL
        AND trigger_detected IS NOT NULL
        GROUP BY trigger_detected
        ORDER BY COUNT(*) DESC
        LIMIT 3
    ) t;

    -- Tendência (comparar última semana com semanas anteriores)
    SELECT AVG(intensity)
    INTO v_recent_avg
    FROM emotional_timeline
    WHERE user_id = p_user_id
    AND created_at > NOW() - INTERVAL '7 days'
    AND emotion IN ('ansioso', 'triste', 'angustiado');

    SELECT AVG(intensity)
    INTO v_older_avg
    FROM emotional_timeline
    WHERE user_id = p_user_id
    AND created_at BETWEEN NOW() - (p_days || ' days')::INTERVAL AND NOW() - INTERVAL '7 days'
    AND emotion IN ('ansioso', 'triste', 'angustiado');

    v_trend := CASE
        WHEN v_recent_avg IS NULL OR v_older_avg IS NULL THEN 'stable'
        WHEN v_recent_avg > v_older_avg * 1.2 THEN 'worsening'
        WHEN v_recent_avg < v_older_avg * 0.8 THEN 'improving'
        ELSE 'stable'
    END;

    RETURN QUERY SELECT
        v_dominant,
        COALESCE(v_avg_intensity, 0.5),
        COALESCE(v_variance, 0.0),
        v_peak_day,
        v_peak_hour,
        COALESCE(v_triggers, ARRAY[]::TEXT[]),
        v_trend;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar updated_at
CREATE TRIGGER update_memory_health_scores_updated_at
    BEFORE UPDATE ON memory_health_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

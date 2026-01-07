-- ============================================
-- AiSyster DATABASE SCHEMA
-- Banco de dados para memória e perfil de usuários
-- ============================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- TABELA: users (Usuários)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- NULL para usuários OAuth
    oauth_provider VARCHAR(20), -- 'google', 'apple', ou NULL para email/senha
    oauth_id VARCHAR(255), -- ID do usuário no provider OAuth
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,
    premium_until TIMESTAMP WITH TIME ZONE,
    trial_messages_used INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,

    -- Legal/Compliance
    accepted_terms BOOLEAN DEFAULT FALSE,
    accepted_terms_at TIMESTAMP WITH TIME ZONE,
    accepted_privacy BOOLEAN DEFAULT FALSE,
    accepted_privacy_at TIMESTAMP WITH TIME ZONE,
    terms_version VARCHAR(20) DEFAULT '1.0', -- Versão dos termos aceitos

    -- Stripe
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    subscription_status VARCHAR(50), -- active, past_due, cancelled, etc.
    subscription_start_date TIMESTAMP WITH TIME ZONE,
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE
);

-- ============================================
-- TABELA: user_profiles (Perfil do Usuário)
-- Dados que a IA usa para personalizar
-- ============================================
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Dados básicos
    nome VARCHAR(100),
    apelido VARCHAR(50),
    idade INTEGER,
    genero VARCHAR(20), -- masculino, feminino, prefere_nao_dizer
    estado_civil VARCHAR(30), -- solteiro, casado, divorciado, viuvo
    filhos JSONB DEFAULT '[]', -- [{"nome": "Pedro", "idade": 5}]
    profissao VARCHAR(100),
    cidade VARCHAR(100),

    -- Dados espirituais
    denominacao VARCHAR(100), -- Batista, Assembleia, Católico, etc.
    tempo_de_fe VARCHAR(50), -- "5 anos", "desde criança", "recém-convertido"
    batizado BOOLEAN,
    data_batismo DATE,
    igreja_local VARCHAR(200),
    cargo_igreja VARCHAR(100), -- líder de jovens, músico, membro, etc.

    -- Preferências de comunicação
    tom_preferido VARCHAR(50) DEFAULT 'equilibrado', -- direto, suave, equilibrado
    profundidade VARCHAR(50) DEFAULT 'moderada', -- superficial, moderada, profunda
    usa_emoji BOOLEAN DEFAULT TRUE,
    horario_ativo VARCHAR(50), -- manhã, tarde, noite, madrugada

    -- Criptografado - dados sensíveis
    lutas_encrypted BYTEA, -- Lutas pessoais (ansiedade, vício, etc.)
    notas_pastorais_encrypted BYTEA, -- Notas sobre a pessoa

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABELA: conversations (Conversas)
-- ============================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,

    -- Resumo da conversa (gerado pela IA)
    resumo TEXT,
    temas JSONB DEFAULT '[]', -- ["ansiedade", "trabalho", "família"]
    humor_inicial VARCHAR(50),
    humor_final VARCHAR(50),
    versiculos_citados JSONB DEFAULT '[]',
    decisoes_tomadas JSONB DEFAULT '[]',

    is_archived BOOLEAN DEFAULT FALSE
);

-- ============================================
-- TABELA: messages (Mensagens individuais)
-- ============================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL, -- 'user' ou 'assistant'
    content_encrypted BYTEA NOT NULL, -- Conteúdo criptografado

    -- Metadados (não sensíveis)
    tokens_used INTEGER,
    model_used VARCHAR(50),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABELA: prayer_requests (Pedidos de Oração)
-- ============================================
CREATE TABLE prayer_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    titulo VARCHAR(200) NOT NULL,
    descricao_encrypted BYTEA, -- Detalhes criptografados
    categoria VARCHAR(50), -- saúde, família, trabalho, relacionamento, espiritual

    status VARCHAR(20) DEFAULT 'ativo', -- ativo, respondido, arquivado
    data_resposta DATE,
    testemunho_encrypted BYTEA, -- Como Deus respondeu

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABELA: saved_content (Conteúdo Salvo)
-- Versículos, insights, devocionais salvos
-- ============================================
CREATE TABLE saved_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    tipo VARCHAR(30) NOT NULL, -- versiculo, insight, devocional, oracao
    conteudo TEXT NOT NULL,
    referencia VARCHAR(100), -- "João 3:16" ou "Conversa de 20/12"
    nota_pessoal TEXT,

    tags JSONB DEFAULT '[]',
    is_favorite BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABELA: user_insights (Insights sobre o usuário)
-- O que a IA aprendeu sobre a pessoa
-- ============================================
CREATE TABLE user_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    categoria VARCHAR(50) NOT NULL, -- luta, vitoria, padrao, preferencia
    insight_encrypted BYTEA NOT NULL,
    confianca DECIMAL(3,2), -- 0.00 a 1.00 - quão certo a IA está

    origem_conversa_id UUID REFERENCES conversations(id),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABELA: devotionals (Devocionais diários)
-- ============================================
CREATE TABLE devotionals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data DATE UNIQUE NOT NULL,

    versiculo TEXT NOT NULL,
    referencia VARCHAR(100) NOT NULL,
    meditacao TEXT NOT NULL,
    oracao TEXT NOT NULL,

    tema VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABELA: user_devotional_interactions
-- Interações do usuário com devocionais
-- ============================================
CREATE TABLE user_devotional_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    devotional_id UUID REFERENCES devotionals(id) ON DELETE CASCADE,

    lido BOOLEAN DEFAULT FALSE,
    lido_em TIMESTAMP WITH TIME ZONE,
    salvo BOOLEAN DEFAULT FALSE,
    nota_pessoal TEXT,

    UNIQUE(user_id, devotional_id)
);

-- ============================================
-- TABELA: audit_log (Log de auditoria)
-- Para segurança e compliance
-- ============================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),

    action VARCHAR(100) NOT NULL, -- login, logout, message_sent, profile_updated
    ip_address INET,
    user_agent TEXT,
    details JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_messages_created ON messages(created_at DESC);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);

CREATE INDEX idx_prayer_requests_user ON prayer_requests(user_id);
CREATE INDEX idx_prayer_requests_status ON prayer_requests(status);

CREATE INDEX idx_saved_content_user ON saved_content(user_id);
CREATE INDEX idx_saved_content_tipo ON saved_content(tipo);

CREATE INDEX idx_user_insights_user ON user_insights(user_id);
CREATE INDEX idx_user_insights_categoria ON user_insights(categoria);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at DESC);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- Usuário só vê seus próprios dados
-- ============================================
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE prayer_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_insights ENABLE ROW LEVEL SECURITY;

-- Políticas de segurança
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY "Users can view own conversations" ON conversations
    FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY "Users can view own messages" ON messages
    FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY "Users can view own prayer requests" ON prayer_requests
    FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY "Users can view own saved content" ON saved_content
    FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY "Users can view own insights" ON user_insights
    FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

-- ============================================
-- FUNÇÕES ÚTEIS
-- ============================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_prayer_requests_updated_at
    BEFORE UPDATE ON prayer_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_insights_updated_at
    BEFORE UPDATE ON user_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

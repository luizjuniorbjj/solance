-- ============================================
-- Migration: Adiciona campos OAuth na tabela users
-- Data: 2024-12-27
-- ============================================

-- Adiciona colunas para OAuth
ALTER TABLE users
ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(20),
ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255);

-- Permite password_hash NULL (para usuários OAuth)
ALTER TABLE users
ALTER COLUMN password_hash DROP NOT NULL;

-- Índice para busca por OAuth ID
CREATE INDEX IF NOT EXISTS idx_users_oauth ON users(oauth_provider, oauth_id);

-- Comentários
COMMENT ON COLUMN users.oauth_provider IS 'Provider OAuth: google, apple, ou NULL para email/senha';
COMMENT ON COLUMN users.oauth_id IS 'ID único do usuário no provider OAuth';

-- ============================================
-- Migration: Add terms acceptance fields
-- Date: December 2024
-- Description: Adds fields for legal compliance (LGPD)
-- ============================================

-- Adiciona campos de aceite de termos na tabela users
ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_terms BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_terms_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_privacy BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_privacy_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_version VARCHAR(20) DEFAULT '1.0';

-- Para usuários existentes, assume-se aceite implícito (legado)
UPDATE users
SET accepted_terms = TRUE,
    accepted_privacy = TRUE,
    accepted_terms_at = created_at,
    accepted_privacy_at = created_at,
    terms_version = '1.0'
WHERE accepted_terms IS NULL OR accepted_terms = FALSE;

-- Comentários para documentação
COMMENT ON COLUMN users.accepted_terms IS 'Se o usuário aceitou os Termos de Uso';
COMMENT ON COLUMN users.accepted_terms_at IS 'Data/hora do aceite dos Termos';
COMMENT ON COLUMN users.accepted_privacy IS 'Se o usuário aceitou a Política de Privacidade';
COMMENT ON COLUMN users.accepted_privacy_at IS 'Data/hora do aceite da Política';
COMMENT ON COLUMN users.terms_version IS 'Versão dos termos aceitos pelo usuário';

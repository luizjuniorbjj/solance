-- SoulHaven - Migração: Adicionar contadores separados para Push e Email
-- Execute este script no banco de dados PostgreSQL/Supabase

-- Adicionar colunas para contagem separada de Push e Email
DO $$
BEGIN
    -- push_sent
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'notifications' AND column_name = 'push_sent') THEN
        ALTER TABLE notifications ADD COLUMN push_sent INTEGER DEFAULT 0;
    END IF;

    -- push_failed
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'notifications' AND column_name = 'push_failed') THEN
        ALTER TABLE notifications ADD COLUMN push_failed INTEGER DEFAULT 0;
    END IF;

    -- email_sent
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'notifications' AND column_name = 'email_sent') THEN
        ALTER TABLE notifications ADD COLUMN email_sent INTEGER DEFAULT 0;
    END IF;

    -- email_failed
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'notifications' AND column_name = 'email_failed') THEN
        ALTER TABLE notifications ADD COLUMN email_failed INTEGER DEFAULT 0;
    END IF;
END $$;

-- Verificar se as colunas foram criadas
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'notifications'
AND column_name IN ('push_sent', 'push_failed', 'email_sent', 'email_failed');

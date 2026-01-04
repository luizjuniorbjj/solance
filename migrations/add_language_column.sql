-- Migration: Add language column to user_profiles
-- Supports: en (English), pt (Portuguese), es (Spanish)

ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'en';

-- Add comment
COMMENT ON COLUMN user_profiles.language IS 'User preferred language: en, pt, es';

-- Create index for potential language-based queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_language ON user_profiles(language);

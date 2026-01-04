-- Migration: Add language and voice columns to user_profiles
-- Supports: auto (detect), en (English), pt (Portuguese), es (Spanish)

-- Language for text/interface (AiSyster responses)
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'auto';

-- Language for Text-to-Speech (spoken responses)
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS spoken_language VARCHAR(10) DEFAULT 'auto';

-- Voice for Text-to-Speech (OpenAI voices: alloy, echo, fable, onyx, nova, shimmer)
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS voice VARCHAR(20) DEFAULT 'nova';

-- Add comments
COMMENT ON COLUMN user_profiles.language IS 'User preferred language for text: auto, en, pt, es';
COMMENT ON COLUMN user_profiles.spoken_language IS 'User preferred language for TTS: auto, en, pt, es';
COMMENT ON COLUMN user_profiles.voice IS 'User preferred voice for TTS: alloy, echo, fable, onyx, nova, shimmer';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_language ON user_profiles(language);
CREATE INDEX IF NOT EXISTS idx_user_profiles_spoken_language ON user_profiles(spoken_language);

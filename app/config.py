"""
AiSyster - Configuracoes
Variaveis de ambiente e configuracoes globais
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# API KEYS
# ============================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Para STT (Whisper) e TTS

# ============================================
# DATABASE
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/soulhaven")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ============================================
# SECURITY
# ============================================
SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-secreta-muito-longa-aqui-32chars")

# ENCRYPTION_KEY - CRÍTICO: Esta chave NUNCA pode mudar ou os dados serão perdidos!
# OBRIGATÓRIO: Deve ser configurada via variável de ambiente em produção.
# Se você não tem a chave, entre em contato com o administrador do sistema.
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError(
        "[CRITICAL] ENCRYPTION_KEY não configurada! "
        "Esta variável é OBRIGATÓRIA para criptografia de dados. "
        "Configure no Railway ou arquivo .env antes de iniciar."
    )

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_HOURS = 1  # Access token: 1 hora (segurança)
JWT_REFRESH_TOKEN_DAYS = 30  # Refresh token: 30 dias (conveniência)

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "AiSyster"
APP_VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Modo manutencao - ativa pagina de manutencao para todos usuarios
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"

# ============================================
# AI SETTINGS
# ============================================
AI_MODEL_PRIMARY = "claude-sonnet-4-20250514"  # Assinantes - máxima qualidade pastoral
AI_MODEL_FALLBACK = "claude-3-5-haiku-20241022"  # Trial/Free - economia, boa qualidade
MAX_TOKENS_RESPONSE = 300  # Respostas adequadas - permite listas completas
MAX_CONTEXT_TOKENS = 4000

# Web Search - Pesquisa na internet quando necessário
WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "True").lower() == "true"
WEB_SEARCH_MAX_RESULTS = 5  # Máximo de resultados por pesquisa

# Voice Settings - STT (Speech-to-Text) e TTS (Text-to-Speech)
VOICE_ENABLED = os.getenv("VOICE_ENABLED", "True").lower() == "true"
# STT - Whisper (OpenAI)
STT_MODEL = "whisper-1"  # Modelo de transcrição
STT_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB (limite do Whisper)
# TTS - OpenAI
TTS_MODEL = "tts-1"  # tts-1 (rápido) ou tts-1-hd (qualidade)
TTS_VOICE = "nova"  # alloy, echo, fable, onyx, nova, shimmer (nova = feminina suave)
TTS_SPEED = 1.0  # 0.25 a 4.0

# ============================================
# LIMITS
# ============================================
FREE_MESSAGE_LIMIT = 30  # Limite total para usuários free
FREE_WARNING_AT = 20  # Aviso sutil "10 restantes"
FREE_URGENT_AT = 25  # Aviso urgente "5 restantes"
TRIAL_MESSAGES_LIMIT_ANONYMOUS = 5  # Limite para visitantes sem conta
MONTHLY_MESSAGE_LIMIT = 500  # Premium - antes de throttling
THROTTLE_DELAY_SECONDS = 3

# ============================================
# PRICING
# ============================================
SUBSCRIPTION_PRICE_USD = 5.99
TRIAL_DAYS = 7

# ============================================
# STRIPE
# ============================================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")  # ID do preço no Stripe

# ============================================
# OAUTH SETTINGS
# ============================================
# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# Apple OAuth
APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID", "")  # Service ID
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID", "")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID", "")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY", "")  # Contents of .p8 file
APPLE_REDIRECT_URI = os.getenv("APPLE_REDIRECT_URI", "http://localhost:8000/auth/apple/callback")

# ============================================
# CORS SETTINGS
# ============================================
# Em desenvolvimento: permite todas as origens
# Em produção: especificar domínios permitidos
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["*"]

# Dominios padrao para producao
PRODUCTION_ORIGINS = [
    "https://aisyster.com",
    "https://www.aisyster.com",
    "https://app.aisyster.com",
]

# ============================================
# EMAIL SETTINGS (Resend)
# ============================================
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = "AiSyster <noreply@aisyster.com>"
EMAIL_REPLY_TO = "contato@aisyster.com"
APP_URL = os.getenv("APP_URL", "https://www.aisyster.com")

# ============================================
# ADMIN SETTINGS
# ============================================
# Emails que têm acesso ao painel admin
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "luizjuniorbjj@gmail.com").split(",")

# ============================================
# PUSH NOTIFICATIONS (VAPID)
# ============================================
VAPID_PUBLIC_KEY = os.getenv(
    "VAPID_PUBLIC_KEY",
    "BPyw4MN-PkXcXZliOPikeQSB2f18vc_vIol247-qBi3Bn2q3jlDXuqYyWXkkfX0sX_ZYzIQ6o8l24CLjfwqAFyQ"
)
VAPID_PRIVATE_KEY = os.getenv(
    "VAPID_PRIVATE_KEY",
    "7rIhcelXxHlm7taPNzC7gmMu6VHvIPQxt3gU5QKi8aE"
)
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "contato@aisyster.com")

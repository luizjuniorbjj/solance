"""
SoulHaven - Configurações
Variáveis de ambiente e configurações globais
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# API KEYS
# ============================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

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
# A chave de produção é hardcoded como fallback final para garantir que NUNCA seja perdida.
# Em produção, sempre defina via variável de ambiente para segurança adicional.
_PRODUCTION_ENCRYPTION_KEY = "SH_PROD_ENC_2024_v1_NEVER_CHANGE_THIS_KEY!"  # Fallback permanente
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", _PRODUCTION_ENCRYPTION_KEY)

# Validação e log de segurança
if ENCRYPTION_KEY == "sua-chave-de-criptografia-32chars":
    print("[CRITICAL] ENCRYPTION_KEY está usando valor de desenvolvimento! Configure em produção.")
elif ENCRYPTION_KEY == _PRODUCTION_ENCRYPTION_KEY:
    print("[INFO] ENCRYPTION_KEY usando fallback de produção (seguro).")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 dias

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "SoulHaven"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ============================================
# AI SETTINGS
# ============================================
AI_MODEL_PRIMARY = "claude-sonnet-4-20250514"  # Assinantes - máxima qualidade pastoral
AI_MODEL_FALLBACK = "claude-3-5-haiku-20241022"  # Trial/Free - economia, boa qualidade
MAX_TOKENS_RESPONSE = 300  # Respostas moderadas
MAX_CONTEXT_TOKENS = 4000

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

# Domínios padrão para produção
PRODUCTION_ORIGINS = [
    "https://soulhaven.app",
    "https://www.soulhaven.app",
    "https://app.soulhaven.app",
]

# ============================================
# EMAIL SETTINGS (Resend)
# ============================================
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = "SoulHaven <noreply@soulhavenapp.com>"
EMAIL_REPLY_TO = "contato@soulhavenapp.com"
APP_URL = os.getenv("APP_URL", "https://www.soulhavenapp.com")

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
    "BDjIT_RYliLCj-aJ7Y11Bqqx-6sfsXUY_Zm2ng3fmvco5yPhS79X_tRN-q9wkC-U189IoIUnC7C8k8Sd7vJqeUk"
)
VAPID_PRIVATE_KEY = os.getenv(
    "VAPID_PRIVATE_KEY",
    """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgS7oe7VQ4Ejs6A2H/
c0xMRNsJla2qRPt5/IqsexlGTWahRANCAAQ4yE/0WJYiwo/mie2NdQaqsfurH7F1
GP2Ztp4N35r3KOcj4Uu/V/7UTfqvcJAvlNfPSKCFJwuwvJPEne7yanlJ
-----END PRIVATE KEY-----"""
)
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "contato@soulhavenapp.com")

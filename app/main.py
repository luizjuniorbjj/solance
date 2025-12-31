"""
AiSYSTER - Backend Principal
API completa com memória, autenticação e personalização
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import (
    APP_NAME, APP_VERSION, DEBUG, MAINTENANCE_MODE,
    CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, CORS_ALLOW_METHODS, CORS_ALLOW_HEADERS,
    PRODUCTION_ORIGINS, ENCRYPTION_KEY, _PRODUCTION_ENCRYPTION_KEY
)
from app.database import init_db, close_db
from app.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.profile import router as profile_router
from app.routes.prayer import router as prayer_router
from app.routes.devotional import router as devotional_router
from app.routes.admin import router as admin_router
from app.routes.payment import router as payment_router
from app.routes.memories import router as memories_router
from app.routes.push import router as push_router
from app.routes.notifications import router as notifications_router
from app.notification_scheduler import notification_scheduler


# ============================================
# LIFECYCLE
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia inicialização e shutdown"""
    # Startup
    print(f"\n🕊️  {APP_NAME} v{APP_VERSION}")
    print("=" * 40)

    # Validação crítica de segurança
    if ENCRYPTION_KEY == "sua-chave-de-criptografia-32chars":
        print("⚠️  [CRITICAL] ENCRYPTION_KEY inválida! Dados podem ser perdidos!")
    elif ENCRYPTION_KEY == _PRODUCTION_ENCRYPTION_KEY:
        print("🔐 Criptografia: usando chave de produção (fallback)")
    else:
        print("🔐 Criptografia: chave configurada via ambiente")

    await init_db()
    print("✅ Banco de dados conectado")

    # Iniciar scheduler de notificacoes
    await notification_scheduler.start()
    print("✅ Scheduler de notificacoes iniciado")

    if MAINTENANCE_MODE:
        print("🛠️  MODO MANUTENCAO ATIVADO")
    print("✅ API pronta")
    print("=" * 40)
    print(f"📍 http://localhost:8000")
    print(f"📚 http://localhost:8000/docs\n")

    yield

    # Shutdown
    await notification_scheduler.stop()
    await close_db()
    print("\n👋 AiSYSTER encerrado\n")


# ============================================
# APP
# ============================================

app = FastAPI(
    title=APP_NAME,
    description="""
    **AiSYSTER** - Seu companheiro de IA para apoio emocional e espiritual

    Ajudando pessoas a atravessarem as lutas da vida com clareza, fé e continuidade.
    """,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None
)

# ============================================
# CORS
# ============================================

# Determinar origens permitidas
def get_cors_origins():
    """Retorna origens CORS baseado no ambiente"""
    if DEBUG:
        # Desenvolvimento: permite localhost e file://
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "*"  # Permite todas em dev
        ]
    elif CORS_ORIGINS != ["*"]:
        # Usa origens configuradas via env var
        return CORS_ORIGINS
    else:
        # Produção: usa domínios oficiais
        return PRODUCTION_ORIGINS


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)


# ============================================
# ROTAS
# ============================================

# Health check (API status)
@app.get("/api", tags=["Status"])
async def api_status():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "message": "Seu companheiro de IA para apoio emocional e espiritual"
    }


@app.get("/health", tags=["Status"])
async def health():
    return {"status": "healthy"}


# Incluir routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(prayer_router)
app.include_router(devotional_router)
app.include_router(admin_router)
app.include_router(payment_router)
app.include_router(memories_router)
app.include_router(push_router)
app.include_router(notifications_router)


# ============================================
# FRONTEND (Servir arquivos estáticos)
# ============================================

# Caminho para o frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/maintenance", tags=["Frontend"])
async def serve_maintenance():
    """Serve a pagina de manutencao"""
    return FileResponse(FRONTEND_DIR / "maintenance.html")


@app.get("/", tags=["Frontend"])
@app.get("/app", tags=["Frontend"])
@app.get("/app/", tags=["Frontend"])
async def serve_frontend():
    """Serve a página principal do AiSYSTER"""
    if MAINTENANCE_MODE:
        return FileResponse(FRONTEND_DIR / "maintenance.html")
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/admin", tags=["Frontend"])
@app.get("/admin/", tags=["Frontend"])
async def serve_admin():
    """Serve o painel de administração"""
    return FileResponse(FRONTEND_DIR / "admin.html")


# ============================================
# PÁGINAS LEGAIS
# ============================================

@app.get("/termos", tags=["Legal"])
@app.get("/termos/", tags=["Legal"])
async def serve_terms():
    """Serve a página de Termos de Uso"""
    return FileResponse(FRONTEND_DIR / "termos.html")


@app.get("/privacidade", tags=["Legal"])
@app.get("/privacidade/", tags=["Legal"])
async def serve_privacy():
    """Serve a página de Política de Privacidade"""
    return FileResponse(FRONTEND_DIR / "privacidade.html")


# ============================================
# PWA FILES
# ============================================

@app.get("/manifest.json", tags=["PWA"])
async def serve_manifest():
    """Serve o manifest.json para PWA"""
    return FileResponse(
        FRONTEND_DIR / "manifest.json",
        media_type="application/manifest+json"
    )


@app.get("/sw.js", tags=["PWA"])
async def serve_service_worker():
    """Serve o Service Worker"""
    return FileResponse(
        FRONTEND_DIR / "sw.js",
        media_type="application/javascript"
    )


@app.get("/offline.html", tags=["PWA"])
async def serve_offline():
    """Serve a página offline"""
    return FileResponse(FRONTEND_DIR / "offline.html")


# ============================================
# LEGAL PAGES
# ============================================

@app.get("/termos", tags=["Legal"])
@app.get("/termos.html", tags=["Legal"])
async def serve_termos():
    """Serve os Termos de Uso"""
    return FileResponse(FRONTEND_DIR / "termos.html")


@app.get("/privacidade", tags=["Legal"])
@app.get("/privacidade.html", tags=["Legal"])
async def serve_privacidade():
    """Serve a Política de Privacidade"""
    return FileResponse(FRONTEND_DIR / "privacidade.html")


# ============================================
# PITCH DECK
# ============================================

@app.get("/pitch", tags=["Marketing"])
@app.get("/pitchdeck", tags=["Marketing"])
async def serve_pitchdeck():
    """Serve o Pitch Deck do AiSYSTER"""
    return FileResponse(FRONTEND_DIR / "pitch.html")


# ============================================
# SEO FILES
# ============================================

@app.get("/robots.txt", tags=["SEO"])
async def serve_robots():
    """Serve robots.txt para crawlers de busca"""
    return FileResponse(
        FRONTEND_DIR / "robots.txt",
        media_type="text/plain"
    )


@app.get("/sitemap.xml", tags=["SEO"])
async def serve_sitemap():
    """Serve sitemap.xml para indexação"""
    return FileResponse(
        FRONTEND_DIR / "sitemap.xml",
        media_type="application/xml"
    )


# Montar pasta estática (se houver assets)
if FRONTEND_DIR.exists():
    # Montar subpasta static para ícones e assets
    static_dir = FRONTEND_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static_assets")
    # Fallback para frontend dir
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )

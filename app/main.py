"""
AiSyster - Backend Principal
API completa com memória, autenticação e personalização
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse

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
    print("\n👋 AiSyster encerrado\n")


# ============================================
# APP
# ============================================

app = FastAPI(
    title=APP_NAME,
    description="""
    **AiSyster** - Sua companheira AI para apoio no dia a dia

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
# REDIRECT SOULHAVENAPP.COM -> AISYSTER.COM
# ============================================

OLD_DOMAINS = ["soulhavenapp.com", "www.soulhavenapp.com"]
NEW_DOMAIN = "www.aisyster.com"


@app.middleware("http")
async def redirect_old_domain(request: Request, call_next):
    """Redireciona soulhavenapp.com para aisyster.com"""
    host = request.headers.get("host", "").lower()

    # Verifica se e dominio antigo
    if any(old in host for old in OLD_DOMAINS):
        # Monta nova URL
        new_url = f"https://{NEW_DOMAIN}{request.url.path}"
        if request.url.query:
            new_url += f"?{request.url.query}"
        return RedirectResponse(url=new_url, status_code=301)

    return await call_next(request)


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
        "message": "Sua companheira AI para apoio no dia a dia"
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
    """Serve a página principal do AiSyster"""
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
    """Serve o Pitch Deck do AiSyster"""
    return FileResponse(FRONTEND_DIR / "pitch.html")


# ============================================
# CHECKOUT (Auto-login para pagamento)
# ============================================

@app.get("/checkout", tags=["Payment"])
async def checkout_with_token(token: str = Query(None)):
    """
    Processa token de checkout e redireciona para Stripe.
    Este endpoint e acessado quando o usuario clica em 'Assinar Premium' no app.

    Fluxo:
    1. App gera token via POST /auth/checkout-token
    2. App abre navegador com URL: /checkout?token=xxx
    3. Este endpoint valida token, cria sessao Stripe e redireciona
    """
    import stripe
    from app.database import get_db_instance
    from app.config import (
        STRIPE_SECRET_KEY, STRIPE_PRICE_ID, APP_URL,
        STRIPE_PUBLISHABLE_KEY
    )

    # Token obrigatorio
    if not token:
        return HTMLResponse(
            content=_checkout_error_page("Link invalido", "O link de checkout esta incompleto. Por favor, tente novamente pelo aplicativo."),
            status_code=400
        )

    # Verificar se Stripe esta configurado
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        return HTMLResponse(
            content=_checkout_error_page("Pagamento indisponivel", "O sistema de pagamentos esta temporariamente indisponivel. Tente novamente mais tarde."),
            status_code=503
        )

    # Obter conexao do banco
    db = await get_db_instance()
    if not db:
        return HTMLResponse(
            content=_checkout_error_page("Erro de sistema", "Nao foi possivel conectar ao banco de dados. Tente novamente."),
            status_code=500
        )

    # Validar token
    token_data = await db.verify_checkout_token(token)
    if not token_data:
        return HTMLResponse(
            content=_checkout_error_page("Link expirado", "Este link de checkout expirou ou ja foi utilizado. Por favor, gere um novo link pelo aplicativo."),
            status_code=400
        )

    # Verificar se usuario ja e premium
    if token_data.get("is_premium"):
        # Marcar token como usado
        await db.use_checkout_token(token)
        return HTMLResponse(
            content=_checkout_success_page("Voce ja e Premium!", "Sua conta ja possui assinatura premium ativa. Volte ao aplicativo para aproveitar todos os beneficios."),
            status_code=200
        )

    # Marcar token como usado (uso unico)
    await db.use_checkout_token(token)

    # Configurar Stripe
    stripe.api_key = STRIPE_SECRET_KEY

    try:
        # Criar sessao de checkout do Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=token_data["email"],
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url=f"{APP_URL}/app?payment=success",
            cancel_url=f"{APP_URL}/app?payment=cancelled",
            metadata={
                "user_id": str(token_data["user_id"]),
                "email": token_data["email"],
                "source": "checkout_token"
            },
            subscription_data={
                "metadata": {
                    "user_id": str(token_data["user_id"])
                }
            }
        )

        # Log de auditoria
        await db.log_audit(
            user_id=str(token_data["user_id"]),
            action="checkout_stripe_redirect",
            details={"session_id": checkout_session.id}
        )

        # Mostrar pagina de teste com dados do cartao antes de redirecionar
        # Em producao, trocar para: return RedirectResponse(url=checkout_session.url, status_code=303)
        return HTMLResponse(
            content=_checkout_test_page(checkout_session.url),
            status_code=200
        )

    except stripe.error.StripeError as e:
        return HTMLResponse(
            content=_checkout_error_page("Erro no pagamento", f"Ocorreu um erro ao processar o pagamento: {str(e)}"),
            status_code=500
        )


def _checkout_error_page(title: str, message: str) -> str:
    """Gera pagina HTML de erro no checkout"""
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - AiSyster</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: #ffffff;
                padding: 20px;
            }}
            .container {{ text-align: center; max-width: 400px; }}
            .icon {{ font-size: 60px; margin-bottom: 20px; }}
            h1 {{ font-size: 1.5rem; margin-bottom: 15px; color: #e74c3c; }}
            p {{ color: #b0b0b0; line-height: 1.6; margin-bottom: 30px; }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%);
                color: #1a1a2e;
                text-decoration: none;
                padding: 14px 28px;
                border-radius: 8px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">⚠️</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <a href="/app" class="btn">Voltar ao App</a>
        </div>
    </body>
    </html>
    """


def _checkout_success_page(title: str, message: str) -> str:
    """Gera pagina HTML de sucesso"""
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - AiSyster</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: #ffffff;
                padding: 20px;
            }}
            .container {{ text-align: center; max-width: 400px; }}
            .icon {{ font-size: 60px; margin-bottom: 20px; }}
            h1 {{ font-size: 1.5rem; margin-bottom: 15px; color: #d4af37; }}
            p {{ color: #b0b0b0; line-height: 1.6; margin-bottom: 30px; }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%);
                color: #1a1a2e;
                text-decoration: none;
                padding: 14px 28px;
                border-radius: 8px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">✨</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <a href="/app" class="btn">Voltar ao App</a>
        </div>
    </body>
    </html>
    """


def _checkout_test_page(stripe_url: str) -> str:
    """Gera pagina HTML com dados do cartao de teste"""
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ambiente de Teste - AiSyster</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: #ffffff;
                padding: 20px;
            }}
            .container {{ text-align: center; max-width: 420px; }}
            .badge {{
                display: inline-block;
                background: #f39c12;
                color: #1a1a2e;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                margin-bottom: 20px;
            }}
            h1 {{ font-size: 1.5rem; margin-bottom: 15px; color: #d4af37; }}
            p {{ color: #b0b0b0; line-height: 1.6; margin-bottom: 20px; }}
            .card-box {{
                background: rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }}
            .card-box h3 {{
                color: #d4af37;
                font-size: 14px;
                margin-bottom: 15px;
                text-transform: uppercase;
            }}
            .card-item {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            .card-item:last-child {{ border-bottom: none; }}
            .card-label {{ color: #888; font-size: 14px; }}
            .card-value {{
                color: #fff;
                font-family: 'Courier New', monospace;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%);
                color: #1a1a2e;
                text-decoration: none;
                padding: 16px 32px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                margin-top: 10px;
                transition: transform 0.2s;
            }}
            .btn:hover {{ transform: scale(1.02); }}
            .note {{
                font-size: 12px;
                color: #666;
                margin-top: 20px;
            }}
            .info-box {{
                background: rgba(212, 175, 55, 0.15);
                border: 1px solid rgba(212, 175, 55, 0.3);
                border-radius: 8px;
                padding: 12px 16px;
                margin-top: 20px;
                text-align: left;
            }}
            .info-box p {{
                font-size: 13px;
                color: #d4af37;
                margin: 0;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="badge">Ambiente de Teste</div>
            <h1>Dados do Cartao de Teste</h1>
            <p>Voce esta testando o sistema de pagamento. Nenhuma cobranca real sera feita.</p>

            <div class="card-box">
                <h3>Cartao de Credito para Teste</h3>
                <div class="card-item">
                    <span class="card-label">Numero</span>
                    <span class="card-value">4242 4242 4242 4242</span>
                </div>
                <div class="card-item">
                    <span class="card-label">Validade</span>
                    <span class="card-value">12/30</span>
                </div>
                <div class="card-item">
                    <span class="card-label">CVC</span>
                    <span class="card-value">123</span>
                </div>
                <div class="card-item">
                    <span class="card-label">Nome</span>
                    <span class="card-value">Seu nome</span>
                </div>
            </div>

            <div class="info-box">
                <p>Na proxima tela, digite os dados acima nos campos do cartao. Esses dados tambem aparecem na descricao do produto no Stripe.</p>
            </div>

            <a href="{stripe_url}" class="btn">Continuar para Pagamento</a>

            <p class="note">Voce sera redirecionado para a pagina segura do Stripe.</p>
        </div>
    </body>
    </html>
    """


# ============================================
# DIGITAL ASSET LINKS (TWA/Google Play)
# ============================================

@app.get("/.well-known/assetlinks.json", tags=["TWA"])
async def serve_assetlinks():
    """Serve Digital Asset Links para TWA/Google Play"""
    return FileResponse(
        FRONTEND_DIR / ".well-known" / "assetlinks.json",
        media_type="application/json"
    )


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

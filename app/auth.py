"""
SoulHaven - Sistema de Autenticação
Rotas e lógica de login/registro + OAuth (Google, Apple)
"""

from datetime import datetime
from typing import Optional
from urllib.parse import urlencode
import secrets
import httpx

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_secure_token
)
from app.database import get_db, Database
from app.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    APPLE_CLIENT_ID,
    APPLE_TEAM_ID,
    APPLE_KEY_ID,
    APPLE_PRIVATE_KEY,
    APPLE_REDIRECT_URI
)
from app.email_service import email_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Store OAuth states temporarily (in production, use Redis)
oauth_states = {}


# ============================================
# MODELOS
# ============================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nome: Optional[str] = None
    accepted_terms: bool = False  # Aceite dos Termos de Uso e Política de Privacidade


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 604800  # 7 dias em segundos


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    email: str
    nome: Optional[str]
    is_premium: bool
    created_at: datetime


# ============================================
# DEPENDÊNCIA: USUÁRIO AUTENTICADO
# ============================================

async def get_current_user(
    authorization: str = Header(..., description="Bearer token")
) -> dict:
    """
    Dependência que extrai e valida o usuário do token JWT
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token expirado ou inválido")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")

    return {
        "user_id": payload["sub"],
        "email": payload["email"]
    }


# ============================================
# ROTAS
# ============================================

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Database = Depends(get_db)):
    """
    Registra novo usuário
    """
    # Verifica aceite de termos
    if not request.accepted_terms:
        raise HTTPException(
            status_code=400,
            detail="Você deve aceitar os Termos de Uso e a Política de Privacidade"
        )

    # Verifica se email já existe
    existing = await db.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Valida senha
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 8 caracteres")

    # Cria usuário com aceite de termos
    password_hash = hash_password(request.password)
    user = await db.create_user(
        email=request.email,
        password_hash=password_hash,
        nome=request.nome,
        accepted_terms=request.accepted_terms
    )

    # Cria perfil inicial vazio
    await db.create_user_profile(user_id=user["id"], nome=request.nome)

    # Gera tokens
    access_token = create_access_token(user["id"], user["email"])
    refresh_token = create_refresh_token(user["id"])

    # Log de auditoria
    await db.log_audit(
        user_id=user["id"],
        action="register",
        details={"email": request.email, "accepted_terms": True}
    )

    # Envia email de boas-vindas (async, nao bloqueia)
    try:
        nome = request.nome or request.email.split("@")[0]
        await email_service.send_welcome_email(request.email, nome)
    except Exception as e:
        print(f"[AUTH] Erro ao enviar email de boas-vindas: {e}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Database = Depends(get_db)):
    """
    Login de usuário existente
    """
    # Busca usuário
    user = await db.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    # Verifica senha
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    # Verifica se conta está ativa
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Conta desativada")

    # Atualiza último login
    await db.update_last_login(user["id"])

    # Gera tokens
    access_token = create_access_token(user["id"], user["email"])
    refresh_token = create_refresh_token(user["id"])

    # Log de auditoria
    await db.log_audit(
        user_id=user["id"],
        action="login",
        details={}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: Database = Depends(get_db)):
    """
    Renova tokens usando refresh token
    """
    payload = verify_token(request.refresh_token)

    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")

    # Busca usuário
    user = await db.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    # Gera novos tokens
    access_token = create_access_token(user["id"], user["email"])
    new_refresh_token = create_refresh_token(user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    """
    Retorna dados do usuário logado
    """
    user = await db.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    profile = await db.get_user_profile(current_user["user_id"])

    return UserResponse(
        id=str(user["id"]),
        email=user["email"],
        nome=profile.get("nome") if profile else None,
        is_premium=user.get("is_premium", False),
        created_at=user["created_at"]
    )


@router.post("/password-reset")
async def request_password_reset(request: PasswordResetRequest, db: Database = Depends(get_db)):
    """
    Solicita reset de senha (envia email)
    """
    print(f"[AUTH] Password reset solicitado para: {request.email}")
    user = await db.get_user_by_email(request.email)
    print(f"[AUTH] Usuario encontrado: {user is not None}")
    if user:
        print(f"[AUTH] Usuario ID: {user.get('id')}, Email no DB: {user.get('email')}")

    # Sempre retorna sucesso para nao revelar se email existe
    if user:
        token = generate_secure_token()
        await db.save_password_reset_token(user["id"], token)

        # Buscar nome do usuario
        profile = await db.get_user_profile(user["id"])
        nome = profile.get("nome") if profile else request.email.split("@")[0]

        # Enviar email
        try:
            result = await email_service.send_password_reset_email(request.email, nome, token)
            if result:
                print(f"[AUTH] Email de reset enviado com sucesso para {request.email}")
            else:
                print(f"[AUTH] Falha ao enviar email de reset para {request.email}")
        except Exception as e:
            print(f"[AUTH] Erro ao enviar email de reset: {e}")

    return {"message": "Se o email existir, voce recebera instrucoes para resetar a senha"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm, db: Database = Depends(get_db)):
    """
    Confirma reset de senha com token
    """
    # Verificar token
    token_data = await db.verify_password_reset_token(request.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Token invalido ou expirado")

    # Validar nova senha
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 8 caracteres")

    # Atualizar senha
    password_hash = hash_password(request.new_password)
    await db.update_user_password(token_data["user_id"], password_hash)

    # Marcar token como usado
    await db.use_password_reset_token(request.token)

    # Log de auditoria
    await db.log_audit(
        user_id=token_data["user_id"],
        action="password_reset",
        details={"method": "email_token"}
    )

    return {"message": "Senha alterada com sucesso"}


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    """
    Logout (invalida sessão no log)
    """
    await db.log_audit(
        user_id=current_user["user_id"],
        action="logout",
        details={}
    )

    return {"message": "Logout realizado com sucesso"}


# ============================================
# OAUTH - GOOGLE
# ============================================

@router.get("/google")
async def google_login():
    """
    Inicia fluxo OAuth com Google
    Redireciona para página de login do Google
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=501,
            detail="Login com Google não configurado. Configure GOOGLE_CLIENT_ID no .env"
        )

    # Gerar state para segurança CSRF
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "google", "timestamp": datetime.now()}

    # Construir URL de autorização do Google
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    db: Database = Depends(get_db)
):
    """
    Callback do Google OAuth
    Recebe código de autorização e troca por tokens
    """
    # Verificar erros
    if error:
        return RedirectResponse(url=f"/app?error={error}")

    if not code or not state:
        return RedirectResponse(url="/app?error=missing_params")

    # Verificar state (proteção CSRF)
    if state not in oauth_states:
        return RedirectResponse(url="/app?error=invalid_state")

    del oauth_states[state]

    try:
        # Trocar código por tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GOOGLE_REDIRECT_URI
                }
            )

            if token_response.status_code != 200:
                return RedirectResponse(url="/app?error=token_exchange_failed")

            tokens = token_response.json()
            access_token = tokens.get("access_token")

            # Buscar informações do usuário
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if user_response.status_code != 200:
                return RedirectResponse(url="/app?error=user_info_failed")

            user_info = user_response.json()

        # Extrair dados do usuário
        email = user_info.get("email")
        nome = user_info.get("name")
        google_id = user_info.get("id")
        picture = user_info.get("picture")

        if not email:
            return RedirectResponse(url="/app?error=no_email")

        # Verificar se usuário já existe
        user = await db.get_user_by_email(email)

        if user:
            # Usuário existe - fazer login
            await db.update_last_login(user["id"])
        else:
            # Criar novo usuário (OAuth implica aceite dos termos)
            user = await db.create_user(
                email=email,
                password_hash=None,  # Sem senha (OAuth)
                nome=nome,
                oauth_provider="google",
                oauth_id=google_id,
                accepted_terms=True  # OAuth requer aceite prévio
            )
            # Criar perfil
            await db.create_user_profile(user_id=user["id"], nome=nome)

        # Gerar tokens JWT
        jwt_access = create_access_token(user["id"], email)
        jwt_refresh = create_refresh_token(user["id"])

        # Log de auditoria
        await db.log_audit(
            user_id=user["id"],
            action="oauth_login",
            details={"provider": "google", "accepted_terms": True}
        )

        # Redirecionar para o app com tokens
        redirect_url = f"/app?token={jwt_access}&refresh={jwt_refresh}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        print(f"Google OAuth error: {e}")
        return RedirectResponse(url="/app?error=oauth_failed")


# ============================================
# OAUTH - APPLE
# ============================================

@router.get("/apple")
async def apple_login():
    """
    Inicia fluxo OAuth com Apple
    """
    if not APPLE_CLIENT_ID:
        raise HTTPException(
            status_code=501,
            detail="Login com Apple não configurado. Configure APPLE_CLIENT_ID no .env"
        )

    # Gerar state para segurança CSRF
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "apple", "timestamp": datetime.now()}

    # Construir URL de autorização da Apple
    params = {
        "client_id": APPLE_CLIENT_ID,
        "redirect_uri": APPLE_REDIRECT_URI,
        "response_type": "code id_token",
        "response_mode": "form_post",
        "scope": "name email",
        "state": state
    }

    auth_url = f"https://appleid.apple.com/auth/authorize?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.post("/apple/callback")
async def apple_callback(
    code: str = None,
    state: str = None,
    id_token: str = None,
    user: str = None,  # JSON string com nome do usuário (apenas primeiro login)
    error: str = None,
    db: Database = Depends(get_db)
):
    """
    Callback do Apple OAuth (POST porque Apple usa form_post)
    """
    import json
    import jwt

    if error:
        return RedirectResponse(url=f"/app?error={error}")

    if not code or not state:
        return RedirectResponse(url="/app?error=missing_params")

    # Verificar state
    if state not in oauth_states:
        return RedirectResponse(url="/app?error=invalid_state")

    del oauth_states[state]

    try:
        # Decodificar id_token para obter email (sem verificar assinatura por enquanto)
        # Em produção, deve-se verificar a assinatura com as chaves públicas da Apple
        if id_token:
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            email = decoded.get("email")
            apple_id = decoded.get("sub")
        else:
            return RedirectResponse(url="/app?error=no_id_token")

        # Extrair nome do usuário (só vem no primeiro login)
        nome = None
        if user:
            try:
                user_data = json.loads(user)
                first_name = user_data.get("name", {}).get("firstName", "")
                last_name = user_data.get("name", {}).get("lastName", "")
                nome = f"{first_name} {last_name}".strip() or None
            except:
                pass

        if not email:
            return RedirectResponse(url="/app?error=no_email")

        # Verificar se usuário já existe
        existing_user = await db.get_user_by_email(email)

        if existing_user:
            # Usuário existe - fazer login
            await db.update_last_login(existing_user["id"])
            user_record = existing_user
        else:
            # Criar novo usuário (OAuth implica aceite dos termos)
            user_record = await db.create_user(
                email=email,
                password_hash=None,
                nome=nome,
                oauth_provider="apple",
                oauth_id=apple_id,
                accepted_terms=True  # OAuth requer aceite prévio
            )
            await db.create_user_profile(user_id=user_record["id"], nome=nome)

        # Gerar tokens JWT
        jwt_access = create_access_token(user_record["id"], email)
        jwt_refresh = create_refresh_token(user_record["id"])

        # Log de auditoria
        await db.log_audit(
            user_id=user_record["id"],
            action="oauth_login",
            details={"provider": "apple", "accepted_terms": True}
        )

        # Redirecionar para o app com tokens
        redirect_url = f"/app?token={jwt_access}&refresh={jwt_refresh}"
        return RedirectResponse(url=redirect_url, status_code=303)

    except Exception as e:
        print(f"Apple OAuth error: {e}")
        return RedirectResponse(url="/app?error=oauth_failed")


# ============================================
# OAUTH - STATUS
# ============================================

@router.get("/oauth/providers")
async def get_oauth_providers():
    """
    Retorna quais provedores OAuth estão configurados
    """
    return {
        "google": bool(GOOGLE_CLIENT_ID),
        "apple": bool(APPLE_CLIENT_ID)
    }

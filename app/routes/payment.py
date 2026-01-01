"""
SoulHaven - Rotas de Pagamento (Stripe)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import stripe

from app.auth import get_current_user
from app.database import get_db, Database
from app.config import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    STRIPE_PRICE_ID,
    SUBSCRIPTION_PRICE_USD
)

router = APIRouter(prefix="/payment", tags=["Payment"])

# ============================================
# MODO BETA - Ativar premium sem pagamento
# Mudar para False quando for para produção
# ============================================
BETA_MODE = False

# Configurar Stripe
stripe.api_key = STRIPE_SECRET_KEY


# ============================================
# MODELOS
# ============================================

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    portal_url: str


class SubscriptionStatus(BaseModel):
    is_premium: bool
    subscription_id: Optional[str] = None
    status: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False


# ============================================
# ROTAS
# ============================================

@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Cria sessão de checkout do Stripe para assinatura premium
    Em modo BETA, ativa premium diretamente sem pagamento
    """
    user_id = current_user["user_id"]

    # Buscar usuário
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verificar se já é premium
    if user.get("is_premium"):
        raise HTTPException(status_code=400, detail="Você já é assinante premium!")

    # Determinar URL base
    origin = request.headers.get("origin", "http://localhost:8000")

    # ============================================
    # MODO BETA: Ativar premium sem pagamento
    # ============================================
    if BETA_MODE:
        async with db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET
                    is_premium = TRUE,
                    subscription_status = 'beta_active',
                    subscription_start_date = NOW(),
                    cancel_at_period_end = FALSE,
                    trial_messages_used = 0
                WHERE id = $1
            """, user_id)

        # Log de auditoria
        await db.log_audit(
            user_id=user_id,
            action="beta_premium_activated",
            details={"mode": "beta_test"}
        )

        # Retornar URL de sucesso diretamente (sem passar pelo Stripe)
        return CheckoutResponse(
            checkout_url=f"{origin}/app?payment=success&beta=true",
            session_id="beta_mode_no_payment"
        )

    # ============================================
    # MODO PRODUÇÃO: Usar Stripe normalmente
    # ============================================
    try:
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=user["email"],
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url=f"{origin}/?payment=success",
            cancel_url=f"{origin}/?payment=cancelled",
            metadata={
                "user_id": user_id,
                "email": user["email"]
            },
            subscription_data={
                "metadata": {
                    "user_id": user_id
                }
            }
        )

        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Retorna status da assinatura do usuário
    """
    user_id = current_user["user_id"]
    user = await db.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return SubscriptionStatus(
        is_premium=user.get("is_premium", False),
        subscription_id=user.get("stripe_subscription_id"),
        status=user.get("subscription_status"),
        current_period_end=user.get("subscription_end_date"),
        cancel_at_period_end=user.get("cancel_at_period_end", False)
    )


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Cria sessao do Customer Portal do Stripe para gerenciar assinatura
    """
    user_id = current_user["user_id"]
    user = await db.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    # Verificar se tem customer_id do Stripe
    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura encontrada")

    # URL de retorno
    from app.config import APP_URL
    return_url = f"{APP_URL}/app"

    try:
        # Criar sessao do portal
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )

        return PortalResponse(portal_url=portal_session.url)

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Cancela assinatura (ao final do período)
    """
    user_id = current_user["user_id"]
    user = await db.get_user_by_id(user_id)

    if not user or not user.get("stripe_subscription_id"):
        raise HTTPException(status_code=400, detail="Nenhuma assinatura ativa encontrada")

    try:
        # Cancelar ao final do período (não imediatamente)
        stripe.Subscription.modify(
            user["stripe_subscription_id"],
            cancel_at_period_end=True
        )

        # Atualizar no banco
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET cancel_at_period_end = TRUE WHERE id = $1",
                user["id"]
            )

        return {"message": "Assinatura será cancelada ao final do período atual"}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reactivate")
async def reactivate_subscription(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Reativa assinatura que estava programada para cancelar
    """
    user_id = current_user["user_id"]
    user = await db.get_user_by_id(user_id)

    if not user or not user.get("stripe_subscription_id"):
        raise HTTPException(status_code=400, detail="Nenhuma assinatura encontrada")

    try:
        stripe.Subscription.modify(
            user["stripe_subscription_id"],
            cancel_at_period_end=False
        )

        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET cancel_at_period_end = FALSE WHERE id = $1",
                user["id"]
            )

        return {"message": "Assinatura reativada com sucesso!"}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Database = Depends(get_db)
):
    """
    Webhook para eventos do Stripe
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Processar eventos
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        # Pagamento inicial concluído
        await handle_checkout_completed(db, data)

    elif event_type == "customer.subscription.updated":
        # Assinatura atualizada
        await handle_subscription_updated(db, data)

    elif event_type == "customer.subscription.deleted":
        # Assinatura cancelada/expirada
        await handle_subscription_deleted(db, data)

    elif event_type == "invoice.payment_failed":
        # Pagamento falhou
        await handle_payment_failed(db, data)

    return {"received": True}


# ============================================
# HANDLERS DE WEBHOOK
# ============================================

async def handle_checkout_completed(db: Database, session: dict):
    """
    Processa checkout concluído - ativa premium
    """
    user_id = session.get("metadata", {}).get("user_id")
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")

    if not user_id:
        return

    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET
                is_premium = TRUE,
                stripe_customer_id = $2,
                stripe_subscription_id = $3,
                subscription_status = 'active',
                subscription_start_date = NOW(),
                cancel_at_period_end = FALSE
            WHERE id = $1
        """, user_id, customer_id, subscription_id)

        # Log de auditoria
        await db.log_audit(
            user_id=user_id,
            action="subscription_created",
            details={"subscription_id": subscription_id}
        )


async def handle_subscription_updated(db: Database, subscription: dict):
    """
    Processa atualização de assinatura
    """
    subscription_id = subscription.get("id")
    status = subscription.get("status")
    cancel_at_period_end = subscription.get("cancel_at_period_end", False)
    current_period_end = subscription.get("current_period_end")

    async with db.pool.acquire() as conn:
        # Buscar usuário pela subscription_id
        user = await conn.fetchrow(
            "SELECT id FROM users WHERE stripe_subscription_id = $1",
            subscription_id
        )

        if user:
            # Determinar se ainda é premium
            is_premium = status in ["active", "trialing", "past_due"]

            await conn.execute("""
                UPDATE users SET
                    subscription_status = $2,
                    is_premium = $3,
                    cancel_at_period_end = $4,
                    subscription_end_date = to_timestamp($5)
                WHERE id = $1
            """, user["id"], status, is_premium, cancel_at_period_end, current_period_end)


async def handle_subscription_deleted(db: Database, subscription: dict):
    """
    Processa cancelamento/expiração de assinatura
    """
    subscription_id = subscription.get("id")

    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id FROM users WHERE stripe_subscription_id = $1",
            subscription_id
        )

        if user:
            await conn.execute("""
                UPDATE users SET
                    is_premium = FALSE,
                    subscription_status = 'cancelled'
                WHERE id = $1
            """, user["id"])

            await db.log_audit(
                user_id=str(user["id"]),
                action="subscription_cancelled",
                details={"subscription_id": subscription_id}
            )


async def handle_payment_failed(db: Database, invoice: dict):
    """
    Processa falha de pagamento
    """
    subscription_id = invoice.get("subscription")

    if subscription_id:
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id FROM users WHERE stripe_subscription_id = $1",
                subscription_id
            )

            if user:
                await conn.execute("""
                    UPDATE users SET
                        subscription_status = 'past_due'
                    WHERE id = $1
                """, user["id"])

"""
SoulHaven - Push Notifications API
Endpoints para gerenciar push notifications
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from pywebpush import webpush, WebPushException

from app.database import Database, get_db
from app.auth import get_current_user
from app.config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS_EMAIL


router = APIRouter(prefix="/api/push", tags=["Push Notifications"])


# ============================================
# SCHEMAS
# ============================================

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # {p256dh: str, auth: str}


class NotificationPreferences(BaseModel):
    push_enabled: Optional[bool] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None  # HH:MM format
    reminder_days: Optional[List[str]] = None  # ["mon", "tue", ...]
    engagement_enabled: Optional[bool] = None
    engagement_after_days: Optional[int] = None
    marketing_enabled: Optional[bool] = None
    timezone: Optional[str] = None


# ============================================
# HELPER FUNCTIONS
# ============================================

async def send_push_notification(
    subscription_info: dict,
    title: str,
    body: str,
    icon: str = "/static/icons/icon-192x192.png",
    url: str = "/",
    tag: str = None,
    db: Database = None,
    user_id: str = None,
    notification_type: str = "general"
) -> bool:
    """
    Envia uma push notification para um dispositivo.
    Retorna True se sucesso, False se falha.
    """
    try:
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": icon,
            "url": url,
            "tag": tag or notification_type,
            "timestamp": None  # Will be set by service worker
        })

        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": f"mailto:{VAPID_CLAIMS_EMAIL}"
            }
        )

        # Log success
        if db and user_id:
            await db.log_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                success=True
            )

        return True

    except WebPushException as e:
        print(f"[PUSH] Error sending notification: {e}")

        # Se subscription expirou ou foi revogada, desativar
        if e.response and e.response.status_code in (404, 410):
            if db:
                await db.deactivate_push_subscription(subscription_info.get("endpoint", ""))

        # Log failure
        if db and user_id:
            await db.log_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                success=False,
                error_message=str(e)
            )

        return False

    except Exception as e:
        print(f"[PUSH] Unexpected error: {e}")
        return False


async def send_push_to_user(
    user_id: str,
    title: str,
    body: str,
    icon: str = "/static/icons/icon-192x192.png",
    url: str = "/"
) -> bool:
    """
    Envia push notification para todos os dispositivos de um usuário.
    Usado pelo sistema de notificações do admin.
    """
    from app.database import get_db_pool

    try:
        pool = await get_db_pool()

        # Buscar todas as subscriptions ativas do usuário
        subscriptions = await pool.fetch(
            """
            SELECT endpoint, p256dh, auth
            FROM push_subscriptions
            WHERE user_id = $1 AND is_active = TRUE
            """,
            user_id if isinstance(user_id, str) else str(user_id)
        )

        if not subscriptions:
            print(f"[PUSH] Nenhuma subscription encontrada para user {user_id}")
            return False

        success = False
        for sub in subscriptions:
            subscription_info = {
                "endpoint": sub["endpoint"],
                "keys": {
                    "p256dh": sub["p256dh"],
                    "auth": sub["auth"]
                }
            }

            result = await send_push_notification(
                subscription_info=subscription_info,
                title=title,
                body=body,
                icon=icon,
                url=url,
                notification_type="admin_broadcast"
            )

            if result:
                success = True

        return success

    except Exception as e:
        print(f"[PUSH] Erro ao enviar push para user {user_id}: {e}")
        return False


# ============================================
# PUBLIC ENDPOINTS
# ============================================

@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Retorna a chave pública VAPID para o frontend"""
    return {"publicKey": VAPID_PUBLIC_KEY}


@router.post("/subscribe")
async def subscribe_to_push(
    subscription: PushSubscription,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Registra subscription de push do usuário"""
    try:
        result = await db.save_push_subscription(
            user_id=str(user["id"]),
            endpoint=subscription.endpoint,
            p256dh=subscription.keys.get("p256dh", ""),
            auth=subscription.keys.get("auth", ""),
            user_agent=None  # Could be extracted from request headers
        )

        # Criar preferências default se não existirem
        prefs = await db.get_user_notification_preferences(str(user["id"]))
        if not prefs:
            await db.save_user_notification_preferences(
                user_id=str(user["id"]),
                preferences={
                    "push_enabled": True,
                    "reminder_enabled": True,
                    "engagement_enabled": True
                }
            )

        return {"success": True, "message": "Subscription registrada com sucesso"}

    except Exception as e:
        print(f"[PUSH] Error saving subscription: {e}")
        raise HTTPException(status_code=500, detail="Erro ao registrar subscription")


@router.delete("/unsubscribe")
async def unsubscribe_from_push(
    endpoint: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Remove subscription de push do usuário"""
    try:
        await db.delete_push_subscription(
            user_id=str(user["id"]),
            endpoint=endpoint
        )
        return {"success": True, "message": "Subscription removida"}

    except Exception as e:
        print(f"[PUSH] Error removing subscription: {e}")
        raise HTTPException(status_code=500, detail="Erro ao remover subscription")


@router.get("/preferences")
async def get_notification_preferences(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Busca preferências de notificação do usuário"""
    prefs = await db.get_user_notification_preferences(str(user["id"]))
    if not prefs:
        return {
            "push_enabled": True,
            "reminder_enabled": True,
            "reminder_time": "09:00",
            "reminder_days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            "engagement_enabled": True,
            "engagement_after_days": 3,
            "marketing_enabled": False,
            "timezone": "America/Sao_Paulo"
        }

    # Format time for frontend
    if prefs.get("reminder_time"):
        prefs["reminder_time"] = str(prefs["reminder_time"])[:5]  # HH:MM

    return prefs


@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferences,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Atualiza preferências de notificação do usuário"""
    try:
        prefs_dict = preferences.dict(exclude_none=True)
        await db.save_user_notification_preferences(
            user_id=str(user["id"]),
            preferences=prefs_dict
        )
        return {"success": True, "message": "Preferencias atualizadas"}

    except Exception as e:
        print(f"[PUSH] Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar preferencias")


@router.post("/test")
async def send_test_notification(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Envia notificação de teste para o usuário"""
    subscriptions = await db.get_user_push_subscriptions(str(user["id"]))

    if not subscriptions:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma subscription encontrada. Ative as notificacoes primeiro."
        )

    success_count = 0
    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub["endpoint"],
            "keys": {
                "p256dh": sub["p256dh"],
                "auth": sub["auth"]
            }
        }

        success = await send_push_notification(
            subscription_info=subscription_info,
            title="SoulHaven - Teste",
            body="Suas notificacoes estao funcionando! Deus abencoe seu dia.",
            db=db,
            user_id=str(user["id"]),
            notification_type="test"
        )

        if success:
            success_count += 1

    if success_count > 0:
        return {"success": True, "message": f"Notificacao enviada para {success_count} dispositivo(s)"}
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar notificacao")

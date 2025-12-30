"""
SoulHaven - Sistema de Notificações
Gerenciamento de notificações push e email para usuários
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from uuid import UUID

from app.auth import get_current_user
from app.database import get_db, Database
from app.config import ADMIN_EMAILS
from app.email_service import email_service
from app.routes.push import send_push_to_user

router = APIRouter(prefix="/notifications", tags=["Notificações"])


# ============================================
# MODELOS
# ============================================

class NotificationCreate(BaseModel):
    title: str
    message: str
    send_push: bool = True
    send_email: bool = True
    target_audience: str = "all"  # all, premium, free, specific
    specific_users: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    send_push: bool
    send_email: bool
    target_audience: str
    status: str
    total_recipients: int
    sent_count: int
    failed_count: int
    created_at: str
    scheduled_at: Optional[str]
    sent_at: Optional[str]


# ============================================
# MIDDLEWARE - VERIFICAR ADMIN
# ============================================

async def verify_admin(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Verifica se o usuário é admin"""
    user_id = current_user["user_id"]
    user = await db.get_user_by_id(user_id)

    if not user or user.get("email") not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas administradores."
        )

    return current_user


# ============================================
# ROTAS - CRIAR E LISTAR NOTIFICAÇÕES
# ============================================

@router.post("/send")
async def send_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Criar e enviar uma nova notificação"""

    async with db.pool.acquire() as conn:
        # Criar registro da notificação
        row = await conn.fetchrow(
            """
            INSERT INTO notifications (
                title, message, send_push, send_email,
                target_audience, status, created_by,
                scheduled_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            notification.title,
            notification.message,
            notification.send_push,
            notification.send_email,
            notification.target_audience,
            "pending" if notification.scheduled_at else "sending",
            UUID(admin["user_id"]),
            notification.scheduled_at
        )

        notification_id = row["id"]

        # Se tem agendamento, apenas salva
        if notification.scheduled_at:
            return {
                "message": "Notificação agendada com sucesso",
                "notification_id": str(notification_id),
                "scheduled_at": notification.scheduled_at.isoformat()
            }

        # Buscar destinatários com base no público-alvo
        if notification.target_audience == "all":
            users = await conn.fetch(
                """
                SELECT u.id, u.email, up.nome, up.push_notifications, up.email_notifications
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE u.is_active = TRUE
                """
            )
        elif notification.target_audience == "premium":
            users = await conn.fetch(
                """
                SELECT u.id, u.email, up.nome, up.push_notifications, up.email_notifications
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE u.is_active = TRUE AND u.is_premium = TRUE
                """
            )
        elif notification.target_audience == "free":
            users = await conn.fetch(
                """
                SELECT u.id, u.email, up.nome, up.push_notifications, up.email_notifications
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE u.is_active = TRUE AND u.is_premium = FALSE
                """
            )
        elif notification.target_audience == "specific" and notification.specific_users:
            user_ids = [UUID(uid) for uid in notification.specific_users]
            users = await conn.fetch(
                """
                SELECT u.id, u.email, up.nome, up.push_notifications, up.email_notifications
                FROM users u
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE u.id = ANY($1) AND u.is_active = TRUE
                """,
                user_ids
            )
        else:
            users = []

        # Atualizar total de destinatários
        await conn.execute(
            "UPDATE notifications SET total_recipients = $1 WHERE id = $2",
            len(users), notification_id
        )

        # Criar registros de entrega para cada usuário
        for user in users:
            # Registrar para push se habilitado
            if notification.send_push and user.get("push_notifications", True):
                await conn.execute(
                    """
                    INSERT INTO notification_deliveries
                    (notification_id, user_id, channel, status)
                    VALUES ($1, $2, 'push', 'pending')
                    """,
                    notification_id, user["id"]
                )

            # Registrar para email se habilitado
            if notification.send_email and user.get("email_notifications", True):
                await conn.execute(
                    """
                    INSERT INTO notification_deliveries
                    (notification_id, user_id, channel, status)
                    VALUES ($1, $2, 'email', 'pending')
                    """,
                    notification_id, user["id"]
                )

    # Enviar em background
    background_tasks.add_task(
        process_notification_delivery,
        str(notification_id),
        notification.title,
        notification.message,
        notification.send_push,
        notification.send_email,
        users
    )

    return {
        "message": "Notificação sendo enviada",
        "notification_id": str(notification_id),
        "total_recipients": len(users)
    }


async def process_notification_delivery(
    notification_id: str,
    title: str,
    message: str,
    send_push: bool,
    send_email: bool,
    users: list
):
    """Processa o envio das notificações em background"""
    from app.database import get_db_pool

    pool = await get_db_pool()
    sent_count = 0
    failed_count = 0

    for user in users:
        user_id = str(user["id"])
        email = user["email"]
        nome = user.get("nome") or email.split("@")[0]

        # Enviar Push
        if send_push and user.get("push_notifications", True):
            try:
                success = await send_push_to_user(user_id, title, message)
                status = "sent" if success else "failed"

                await pool.execute(
                    """
                    UPDATE notification_deliveries
                    SET status = $1, sent_at = NOW()
                    WHERE notification_id = $2 AND user_id = $3 AND channel = 'push'
                    """,
                    status, UUID(notification_id), user["id"]
                )

                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"[NOTIFICATION] Erro ao enviar push para {email}: {e}")
                failed_count += 1

        # Enviar Email
        if send_email and user.get("email_notifications", True):
            try:
                success = await email_service.send_notification_email(
                    to=email,
                    nome=nome,
                    title=title,
                    message=message
                )
                status = "sent" if success else "failed"

                await pool.execute(
                    """
                    UPDATE notification_deliveries
                    SET status = $1, sent_at = NOW()
                    WHERE notification_id = $2 AND user_id = $3 AND channel = 'email'
                    """,
                    status, UUID(notification_id), user["id"]
                )

                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"[NOTIFICATION] Erro ao enviar email para {email}: {e}")
                failed_count += 1

    # Atualizar status da notificação
    await pool.execute(
        """
        UPDATE notifications
        SET status = 'sent', sent_at = NOW(),
            sent_count = $1, failed_count = $2
        WHERE id = $3
        """,
        sent_count, failed_count, UUID(notification_id)
    )

    print(f"[NOTIFICATION] Envio concluído: {sent_count} enviados, {failed_count} falhas")


@router.get("/list")
async def list_notifications(
    limit: int = 50,
    offset: int = 0,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Lista todas as notificações enviadas"""

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, message, send_push, send_email,
                   target_audience, status, total_recipients,
                   sent_count, failed_count, created_at,
                   scheduled_at, sent_at
            FROM notifications
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset
        )

    return [
        {
            "id": str(row["id"]),
            "title": row["title"],
            "message": row["message"],
            "send_push": row["send_push"],
            "send_email": row["send_email"],
            "target_audience": row["target_audience"],
            "status": row["status"],
            "total_recipients": row["total_recipients"] or 0,
            "sent_count": row["sent_count"] or 0,
            "failed_count": row["failed_count"] or 0,
            "created_at": row["created_at"].isoformat(),
            "scheduled_at": row["scheduled_at"].isoformat() if row["scheduled_at"] else None,
            "sent_at": row["sent_at"].isoformat() if row["sent_at"] else None
        }
        for row in rows
    ]


@router.get("/stats")
async def get_notification_stats(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Estatísticas de notificações"""

    async with db.pool.acquire() as conn:
        # Total de notificações
        total = await conn.fetchval("SELECT COUNT(*) FROM notifications")

        # Enviadas com sucesso
        sent = await conn.fetchval(
            "SELECT COUNT(*) FROM notifications WHERE status = 'sent'"
        )

        # Total de entregas
        total_deliveries = await conn.fetchval(
            "SELECT COUNT(*) FROM notification_deliveries WHERE status = 'sent'"
        )

        # Falhas
        failed_deliveries = await conn.fetchval(
            "SELECT COUNT(*) FROM notification_deliveries WHERE status = 'failed'"
        )

        # Usuários com push REGISTRADO (têm subscription ativa)
        push_registered = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT user_id) FROM push_subscriptions
            WHERE is_active = TRUE
            """
        )

        # Usuários com email habilitado
        email_enabled = await conn.fetchval(
            """
            SELECT COUNT(*) FROM user_profiles
            WHERE email_notifications = TRUE OR email_notifications IS NULL
            """
        )

    return {
        "total_notifications": total or 0,
        "sent_notifications": sent or 0,
        "total_deliveries": total_deliveries or 0,
        "failed_deliveries": failed_deliveries or 0,
        "users_push_registered": push_registered or 0,
        "users_email_enabled": email_enabled or 0
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Excluir uma notificação (apenas pendentes/agendadas)"""

    async with db.pool.acquire() as conn:
        # Verificar se pode ser excluída
        notification = await conn.fetchrow(
            "SELECT status FROM notifications WHERE id = $1",
            UUID(notification_id)
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")

        if notification["status"] not in ["pending", "scheduled"]:
            raise HTTPException(
                status_code=400,
                detail="Apenas notificações pendentes podem ser excluídas"
            )

        # Excluir entregas
        await conn.execute(
            "DELETE FROM notification_deliveries WHERE notification_id = $1",
            UUID(notification_id)
        )

        # Excluir notificação
        await conn.execute(
            "DELETE FROM notifications WHERE id = $1",
            UUID(notification_id)
        )

    return {"message": "Notificação excluída"}


@router.get("/users-preview")
async def preview_recipients(
    target_audience: str = "all",
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Preview de quantos usuários receberão a notificação"""

    async with db.pool.acquire() as conn:
        # Base query filter
        if target_audience == "all":
            user_filter = "u.is_active = TRUE"
        elif target_audience == "premium":
            user_filter = "u.is_active = TRUE AND u.is_premium = TRUE"
        elif target_audience == "free":
            user_filter = "u.is_active = TRUE AND u.is_premium = FALSE"
        else:
            return {"total_users": 0, "push_enabled": 0, "push_registered": 0, "email_enabled": 0}

        # Total de usuários
        total = await conn.fetchval(f"SELECT COUNT(*) FROM users u WHERE {user_filter}")

        # Usuários com preferência de push habilitada
        push_enabled = await conn.fetchval(f"""
            SELECT COUNT(*) FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE {user_filter}
            AND (up.push_notifications = TRUE OR up.push_notifications IS NULL)
        """)

        # Usuários com push subscription REGISTRADA (estes vão receber de fato)
        push_registered = await conn.fetchval(f"""
            SELECT COUNT(DISTINCT u.id) FROM users u
            INNER JOIN push_subscriptions ps ON u.id = ps.user_id AND ps.is_active = TRUE
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE {user_filter}
            AND (up.push_notifications = TRUE OR up.push_notifications IS NULL)
        """)

        # Usuários com email habilitado
        email_enabled = await conn.fetchval(f"""
            SELECT COUNT(*) FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE {user_filter}
            AND (up.email_notifications = TRUE OR up.email_notifications IS NULL)
        """)

    return {
        "total_users": total or 0,
        "push_enabled": push_enabled or 0,
        "push_registered": push_registered or 0,
        "email_enabled": email_enabled or 0
    }

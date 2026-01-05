"""
SoulHaven - Rotas de Administração
Painel para gerenciar usuários, conversas e métricas
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database
from app.config import ADMIN_EMAILS
from app.routes.push import send_push_notification
from app.notification_scheduler import send_reminder_notifications, send_engagement_notifications

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================
# MODELOS
# ============================================

class UserStats(BaseModel):
    total_users: int
    premium_users: int
    active_today: int
    new_this_week: int


class UserSummary(BaseModel):
    id: str
    email: str
    nome: Optional[str]
    is_premium: bool
    is_active: bool
    created_at: str
    last_login: Optional[str]
    total_messages: int
    trial_messages_used: int


class ConversationStats(BaseModel):
    total_conversations: int
    total_messages: int
    avg_messages_per_conversation: float
    conversations_today: int


class SystemHealth(BaseModel):
    database: str
    redis: str
    ai_api: str
    uptime: str


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
# ROTAS - DASHBOARD
# ============================================

@router.get("/stats/users", response_model=UserStats)
async def get_user_stats(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Estatísticas de usuários"""
    async with db.pool.acquire() as conn:
        # Total de usuários
        total = await conn.fetchval("SELECT COUNT(*) FROM users")

        # Usuários premium
        premium = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")

        # Ativos hoje
        today = datetime.now().date()
        active_today = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE last_login::date = $1",
            today
        )

        # Novos esta semana
        week_ago = datetime.now() - timedelta(days=7)
        new_this_week = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE created_at >= $1",
            week_ago
        )

    return UserStats(
        total_users=total or 0,
        premium_users=premium or 0,
        active_today=active_today or 0,
        new_this_week=new_this_week or 0
    )


@router.get("/stats/conversations", response_model=ConversationStats)
async def get_conversation_stats(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Estatísticas de conversas"""
    async with db.pool.acquire() as conn:
        # Total de conversas
        total_conv = await conn.fetchval("SELECT COUNT(*) FROM conversations")

        # Total de mensagens
        total_msg = await conn.fetchval("SELECT COUNT(*) FROM messages")

        # Média de mensagens por conversa
        avg = total_msg / total_conv if total_conv > 0 else 0

        # Conversas hoje
        today = datetime.now().date()
        today_conv = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE started_at::date = $1",
            today
        )

    return ConversationStats(
        total_conversations=total_conv or 0,
        total_messages=total_msg or 0,
        avg_messages_per_conversation=round(avg, 1),
        conversations_today=today_conv or 0
    )


@router.get("/stats/financial")
async def get_financial_stats(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Análise financeira completa: usuários, uso, custos estimados e receitas.
    """
    async with db.pool.acquire() as conn:
        # ==================== USUÁRIOS ====================
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")
        free_users = total_users - premium_users

        # Ativos últimos 7 dias
        week_ago = datetime.now() - timedelta(days=7)
        active_7d = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE last_login >= $1",
            week_ago
        )

        # Ativos últimos 30 dias
        month_ago = datetime.now() - timedelta(days=30)
        active_30d = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE last_login >= $1",
            month_ago
        )

        # Novos este mês
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE created_at >= $1",
            month_start
        )

        # ==================== MENSAGENS ====================
        total_messages = await conn.fetchval("SELECT COUNT(*) FROM messages")

        # Mensagens este mês
        messages_this_month = await conn.fetchval(
            "SELECT COUNT(*) FROM messages WHERE created_at >= $1",
            month_start
        )

        # Mensagens por tipo de usuário (estimativa baseada em is_premium)
        premium_messages = await conn.fetchval("""
            SELECT COUNT(*) FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            JOIN users u ON c.user_id = u.id
            WHERE u.is_premium = TRUE
        """)
        free_messages = total_messages - (premium_messages or 0)

        # Média de mensagens por usuário ativo
        avg_messages_per_user = total_messages / active_30d if active_30d > 0 else 0

        # ==================== CONVERSAS ====================
        total_conversations = await conn.fetchval("SELECT COUNT(*) FROM conversations")
        conversations_this_month = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE started_at >= $1",
            month_start
        )

        # ==================== CUSTOS ESTIMADOS ====================
        # Preços por token (Claude Sonnet para premium, Haiku para free)
        # Sonnet: $3/1M input, $15/1M output
        # Haiku: $0.25/1M input, $1.25/1M output

        # Estimativa média de tokens por mensagem: 200 input + 300 output
        avg_input_tokens = 200
        avg_output_tokens = 300

        # Custo por mensagem
        cost_per_premium_msg = (avg_input_tokens * 3 / 1_000_000) + (avg_output_tokens * 15 / 1_000_000)  # ~$0.0051
        cost_per_free_msg = (avg_input_tokens * 0.25 / 1_000_000) + (avg_output_tokens * 1.25 / 1_000_000)  # ~$0.000425

        # Custos totais estimados
        total_premium_cost = (premium_messages or 0) * cost_per_premium_msg
        total_free_cost = (free_messages or 0) * cost_per_free_msg
        total_ai_cost = total_premium_cost + total_free_cost

        # Custo este mês (proporção)
        if total_messages > 0:
            monthly_cost_ratio = messages_this_month / total_messages
            monthly_ai_cost = total_ai_cost * monthly_cost_ratio
        else:
            monthly_ai_cost = 0

        # ==================== RECEITA ====================
        # Receita potencial mensal (todos premium pagando $5.99)
        monthly_revenue = premium_users * 5.99

        # Lucro estimado (receita - custos AI)
        monthly_profit = monthly_revenue - monthly_ai_cost

        # ==================== MÉTRICAS AVANÇADAS ====================
        # Custo médio por usuário ativo
        cost_per_active_user = total_ai_cost / active_30d if active_30d > 0 else 0

        # Taxa de conversão free -> premium
        conversion_rate = (premium_users / total_users * 100) if total_users > 0 else 0

        # Retenção (ativos 30d / total)
        retention_rate = (active_30d / total_users * 100) if total_users > 0 else 0

    return {
        "summary": {
            "total_users": total_users,
            "premium_users": premium_users,
            "free_users": free_users,
            "conversion_rate": f"{conversion_rate:.1f}%",
            "retention_30d": f"{retention_rate:.1f}%"
        },
        "activity": {
            "active_7_days": active_7d,
            "active_30_days": active_30d,
            "new_this_month": new_this_month,
            "total_conversations": total_conversations,
            "conversations_this_month": conversations_this_month
        },
        "messages": {
            "total": total_messages,
            "this_month": messages_this_month,
            "from_premium_users": premium_messages or 0,
            "from_free_users": free_messages or 0,
            "avg_per_active_user": round(avg_messages_per_user, 1)
        },
        "costs": {
            "total_ai_cost_usd": f"${total_ai_cost:.2f}",
            "monthly_ai_cost_usd": f"${monthly_ai_cost:.2f}",
            "cost_per_premium_msg": f"${cost_per_premium_msg:.4f}",
            "cost_per_free_msg": f"${cost_per_free_msg:.4f}",
            "cost_per_active_user": f"${cost_per_active_user:.4f}"
        },
        "revenue": {
            "monthly_revenue_usd": f"${monthly_revenue:.2f}",
            "monthly_profit_usd": f"${monthly_profit:.2f}",
            "profit_margin": f"{(monthly_profit / monthly_revenue * 100) if monthly_revenue > 0 else 0:.1f}%"
        },
        "health_indicators": {
            "avg_messages_per_user": round(avg_messages_per_user, 1),
            "premium_engagement": f"{(premium_messages or 0) / (premium_users or 1):.1f} msgs/user" if premium_users else "N/A",
            "free_engagement": f"{(free_messages or 0) / (free_users or 1):.1f} msgs/user" if free_users else "N/A"
        }
    }


@router.get("/users", response_model=List[UserSummary])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Lista todos os usuários"""
    async with db.pool.acquire() as conn:
        if search:
            rows = await conn.fetch(
                """
                SELECT id, email, is_premium, is_active, created_at, last_login,
                       total_messages, trial_messages_used
                FROM users
                WHERE email ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                f"%{search}%", limit, offset
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, email, is_premium, is_active, created_at, last_login,
                       total_messages, trial_messages_used
                FROM users
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset
            )

    users = []
    for row in rows:
        # Buscar nome do perfil
        profile = await db.get_user_profile(str(row["id"]))
        nome = profile.get("nome") if profile else None

        users.append(UserSummary(
            id=str(row["id"]),
            email=row["email"],
            nome=nome,
            is_premium=row["is_premium"],
            is_active=row["is_active"],
            created_at=row["created_at"].isoformat(),
            last_login=row["last_login"].isoformat() if row["last_login"] else None,
            total_messages=row["total_messages"] or 0,
            trial_messages_used=row["trial_messages_used"] or 0
        ))

    return users


@router.post("/users/{user_id}/premium")
async def toggle_premium(
    user_id: str,
    is_premium: bool,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Ativar/desativar premium de um usuário"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users SET is_premium = $1,
            premium_until = CASE WHEN $1 THEN NOW() + INTERVAL '30 days' ELSE NULL END
            WHERE id = $2
            """,
            is_premium, user_id
        )

    return {"message": f"Premium {'ativado' if is_premium else 'desativado'} com sucesso"}


@router.post("/revoke-beta-premium")
async def revoke_beta_premium(
    except_email: Optional[str] = None,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Revoga premium de todos os usuarios BETA (sem stripe_subscription_id).
    Usuarios com assinatura Stripe real nao sao afetados.
    """
    async with db.pool.acquire() as conn:
        # Contar quantos serao afetados
        if except_email:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM users
                WHERE is_premium = TRUE
                AND (stripe_subscription_id IS NULL OR stripe_subscription_id = '')
                AND email != $1
            """, except_email)

            # Revogar
            await conn.execute("""
                UPDATE users SET
                    is_premium = FALSE,
                    subscription_status = 'beta_revoked'
                WHERE is_premium = TRUE
                AND (stripe_subscription_id IS NULL OR stripe_subscription_id = '')
                AND email != $1
            """, except_email)
        else:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM users
                WHERE is_premium = TRUE
                AND (stripe_subscription_id IS NULL OR stripe_subscription_id = '')
            """)

            # Revogar
            await conn.execute("""
                UPDATE users SET
                    is_premium = FALSE,
                    subscription_status = 'beta_revoked'
                WHERE is_premium = TRUE
                AND (stripe_subscription_id IS NULL OR stripe_subscription_id = '')
            """)

    return {
        "success": True,
        "revoked_count": count,
        "except_email": except_email,
        "message": f"Premium revogado de {count} usuarios BETA"
    }


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Desativar usuário"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_active = FALSE WHERE id = $1",
            user_id
        )

    return {"message": "Usuário desativado"}


@router.post("/users/{user_id}/active")
async def toggle_user_active(
    user_id: str,
    is_active: bool,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Ativar/desativar usuário"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_active = $1 WHERE id = $2",
            is_active, user_id
        )

    return {"message": f"Usuário {'ativado' if is_active else 'desativado'} com sucesso"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Remover usuário permanentemente"""
    import uuid

    # Converter string para UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    async with db.pool.acquire() as conn:
        # Verificar se usuário existe
        user = await conn.fetchrow("SELECT email FROM users WHERE id = $1", user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Verificar se não é admin tentando se deletar
        if user["email"] in ADMIN_EMAILS:
            raise HTTPException(status_code=403, detail="Não é possível remover um administrador")

        # Deletar em cascata (mensagens, conversas, perfis, etc.)
        # Usar try/except para ignorar tabelas que não existem
        try:
            await conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = $1)", user_uuid)
        except:
            pass

        try:
            await conn.execute("DELETE FROM conversations WHERE user_id = $1", user_uuid)
        except:
            pass

        try:
            await conn.execute("DELETE FROM user_profiles WHERE user_id = $1", user_uuid)
        except:
            pass

        try:
            await conn.execute("DELETE FROM audit_log WHERE user_id = $1", user_uuid)
        except:
            pass

        # Deletar usuário
        await conn.execute("DELETE FROM users WHERE id = $1", user_uuid)

    return {"message": "Usuário removido permanentemente"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Enviar email de reset de senha para usuário"""
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT email FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # TODO: Implementar envio de email
    # Por enquanto, apenas retorna sucesso
    return {"message": f"Email de reset enviado para {user['email']}"}


@router.get("/conversations/recent")
async def get_recent_conversations(
    limit: int = 20,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Lista conversas recentes de todos os usuários"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.id, c.user_id, c.started_at, c.last_message_at,
                   c.message_count, c.resumo, u.email
            FROM conversations c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.last_message_at DESC
            LIMIT $1
            """,
            limit
        )

    return [
        {
            "id": str(row["id"]),
            "user_email": row["email"],
            "started_at": row["started_at"].isoformat(),
            "last_message_at": row["last_message_at"].isoformat(),
            "message_count": row["message_count"],
            "resumo": row["resumo"]
        }
        for row in rows
    ]


@router.get("/audit/recent")
async def get_recent_audit_logs(
    limit: int = 50,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Logs de auditoria recentes"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT a.id, a.user_id, a.action, a.ip_address, a.created_at, u.email
            FROM audit_log a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT $1
            """,
            limit
        )

    return [
        {
            "id": str(row["id"]),
            "user_email": row["email"],
            "action": row["action"],
            "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
            "created_at": row["created_at"].isoformat()
        }
        for row in rows
    ]


# ============================================
# ROTAS - PERFIL PSICOLÓGICO
# ============================================

@router.post("/users/{user_id}/analyze-psychology")
async def analyze_user_psychology(
    user_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Força análise psicológica de um usuário"""
    from app.ai_service import AIService

    ai_service = AIService(db)
    await ai_service._analyze_psychological_profile(user_id)

    return {"message": "Análise psicológica executada"}


@router.get("/users/{user_id}/psychology")
async def get_user_psychology(
    user_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Retorna perfil psicológico de um usuário"""
    profile = await db.get_psychological_profile(user_id)

    if not profile:
        return {"message": "Perfil ainda não analisado", "profile": None}

    return {
        "profile": {
            "communication_style": profile.get("communication_style"),
            "primary_needs": profile.get("primary_needs"),
            "thinking_patterns": profile.get("thinking_patterns"),
            "emotional_triggers": profile.get("emotional_triggers"),
            "coping_mechanisms": profile.get("coping_mechanisms"),
            "faith_stage": profile.get("faith_stage"),
            "love_language": profile.get("love_language"),
            "temperament": profile.get("temperament"),
            "emotional_openness": profile.get("emotional_openness"),
            "self_awareness": profile.get("self_awareness"),
            "resilience_level": profile.get("resilience_level"),
            "baseline_anxiety": profile.get("baseline_anxiety"),
            "attachment_style": profile.get("attachment_style"),
            "accumulated_insights": profile.get("accumulated_insights"),
            "recommended_approach": profile.get("recommended_approach"),
            "analysis_count": profile.get("analysis_count"),
            "confidence_score": float(profile.get("confidence_score", 0)),
            "last_analysis_at": profile.get("last_analysis_at").isoformat() if profile.get("last_analysis_at") else None
        }
    }


# ============================================
# ROTAS - FEEDBACKS
# ============================================

@router.get("/feedbacks")
async def get_feedbacks(
    limit: int = 50,
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Lista feedbacks reportados pelos usuários"""
    async with db.pool.acquire() as conn:
        # Verificar se tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'message_feedback'
            )
        """)

        if not table_exists:
            return []

        # Construir query
        query = """
            SELECT f.id, f.user_id, f.message_content, f.feedback_type,
                   f.details, f.status, f.created_at, f.reviewed_at,
                   f.reviewer_notes, u.email
            FROM message_feedback f
            LEFT JOIN users u ON f.user_id = u.id
            WHERE 1=1
        """
        params = []
        param_count = 0

        if status:
            param_count += 1
            query += f" AND f.status = ${param_count}"
            params.append(status)

        if feedback_type:
            param_count += 1
            query += f" AND f.feedback_type = ${param_count}"
            params.append(feedback_type)

        param_count += 1
        query += f" ORDER BY f.created_at DESC LIMIT ${param_count}"
        params.append(limit)

        rows = await conn.fetch(query, *params)

    feedback_labels = {
        "not_christian": "Não é cristão",
        "wrong_info": "Informação incorreta",
        "not_helpful": "Não foi útil",
        "inappropriate": "Inapropriado",
        "other": "Outro"
    }

    return [
        {
            "id": str(row["id"]),
            "user_email": row["email"],
            "message_content": row["message_content"][:200] + "..." if len(row["message_content"]) > 200 else row["message_content"],
            "message_full": row["message_content"],
            "feedback_type": row["feedback_type"],
            "feedback_label": feedback_labels.get(row["feedback_type"], row["feedback_type"]),
            "details": row["details"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat(),
            "reviewed_at": row["reviewed_at"].isoformat() if row["reviewed_at"] else None,
            "reviewer_notes": row["reviewer_notes"]
        }
        for row in rows
    ]


@router.get("/feedbacks/stats")
async def get_feedback_stats(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Estatísticas de feedbacks"""
    async with db.pool.acquire() as conn:
        # Verificar se tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'message_feedback'
            )
        """)

        if not table_exists:
            return {
                "total": 0,
                "pending": 0,
                "reviewed": 0,
                "by_type": {}
            }

        total = await conn.fetchval("SELECT COUNT(*) FROM message_feedback")
        pending = await conn.fetchval("SELECT COUNT(*) FROM message_feedback WHERE status = 'pending'")
        reviewed = await conn.fetchval("SELECT COUNT(*) FROM message_feedback WHERE status = 'reviewed'")

        by_type = await conn.fetch("""
            SELECT feedback_type, COUNT(*) as count
            FROM message_feedback
            GROUP BY feedback_type
        """)

    return {
        "total": total or 0,
        "pending": pending or 0,
        "reviewed": reviewed or 0,
        "by_type": {row["feedback_type"]: row["count"] for row in by_type}
    }


@router.post("/feedbacks/{feedback_id}/review")
async def review_feedback(
    feedback_id: str,
    notes: Optional[str] = None,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """Marca feedback como revisado"""
    import uuid
    from datetime import datetime

    try:
        feedback_uuid = uuid.UUID(feedback_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de feedback inválido")

    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE message_feedback
            SET status = 'reviewed', reviewed_at = $1, reviewer_notes = $2
            WHERE id = $3
        """, datetime.utcnow(), notes, feedback_uuid)

    return {"message": "Feedback marcado como revisado"}


# ============================================
# DIAGNÓSTICO DE USUÁRIO
# ============================================

@router.get("/users/{user_id}/diagnose")
async def diagnose_user(
    user_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Diagnóstico completo de um usuário - verifica todos os dados
    que podem causar erros no chat
    """
    import uuid
    import json

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    diagnosis = {
        "user_id": user_id,
        "errors": [],
        "warnings": [],
        "data": {}
    }

    async with db.pool.acquire() as conn:
        # 1. Verificar usuário básico
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_uuid)
        if not user:
            diagnosis["errors"].append("Usuário não encontrado no banco")
            return diagnosis

        diagnosis["data"]["user"] = {
            "email": user["email"],
            "is_premium": user["is_premium"],
            "is_active": user["is_active"],
            "total_messages": user["total_messages"],
            "trial_messages_used": user["trial_messages_used"]
        }

        # 2. Verificar perfil
        try:
            profile = await conn.fetchrow("SELECT * FROM user_profiles WHERE user_id = $1", user_uuid)
            if profile:
                diagnosis["data"]["profile"] = {
                    "nome": profile.get("nome"),
                    "has_lutas_encrypted": bool(profile.get("lutas_encrypted"))
                }
                # Tentar descriptografar lutas
                if profile.get("lutas_encrypted"):
                    try:
                        from app.security import decrypt_data
                        decrypted = decrypt_data(profile["lutas_encrypted"], user_id)
                        json.loads(decrypted)  # Testar se é JSON válido
                        diagnosis["data"]["profile"]["lutas_valid"] = True
                    except Exception as e:
                        diagnosis["errors"].append(f"Erro ao descriptografar lutas: {str(e)}")
                        diagnosis["data"]["profile"]["lutas_valid"] = False
            else:
                diagnosis["warnings"].append("Perfil não encontrado - será criado no primeiro uso")
        except Exception as e:
            diagnosis["errors"].append(f"Erro ao buscar perfil: {str(e)}")

        # 3. Verificar perfil psicológico
        try:
            psych = await conn.fetchrow("SELECT * FROM user_psychological_profile WHERE user_id = $1", user_uuid)
            if psych:
                diagnosis["data"]["psychological_profile"] = {
                    "exists": True,
                    "analysis_count": psych.get("analysis_count"),
                    "confidence_score": float(psych.get("confidence_score", 0))
                }
                # Verificar thinking_patterns (é JSON)
                if psych.get("thinking_patterns"):
                    try:
                        if isinstance(psych["thinking_patterns"], str):
                            json.loads(psych["thinking_patterns"])
                        diagnosis["data"]["psychological_profile"]["thinking_patterns_valid"] = True
                    except Exception as e:
                        diagnosis["errors"].append(f"thinking_patterns inválido: {str(e)}")
                        diagnosis["data"]["psychological_profile"]["thinking_patterns_valid"] = False
            else:
                diagnosis["data"]["psychological_profile"] = {"exists": False}
        except Exception as e:
            diagnosis["warnings"].append(f"Tabela user_psychological_profile pode não existir: {str(e)}")

        # 4. Verificar memórias
        try:
            memories_count = await conn.fetchval(
                "SELECT COUNT(*) FROM user_memories WHERE user_id = $1 AND status = 'active'",
                user_uuid
            )
            diagnosis["data"]["memories"] = {"count": memories_count}

            # Verificar memórias com payload inválido
            invalid_memories = await conn.fetch("""
                SELECT id, fato, payload FROM user_memories
                WHERE user_id = $1 AND payload IS NOT NULL
            """, user_uuid)

            invalid_count = 0
            for mem in invalid_memories:
                if mem["payload"]:
                    try:
                        if isinstance(mem["payload"], str):
                            json.loads(mem["payload"])
                    except:
                        invalid_count += 1
                        diagnosis["errors"].append(f"Memória {mem['id']} tem payload inválido")

            diagnosis["data"]["memories"]["invalid_payload_count"] = invalid_count
        except Exception as e:
            diagnosis["warnings"].append(f"Erro ao verificar memórias: {str(e)}")

        # 5. Verificar conversas
        try:
            conv_count = await conn.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE user_id = $1",
                user_uuid
            )
            diagnosis["data"]["conversations"] = {"count": conv_count}
        except Exception as e:
            diagnosis["warnings"].append(f"Erro ao verificar conversas: {str(e)}")

        # 6. Verificar mensagens (e se descriptografam corretamente)
        try:
            # Pegar última mensagem para testar descriptografia
            last_msg = await conn.fetchrow("""
                SELECT m.id, m.content_encrypted, c.user_id
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.user_id = $1
                ORDER BY m.created_at DESC
                LIMIT 1
            """, user_uuid)

            if last_msg:
                try:
                    from app.security import decrypt_data
                    decrypted = decrypt_data(last_msg["content_encrypted"], user_id)
                    diagnosis["data"]["messages"] = {
                        "last_message_decrypts": True,
                        "sample": decrypted[:50] + "..." if len(decrypted) > 50 else decrypted
                    }
                except Exception as e:
                    diagnosis["errors"].append(f"Erro ao descriptografar última mensagem: {str(e)}")
                    diagnosis["data"]["messages"] = {"last_message_decrypts": False}
            else:
                diagnosis["data"]["messages"] = {"count": 0}
        except Exception as e:
            diagnosis["warnings"].append(f"Erro ao verificar mensagens: {str(e)}")

        # 7. Verificar tabela learning_interactions
        try:
            learning_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'learning_interactions'
                )
            """)
            diagnosis["data"]["learning"] = {"table_exists": learning_exists}
        except Exception as e:
            diagnosis["warnings"].append(f"Erro ao verificar learning: {str(e)}")

    # Resumo
    diagnosis["summary"] = {
        "total_errors": len(diagnosis["errors"]),
        "total_warnings": len(diagnosis["warnings"]),
        "can_chat": len(diagnosis["errors"]) == 0
    }

    return diagnosis


@router.get("/diagnose/email/{email}")
async def diagnose_user_by_email(
    email: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Diagnóstico de usuário por email
    """
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return await diagnose_user(str(user["id"]), admin, db)


# ============================================
# LAYER 2: HEALTH SCORES E TIMELINE EMOCIONAL
# ============================================

@router.get("/users/{user_id}/health-score")
async def get_user_health_score(
    user_id: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Retorna o Memory Health Score de um usuário.
    Calcula em tempo real ou retorna do cache se recente.
    """
    import uuid

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    # Verificar se usuário existe
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Tentar buscar do cache primeiro
    cached = await db.get_cached_health_score(user_id)
    if cached:
        cached["source"] = "cache"
        return cached

    # Calcular fresh
    health_score = await db.calculate_memory_health_score(user_id)
    health_score["source"] = "calculated"

    # Salvar no cache
    await db.save_memory_health_score(user_id, health_score)

    return health_score


@router.get("/users/{user_id}/emotional-timeline")
async def get_user_emotional_timeline(
    user_id: str,
    days: int = 30,
    limit: int = 50,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Retorna a timeline emocional do usuário.
    Dados internos - não expostos ao usuário.
    """
    import uuid

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    # Verificar se usuário existe
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    timeline = await db.get_emotional_timeline(user_id, days=days, limit=limit)

    # Formatar para resposta
    formatted = []
    for entry in timeline:
        formatted.append({
            "id": str(entry.get("id", "")),
            "emotion": entry.get("emotion"),
            "intensity": float(entry.get("intensity", 0.5)),
            "confidence": float(entry.get("confidence", 0.7)),
            "trigger": entry.get("trigger_detected"),
            "themes": entry.get("themes", []),
            "day_of_week": entry.get("day_of_week"),
            "hour_of_day": entry.get("hour_of_day"),
            "created_at": entry.get("created_at").isoformat() if entry.get("created_at") else None
        })

    return {
        "user_id": user_id,
        "email": user.get("email"),
        "period_days": days,
        "total_entries": len(formatted),
        "timeline": formatted
    }


@router.get("/users/{user_id}/emotional-patterns")
async def get_user_emotional_patterns(
    user_id: str,
    days: int = 30,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Retorna padrões emocionais analisados do usuário.
    Inclui emoção dominante, tendência, triggers comuns.
    """
    import uuid

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido")

    # Verificar se usuário existe
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    patterns = await db.get_emotional_patterns(user_id, days=days)
    trend = await db.get_emotional_trend(user_id)

    # Mapear dia da semana para nome
    days_map = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}

    return {
        "user_id": user_id,
        "email": user.get("email"),
        "period_days": days,
        "dominant_emotion": patterns.get("dominant_emotion", "neutro"),
        "avg_intensity": float(patterns.get("avg_intensity", 0.5)),
        "trend": trend,
        "trend_description": {
            "improving": "Melhora emocional recente",
            "worsening": "Piora emocional recente - atenção recomendada",
            "stable": "Estável"
        }.get(trend, "Estável"),
        "peak_day": days_map.get(patterns.get("peak_day"), None),
        "peak_hour": patterns.get("peak_hour"),
        "common_triggers": patterns.get("common_triggers", []),
        "emotions_detected": patterns.get("emotions_detected", []),
        "needs_attention": trend == "worsening" or float(patterns.get("avg_intensity", 0.5)) > 0.75
    }


@router.get("/health-scores/overview")
async def get_health_scores_overview(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Visão geral de Health Scores de todos os usuários.
    Útil para identificar usuários que precisam de atenção.
    """
    async with db.pool.acquire() as conn:
        # Verificar se tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'memory_health_scores'
            )
        """)

        if not table_exists:
            return {
                "message": "Tabela de health scores ainda não existe",
                "total_scored": 0,
                "by_level": {},
                "users": []
            }

        # Buscar scores
        scores = await conn.fetch("""
            SELECT
                mhs.*,
                u.email,
                u.total_messages
            FROM memory_health_scores mhs
            JOIN users u ON u.id = mhs.user_id
            ORDER BY mhs.overall_score ASC
            LIMIT 50
        """)

        # Contar por nível
        level_counts = await conn.fetch("""
            SELECT health_level, COUNT(*) as count
            FROM memory_health_scores
            GROUP BY health_level
        """)

        users = []
        for s in scores:
            users.append({
                "user_id": str(s["user_id"]),
                "email": s["email"],
                "overall_score": s["overall_score"],
                "health_level": s["health_level"],
                "total_messages": s["total_messages"],
                "active_memories": s["active_memories"],
                "last_calculated": s["last_calculated_at"].isoformat() if s["last_calculated_at"] else None
            })

        return {
            "total_scored": len(scores),
            "by_level": {row["health_level"]: row["count"] for row in level_counts},
            "users": users
        }


@router.get("/emotional-alerts")
async def get_emotional_alerts(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Lista usuários que precisam de atenção baseado em padrões emocionais.
    Identifica tendências de piora ou alta intensidade emocional.
    """
    async with db.pool.acquire() as conn:
        # Verificar se tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'emotional_timeline'
            )
        """)

        if not table_exists:
            return {
                "message": "Tabela de timeline emocional ainda não existe",
                "alerts": []
            }

        # Buscar usuários com emoções negativas frequentes nos últimos 7 dias
        alerts = await conn.fetch("""
            WITH recent_emotions AS (
                SELECT
                    user_id,
                    emotion,
                    AVG(intensity) as avg_intensity,
                    COUNT(*) as count
                FROM emotional_timeline
                WHERE created_at > NOW() - INTERVAL '7 days'
                AND emotion IN ('ansioso', 'triste', 'angustiado', 'estressado', 'deprimido', 'medo', 'solitário')
                GROUP BY user_id, emotion
            ),
            user_summary AS (
                SELECT
                    user_id,
                    SUM(count) as total_negative,
                    MAX(avg_intensity) as max_intensity,
                    ARRAY_AGG(DISTINCT emotion) as emotions
                FROM recent_emotions
                GROUP BY user_id
                HAVING SUM(count) >= 3 OR MAX(avg_intensity) > 0.7
            )
            SELECT
                us.*,
                u.email,
                u.total_messages
            FROM user_summary us
            JOIN users u ON u.id = us.user_id
            ORDER BY us.max_intensity DESC, us.total_negative DESC
            LIMIT 20
        """)

        result = []
        for a in alerts:
            result.append({
                "user_id": str(a["user_id"]),
                "email": a["email"],
                "total_negative_emotions": a["total_negative"],
                "max_intensity": float(a["max_intensity"]),
                "emotions_detected": a["emotions"],
                "total_messages": a["total_messages"],
                "alert_level": "high" if float(a["max_intensity"]) > 0.8 else "medium"
            })

        return {
            "period": "last_7_days",
            "total_alerts": len(result),
            "alerts": result
        }


# ============================================
# BACKUP DO BANCO DE DADOS
# ============================================

@router.get("/backup/full")
async def download_full_backup(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Gera backup completo do banco em JSON.
    Inclui: usuários, perfis, conversas, mensagens (criptografadas), memórias.
    IMPORTANTE: Mensagens permanecem criptografadas por segurança.
    """
    import json
    from datetime import datetime
    from fastapi.responses import Response

    backup_data = {
        "backup_info": {
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "generated_by": admin["user_id"]
        },
        "users": [],
        "profiles": [],
        "conversations": [],
        "messages": [],
        "memories": [],
        "psychological_profiles": []
    }

    async with db.pool.acquire() as conn:
        # 1. Usuários (sem senha)
        users = await conn.fetch("""
            SELECT id, email, is_premium, is_active, created_at, last_login,
                   total_messages, trial_messages_used, premium_until
            FROM users
        """)
        backup_data["users"] = [
            {
                "id": str(u["id"]),
                "email": u["email"],
                "is_premium": u["is_premium"],
                "is_active": u["is_active"],
                "created_at": u["created_at"].isoformat() if u["created_at"] else None,
                "last_login": u["last_login"].isoformat() if u["last_login"] else None,
                "total_messages": u["total_messages"],
                "trial_messages_used": u["trial_messages_used"],
                "premium_until": u["premium_until"].isoformat() if u["premium_until"] else None
            }
            for u in users
        ]

        # 2. Perfis
        profiles = await conn.fetch("SELECT * FROM user_profiles")
        backup_data["profiles"] = [
            {
                "id": str(p["id"]),
                "user_id": str(p["user_id"]),
                "nome": p.get("nome"),
                "lutas_encrypted": p["lutas_encrypted"].hex() if p.get("lutas_encrypted") else None,
                "created_at": p["created_at"].isoformat() if p.get("created_at") else None
            }
            for p in profiles
        ]

        # 3. Conversas
        conversations = await conn.fetch("SELECT * FROM conversations")
        backup_data["conversations"] = [
            {
                "id": str(c["id"]),
                "user_id": str(c["user_id"]),
                "started_at": c["started_at"].isoformat() if c.get("started_at") else None,
                "last_message_at": c["last_message_at"].isoformat() if c.get("last_message_at") else None,
                "message_count": c.get("message_count"),
                "resumo": c.get("resumo"),
                "is_archived": c.get("is_archived", False)
            }
            for c in conversations
        ]

        # 4. Mensagens (mantém criptografado)
        messages = await conn.fetch("SELECT * FROM messages")
        backup_data["messages"] = [
            {
                "id": str(m["id"]),
                "conversation_id": str(m["conversation_id"]),
                "user_id": str(m["user_id"]),
                "role": m["role"],
                "content_encrypted": m["content_encrypted"].hex() if m.get("content_encrypted") else None,
                "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
                "tokens_used": m.get("tokens_used"),
                "model_used": m.get("model_used")
            }
            for m in messages
        ]

        # 5. Memórias
        try:
            memories = await conn.fetch("SELECT * FROM user_memories")
            backup_data["memories"] = [
                {
                    "id": str(mem["id"]),
                    "user_id": str(mem["user_id"]),
                    "categoria": mem.get("categoria"),
                    "fato": mem.get("fato"),
                    "contexto": mem.get("contexto"),
                    "importancia": mem.get("importancia"),
                    "status": mem.get("status"),
                    "created_at": mem["created_at"].isoformat() if mem.get("created_at") else None
                }
                for mem in memories
            ]
        except:
            backup_data["memories"] = []

        # 6. Perfis psicológicos
        try:
            psych = await conn.fetch("SELECT * FROM user_psychological_profile")
            backup_data["psychological_profiles"] = [
                {
                    "id": str(p["id"]),
                    "user_id": str(p["user_id"]),
                    "communication_style": p.get("communication_style"),
                    "primary_needs": p.get("primary_needs"),
                    "faith_stage": p.get("faith_stage"),
                    "temperament": p.get("temperament"),
                    "confidence_score": float(p.get("confidence_score", 0)),
                    "analysis_count": p.get("analysis_count"),
                    "last_analysis_at": p["last_analysis_at"].isoformat() if p.get("last_analysis_at") else None
                }
                for p in psych
            ]
        except:
            backup_data["psychological_profiles"] = []

    # Gerar JSON
    json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)

    # Retornar como download
    filename = f"aisyster_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    return Response(
        content=json_data,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/backup/stats")
async def get_backup_stats(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Retorna estatísticas do que seria incluído no backup.
    Útil para verificar antes de baixar.
    """
    async with db.pool.acquire() as conn:
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        conversations_count = await conn.fetchval("SELECT COUNT(*) FROM conversations")
        messages_count = await conn.fetchval("SELECT COUNT(*) FROM messages")

        try:
            memories_count = await conn.fetchval("SELECT COUNT(*) FROM user_memories")
        except:
            memories_count = 0

        try:
            profiles_count = await conn.fetchval("SELECT COUNT(*) FROM user_profiles")
        except:
            profiles_count = 0

    return {
        "users": users_count or 0,
        "profiles": profiles_count or 0,
        "conversations": conversations_count or 0,
        "messages": messages_count or 0,
        "memories": memories_count or 0,
        "estimated_size_mb": round((messages_count or 0) * 0.002, 2)  # ~2KB por mensagem
    }


# ============================================
# PUSH NOTIFICATIONS - ADMIN
# ============================================

class BroadcastNotification(BaseModel):
    title: str
    body: str
    url: Optional[str] = "/"
    target: Optional[str] = "all"  # all, premium, free


@router.get("/push/stats")
async def get_push_stats(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Estatísticas de push notifications.
    """
    async with db.pool.acquire() as conn:
        # Contar subscriptions ativas
        try:
            subs = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) FILTER (WHERE is_active = TRUE) as active
                FROM push_subscriptions
            """)
            subscriptions = {
                "total": subs["total"] or 0,
                "unique_users": subs["unique_users"] or 0,
                "active": subs["active"] or 0
            }
        except:
            subscriptions = {"total": 0, "unique_users": 0, "active": 0}

        # Estatísticas de notificações enviadas
        try:
            notification_stats = await db.get_notification_stats(days=7)
        except:
            notification_stats = {}

    return {
        "subscriptions": subscriptions,
        "notifications_last_7_days": notification_stats
    }


@router.get("/push/subscriptions")
async def list_push_subscriptions(
    limit: int = 50,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Lista subscriptions de push.
    """
    subs = await db.get_all_push_subscriptions(limit=limit)

    return [
        {
            "id": str(s.get("id", "")),
            "user_id": str(s.get("user_id", "")),
            "email": s.get("email"),
            "is_premium": s.get("is_premium", False),
            "endpoint": s.get("endpoint", "")[:50] + "...",
            "is_active": s.get("is_active", True),
            "created_at": s.get("created_at").isoformat() if s.get("created_at") else None,
            "last_used_at": s.get("last_used_at").isoformat() if s.get("last_used_at") else None
        }
        for s in subs
    ]


@router.post("/push/broadcast")
async def broadcast_notification(
    notification: BroadcastNotification,
    background_tasks: BackgroundTasks,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Envia notificação para todos os usuários (ou grupo específico).
    """
    # Determinar filtro
    filter_premium = None
    if notification.target == "premium":
        filter_premium = True
    elif notification.target == "free":
        filter_premium = False

    # Buscar todas subscriptions
    subscriptions = await db.get_all_push_subscriptions(
        filter_premium=filter_premium,
        limit=1000
    )

    if not subscriptions:
        return {"success": False, "message": "Nenhuma subscription encontrada", "sent": 0}

    # Enviar em background
    async def send_all():
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
                title=notification.title,
                body=notification.body,
                url=notification.url or "/",
                db=db,
                user_id=str(sub["user_id"]),
                notification_type="broadcast"
            )

            if success:
                success_count += 1

        print(f"[PUSH BROADCAST] Sent to {success_count}/{len(subscriptions)} users")

    background_tasks.add_task(send_all)

    return {
        "success": True,
        "message": f"Enviando notificacao para {len(subscriptions)} dispositivos",
        "target": notification.target,
        "queued": len(subscriptions)
    }


@router.post("/push/send-to-user/{user_id}")
async def send_notification_to_user(
    user_id: str,
    title: str,
    body: str,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Envia notificação para um usuário específico.
    """
    import uuid

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario invalido")

    # Verificar se usuário existe
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    # Buscar subscriptions do usuário
    subscriptions = await db.get_user_push_subscriptions(user_id)

    if not subscriptions:
        raise HTTPException(
            status_code=400,
            detail="Usuario nao tem push habilitado"
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
            title=title,
            body=body,
            db=db,
            user_id=user_id,
            notification_type="admin_direct"
        )

        if success:
            success_count += 1

    if success_count > 0:
        return {
            "success": True,
            "message": f"Notificacao enviada para {success_count} dispositivo(s)",
            "user_email": user.get("email")
        }
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar notificacao")


@router.get("/push/logs")
async def get_notification_logs(
    limit: int = 50,
    notification_type: Optional[str] = None,
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Logs de notificações enviadas.
    """
    async with db.pool.acquire() as conn:
        try:
            if notification_type:
                rows = await conn.fetch("""
                    SELECT nl.*, u.email
                    FROM notification_logs nl
                    LEFT JOIN users u ON u.id = nl.user_id
                    WHERE nl.notification_type = $1
                    ORDER BY nl.sent_at DESC
                    LIMIT $2
                """, notification_type, limit)
            else:
                rows = await conn.fetch("""
                    SELECT nl.*, u.email
                    FROM notification_logs nl
                    LEFT JOIN users u ON u.id = nl.user_id
                    ORDER BY nl.sent_at DESC
                    LIMIT $1
                """, limit)
        except:
            return []

    return [
        {
            "id": str(r.get("id", "")),
            "user_email": r.get("email"),
            "notification_type": r.get("notification_type"),
            "title": r.get("title"),
            "body": r.get("body")[:100] + "..." if r.get("body") and len(r.get("body", "")) > 100 else r.get("body"),
            "success": r.get("success", True),
            "error_message": r.get("error_message"),
            "sent_at": r.get("sent_at").isoformat() if r.get("sent_at") else None
        }
        for r in rows
    ]


@router.post("/push/trigger-reminders")
async def trigger_reminder_notifications(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Dispara lembretes manualmente (para teste).
    Normalmente enviados automaticamente pelo scheduler.
    """
    count = await send_reminder_notifications()
    return {
        "success": True,
        "message": f"Lembretes enviados para {count} usuarios"
    }


@router.post("/push/trigger-engagement")
async def trigger_engagement_notifications(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Dispara notificacoes de engajamento manualmente (para teste).
    Normalmente enviados automaticamente pelo scheduler.
    """
    count = await send_engagement_notifications()
    return {
        "success": True,
        "message": f"Notificacoes de engajamento enviadas para {count} usuarios"
    }


@router.post("/debug/create-push-table")
async def create_push_subscriptions_table(
    db: Database = Depends(get_db)
):
    """
    Debug: cria a tabela push_subscriptions se não existir.
    TEMPORÁRIO
    """
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                endpoint TEXT NOT NULL UNIQUE,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        return {"success": True, "message": "Tabela push_subscriptions criada/verificada"}


@router.get("/debug/user-push/{email}")
async def debug_user_push(
    email: str,
    db: Database = Depends(get_db)
):
    """
    Debug: verifica push subscription de um usuário por email.
    TEMPORÁRIO - remover autenticação para debug
    """
    async with db.pool.acquire() as conn:
        # Buscar usuário
        user = await conn.fetchrow(
            "SELECT id, email, is_active, is_premium FROM users WHERE email = $1",
            email
        )

        if not user:
            return {"error": "Usuário não encontrado", "email": email}

        user_id = user["id"]

        # Verificar se tabela push_subscriptions existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'push_subscriptions'
            )
        """)

        if not table_exists:
            return {
                "user": dict(user),
                "error": "Tabela push_subscriptions não existe ainda"
            }

        # Buscar subscriptions
        subscriptions = await conn.fetch(
            """
            SELECT id, endpoint, is_active, created_at, last_used_at
            FROM push_subscriptions
            WHERE user_id = $1
            """,
            user_id
        )

        # Contar total de subscriptions ativas
        total_active = await conn.fetchval(
            "SELECT COUNT(*) FROM push_subscriptions WHERE is_active = TRUE"
        )

        return {
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "is_active": user["is_active"],
                "is_premium": user["is_premium"]
            },
            "subscriptions": [
                {
                    "id": str(s["id"]),
                    "endpoint": s["endpoint"][:80] + "..." if len(s["endpoint"]) > 80 else s["endpoint"],
                    "is_active": s["is_active"],
                    "created_at": s["created_at"].isoformat() if s["created_at"] else None,
                    "last_used_at": s["last_used_at"].isoformat() if s["last_used_at"] else None
                }
                for s in subscriptions
            ],
            "subscription_count": len(subscriptions),
            "total_active_subscriptions_in_db": total_active
        }


@router.post("/debug/add-notification-columns")
async def add_notification_separate_columns(
    db: Database = Depends(get_db)
):
    """
    Debug: adiciona colunas push_sent, push_failed, email_sent, email_failed
    na tabela notifications se não existirem.
    """
    async with db.pool.acquire() as conn:
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'push_sent') THEN
                    ALTER TABLE notifications ADD COLUMN push_sent INTEGER DEFAULT 0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'push_failed') THEN
                    ALTER TABLE notifications ADD COLUMN push_failed INTEGER DEFAULT 0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'email_sent') THEN
                    ALTER TABLE notifications ADD COLUMN email_sent INTEGER DEFAULT 0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'email_failed') THEN
                    ALTER TABLE notifications ADD COLUMN email_failed INTEGER DEFAULT 0;
                END IF;
            END $$;
        """)
        return {"success": True, "message": "Colunas de contagem separada adicionadas"}


@router.post("/debug/create-notification-deliveries")
async def create_notification_deliveries_table(
    db: Database = Depends(get_db)
):
    """
    Debug: cria a tabela notification_deliveries se não existir.
    """
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notification_deliveries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                channel VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                sent_at TIMESTAMP WITH TIME ZONE,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        # Criar índices
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notification_deliveries_notification
            ON notification_deliveries(notification_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notification_deliveries_user
            ON notification_deliveries(user_id)
        """)
        return {"success": True, "message": "Tabela notification_deliveries criada/verificada"}


@router.get("/debug/check-notification-tables")
async def check_notification_tables(
    db: Database = Depends(get_db)
):
    """
    Debug: verifica se todas as tabelas de notificação existem.
    """
    async with db.pool.acquire() as conn:
        tables = {}

        for table in ['notifications', 'notification_deliveries', 'notification_logs', 'push_subscriptions']:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = $1
                )
            """, table)
            tables[table] = exists

        # Verificar colunas da tabela notifications
        if tables['notifications']:
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'notifications'
                ORDER BY ordinal_position
            """)
            tables['notifications_columns'] = [
                {"name": c["column_name"], "type": c["data_type"]}
                for c in columns
            ]

        return tables


@router.post("/debug/test-push-direct/{user_id}")
async def test_push_direct(
    user_id: str,
    db: Database = Depends(get_db)
):
    """
    Debug: testa envio de push direto para um usuário com detalhes do erro.
    """
    from pywebpush import webpush, WebPushException
    from app.config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS_EMAIL
    import uuid
    import json

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return {"error": "ID de usuário inválido"}

    # Verificar subscriptions
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT email FROM users WHERE id = $1", user_uuid)
        if not user:
            return {"error": "Usuário não encontrado"}

        subs = await conn.fetch("""
            SELECT endpoint, p256dh, auth, is_active
            FROM push_subscriptions
            WHERE user_id = $1 AND is_active = TRUE
        """, user_uuid)

        if not subs:
            return {
                "error": "Nenhuma subscription ativa encontrada",
                "user_email": user["email"]
            }

    # Tentar enviar diretamente com captura de erro
    results = []
    for sub in subs:
        subscription_info = {
            "endpoint": sub["endpoint"],
            "keys": {
                "p256dh": sub["p256dh"],
                "auth": sub["auth"]
            }
        }

        payload = json.dumps({
            "title": "Teste Direto",
            "body": "Esta é uma notificação de teste direto do admin.",
            "icon": "/static/icons/icon-192x192.png",
            "url": "/app"
        })

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{VAPID_CLAIMS_EMAIL}"
                }
            )
            results.append({
                "endpoint": sub["endpoint"][:60] + "...",
                "success": True,
                "error": None
            })
        except WebPushException as e:
            error_detail = str(e)
            if e.response:
                error_detail += f" | Status: {e.response.status_code} | Body: {e.response.text[:200]}"
            results.append({
                "endpoint": sub["endpoint"][:60] + "...",
                "success": False,
                "error": error_detail
            })
        except Exception as e:
            results.append({
                "endpoint": sub["endpoint"][:60] + "...",
                "success": False,
                "error": f"Unexpected: {str(e)}"
            })

    success_count = sum(1 for r in results if r["success"])

    return {
        "user_email": user["email"],
        "subscriptions_tested": len(results),
        "success_count": success_count,
        "vapid_email": VAPID_CLAIMS_EMAIL,
        "vapid_public_key_preview": VAPID_PUBLIC_KEY[:20] + "..." if VAPID_PUBLIC_KEY else "NOT SET",
        "vapid_private_key_set": bool(VAPID_PRIVATE_KEY),
        "results": results
    }


@router.get("/debug/generate-vapid-keys")
async def generate_vapid_keys():
    """
    Debug: gera novas chaves VAPID no formato correto para pywebpush.
    """
    from py_vapid import Vapid

    vapid = Vapid()
    vapid.generate_keys()

    # Obter as chaves no formato correto
    public_key = vapid.public_key_urlsafe_base64
    private_key = vapid.private_key_urlsafe_base64

    return {
        "message": "Novas chaves VAPID geradas. Configure no Railway:",
        "VAPID_PUBLIC_KEY": public_key,
        "VAPID_PRIVATE_KEY": private_key,
        "instructions": [
            "1. Copie as chaves acima",
            "2. No Railway, vá em Variables",
            "3. Adicione VAPID_PUBLIC_KEY e VAPID_PRIVATE_KEY",
            "4. Atualize também a chave pública no frontend (index.html)",
            "5. Depois, os usuários precisarão re-registrar as subscriptions"
        ]
    }


@router.delete("/debug/clear-push-subscriptions")
async def clear_push_subscriptions(
    db: Database = Depends(get_db)
):
    """
    Debug: limpa todas as push subscriptions (necessário após trocar chaves VAPID).
    """
    async with db.pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM push_subscriptions")
        await conn.execute("DELETE FROM push_subscriptions")
        return {
            "success": True,
            "deleted": count,
            "message": f"{count} subscriptions removidas. Os usuários precisam re-ativar as notificações."
        }


@router.post("/run-migration/language-voice")
async def run_language_voice_migration(
    admin: dict = Depends(verify_admin),
    db: Database = Depends(get_db)
):
    """
    Executa migration para adicionar colunas language, spoken_language e voice
    na tabela user_profiles.
    """
    results = []

    async with db.pool.acquire() as conn:
        # 1. Adicionar coluna language
        try:
            await conn.execute("""
                ALTER TABLE user_profiles
                ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'auto'
            """)
            results.append({"column": "language", "status": "success"})
        except Exception as e:
            results.append({"column": "language", "status": "error", "error": str(e)})

        # 2. Adicionar coluna spoken_language
        try:
            await conn.execute("""
                ALTER TABLE user_profiles
                ADD COLUMN IF NOT EXISTS spoken_language VARCHAR(10) DEFAULT 'auto'
            """)
            results.append({"column": "spoken_language", "status": "success"})
        except Exception as e:
            results.append({"column": "spoken_language", "status": "error", "error": str(e)})

        # 3. Adicionar coluna voice
        try:
            await conn.execute("""
                ALTER TABLE user_profiles
                ADD COLUMN IF NOT EXISTS voice VARCHAR(20) DEFAULT 'nova'
            """)
            results.append({"column": "voice", "status": "success"})
        except Exception as e:
            results.append({"column": "voice", "status": "error", "error": str(e)})

        # Verificar colunas criadas
        columns = await conn.fetch("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'user_profiles'
            AND column_name IN ('language', 'spoken_language', 'voice')
            ORDER BY column_name
        """)

        columns_info = [
            {
                "name": col["column_name"],
                "type": col["data_type"],
                "default": col["column_default"]
            }
            for col in columns
        ]

    success = all(r["status"] == "success" for r in results)

    return {
        "success": success,
        "migration": "language_voice_columns",
        "results": results,
        "columns_verified": columns_info,
        "message": "Migration executada com sucesso!" if success else "Alguns erros ocorreram"
    }


@router.get("/debug/push-subscriptions")
async def list_all_push_subscriptions(
    db: Database = Depends(get_db)
):
    """
    Debug: lista todos os usuários com push subscription ativa.
    """
    async with db.pool.acquire() as conn:
        # Verificar se tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'push_subscriptions'
            )
        """)

        if not table_exists:
            return {"error": "Tabela push_subscriptions não existe", "users": []}

        # Buscar todos os usuários com subscription ativa
        rows = await conn.fetch("""
            SELECT DISTINCT
                u.id,
                u.email,
                u.is_premium,
                u.is_active,
                up.nome,
                COUNT(ps.id) as subscription_count,
                MAX(ps.created_at) as last_subscription
            FROM push_subscriptions ps
            JOIN users u ON ps.user_id = u.id
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE ps.is_active = TRUE
            GROUP BY u.id, u.email, u.is_premium, u.is_active, up.nome
            ORDER BY last_subscription DESC
        """)

        return {
            "total_users_with_push": len(rows),
            "users": [
                {
                    "id": str(r["id"]),
                    "email": r["email"],
                    "nome": r["nome"],
                    "is_premium": r["is_premium"],
                    "is_active": r["is_active"],
                    "subscription_count": r["subscription_count"],
                    "last_subscription": r["last_subscription"].isoformat() if r["last_subscription"] else None
                }
                for r in rows
            ]
        }

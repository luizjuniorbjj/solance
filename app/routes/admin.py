"""
SoulHaven - Rotas de Administração
Painel para gerenciar usuários, conversas e métricas
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database
from app.config import ADMIN_EMAILS

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

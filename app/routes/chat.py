"""
SoulHaven - Rotas de Chat
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database
from app.ai_service import AIService
from app.security import rate_limiter
from app.config import FREE_MESSAGE_LIMIT, FREE_WARNING_AT, FREE_URGENT_AT, TRIAL_MESSAGES_LIMIT_ANONYMOUS

router = APIRouter(prefix="/chat", tags=["Chat"])

# In-memory storage for trial sessions (in production, use Redis)
trial_sessions: Dict[str, dict] = {}


# ============================================
# MODELOS
# ============================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class TrialChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model_used: str
    tokens_used: int
    # Limite free
    messages_used: Optional[int] = None
    messages_limit: Optional[int] = None
    limit_warning: Optional[str] = None  # "soft", "urgent", "reached"


class TrialChatResponse(BaseModel):
    response: str
    trial_remaining: int


class ConversationSummary(BaseModel):
    id: str
    started_at: str
    last_message_at: str
    message_count: int
    resumo: Optional[str]
    temas: List[str]


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


# ============================================
# ROTAS
# ============================================

@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Envia mensagem e recebe resposta da IA
    """
    user_id = current_user["user_id"]

    # Rate limiting
    if not rate_limiter.is_allowed(user_id, max_requests=30, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Muitas mensagens. Aguarde um momento."
        )

    # Validação básica
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode ser vazia")

    if len(request.message) > 5000:
        raise HTTPException(status_code=400, detail="Mensagem muito longa")

    # Buscar usuário e verificar limites
    user = await db.get_user_by_id(user_id)
    is_premium = user.get("is_premium", False)
    messages_used = user.get("trial_messages_used", 0)

    # Verificar limite para usuários free
    limit_warning = None
    if not is_premium:
        if messages_used >= FREE_MESSAGE_LIMIT:
            raise HTTPException(
                status_code=402,
                detail="Você atingiu o limite gratuito. Assine para continuar conversando!"
            )

    # Processar mensagem
    ai_service = AIService(db)
    result = await ai_service.chat(
        user_id=user_id,
        message=request.message,
        conversation_id=request.conversation_id
    )

    # Incrementar contador para usuários free
    if not is_premium:
        messages_used += 1
        await db.increment_trial_messages(user_id)

        # Definir aviso de limite
        if messages_used >= FREE_MESSAGE_LIMIT:
            limit_warning = "reached"
        elif messages_used >= FREE_URGENT_AT:
            limit_warning = "urgent"
        elif messages_used >= FREE_WARNING_AT:
            limit_warning = "soft"

    # Log de auditoria
    await db.log_audit(
        user_id=user_id,
        action="message_sent",
        details={"conversation_id": result["conversation_id"]}
    )

    return ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
        model_used=result["model_used"],
        tokens_used=result["tokens_used"],
        messages_used=messages_used if not is_premium else None,
        messages_limit=FREE_MESSAGE_LIMIT if not is_premium else None,
        limit_warning=limit_warning
    )


@router.post("/trial", response_model=TrialChatResponse)
async def trial_chat(
    request: TrialChatRequest,
    req: Request,
    db: Database = Depends(get_db)
):
    """
    Chat para usuários sem conta (modo trial/visitante)
    Limite de mensagens por sessão
    """
    session_id = request.session_id
    client_ip = req.client.host if req.client else "unknown"

    # Rate limiting por IP
    if not rate_limiter.is_allowed(f"trial_{client_ip}", max_requests=10, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Muitas mensagens. Aguarde um momento."
        )

    # Inicializar ou buscar sessão
    if session_id not in trial_sessions:
        trial_sessions[session_id] = {
            "messages_count": 0,
            "messages": [],
            "ip": client_ip
        }

    session = trial_sessions[session_id]

    # Verificar limite
    if session["messages_count"] >= TRIAL_MESSAGES_LIMIT_ANONYMOUS:
        raise HTTPException(
            status_code=402,
            detail="Limite de mensagens atingido. Crie uma conta para continuar."
        )

    # Validação básica
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode ser vazia")

    if len(request.message) > 2000:
        raise HTTPException(status_code=400, detail="Mensagem muito longa (máx 2000 caracteres)")

    # Processar mensagem com AI
    ai_service = AIService(db)

    # Simular contexto de usuário trial
    trial_user = {
        "is_premium": False,
        "nome": "Visitante"
    }

    # Construir histórico simples
    history = session["messages"][-6:]  # Últimas 3 trocas

    response = await ai_service.chat_trial(
        message=request.message,
        history=history,
        user=trial_user
    )

    # Atualizar sessão
    session["messages_count"] += 1
    session["messages"].append({"role": "user", "content": request.message})
    session["messages"].append({"role": "assistant", "content": response})

    remaining = TRIAL_MESSAGES_LIMIT_ANONYMOUS - session["messages_count"]

    return TrialChatResponse(
        response=response,
        trial_remaining=remaining
    )


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Lista conversas recentes do usuário
    """
    conversations = await db.get_recent_conversations(
        user_id=current_user["user_id"],
        limit=limit
    )

    import json
    result = []
    for c in conversations:
        # Tratar temas que pode vir como string JSON ou lista
        temas = c.get("temas", [])
        if isinstance(temas, str):
            try:
                temas = json.loads(temas) if temas else []
            except:
                temas = []
        result.append(ConversationSummary(
            id=str(c["id"]),
            started_at=c["started_at"].isoformat(),
            last_message_at=c["last_message_at"].isoformat(),
            message_count=c["message_count"],
            resumo=c.get("resumo"),
            temas=temas or []
        ))
    return result


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Busca mensagens de uma conversa específica
    """
    # Verificar se a conversa pertence ao usuário
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    if str(conversation["user_id"]) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    messages = await db.get_conversation_messages(
        conversation_id=conversation_id,
        user_id=current_user["user_id"],
        limit=limit
    )

    return [
        MessageResponse(
            id=str(m["id"]),
            role=m["role"],
            content=m["content"],
            created_at=m["created_at"].isoformat()
        )
        for m in messages
    ]


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Arquiva uma conversa
    """
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    if str(conversation["user_id"]) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE conversations SET is_archived = TRUE WHERE id = $1",
            conversation_id
        )

    return {"message": "Conversa arquivada"}


class RenameRequest(BaseModel):
    resumo: str


@router.patch("/conversations/{conversation_id}/rename")
async def rename_conversation(
    conversation_id: str,
    request: RenameRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Renomeia uma conversa (atualiza o resumo)
    """
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    if str(conversation["user_id"]) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE conversations SET resumo = $1 WHERE id = $2",
            request.resumo,
            conversation_id
        )

    return {"message": "Conversa renomeada"}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Exclui uma conversa e suas mensagens
    """
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    if str(conversation["user_id"]) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    async with db.pool.acquire() as conn:
        # Limpar referência em user_memories (não excluir as memórias, só a referência)
        await conn.execute(
            "UPDATE user_memories SET origem_conversa_id = NULL WHERE origem_conversa_id = $1",
            conversation_id
        )
        # Limpar referência em user_insights
        await conn.execute(
            "UPDATE user_insights SET origem_conversa_id = NULL WHERE origem_conversa_id = $1",
            conversation_id
        )
        # Excluir mensagens (devido à foreign key)
        await conn.execute(
            "DELETE FROM messages WHERE conversation_id = $1",
            conversation_id
        )
        # Excluir conversa
        await conn.execute(
            "DELETE FROM conversations WHERE id = $1",
            conversation_id
        )

    return {"message": "Conversa excluída"}


# ============================================
# FEEDBACK DE MENSAGENS
# ============================================

class FeedbackRequest(BaseModel):
    message_content: str  # Conteúdo da mensagem da IA
    feedback_type: str  # "wrong_info", "not_christian", "not_helpful", "inappropriate", "other"
    details: Optional[str] = None  # Detalhes adicionais do usuário
    conversation_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    message: str
    feedback_id: str


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Envia feedback sobre uma resposta da IA
    Permite reportar erros, respostas não-cristãs, etc.
    """
    import uuid
    from datetime import datetime

    user_id = current_user["user_id"]

    # Validar tipo de feedback
    valid_types = ["wrong_info", "not_christian", "not_helpful", "inappropriate", "other"]
    if request.feedback_type not in valid_types:
        raise HTTPException(status_code=400, detail="Tipo de feedback inválido")

    # Salvar feedback no banco
    feedback_id = str(uuid.uuid4())

    async with db.pool.acquire() as conn:
        # Criar tabela se não existir
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS message_feedback (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id),
                conversation_id UUID,
                message_content TEXT NOT NULL,
                feedback_type VARCHAR(50) NOT NULL,
                details TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW(),
                reviewed_at TIMESTAMP,
                reviewer_notes TEXT
            )
        """)

        # Inserir feedback
        await conn.execute("""
            INSERT INTO message_feedback (id, user_id, conversation_id, message_content, feedback_type, details)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, uuid.UUID(feedback_id), uuid.UUID(user_id),
            uuid.UUID(request.conversation_id) if request.conversation_id else None,
            request.message_content[:2000],  # Limitar tamanho
            request.feedback_type,
            request.details[:1000] if request.details else None
        )

    # Log de auditoria
    await db.log_audit(
        user_id=user_id,
        action="feedback_submitted",
        details={"feedback_type": request.feedback_type, "feedback_id": feedback_id}
    )

    return FeedbackResponse(
        message="Obrigado pelo feedback! Vamos analisar e melhorar.",
        feedback_id=feedback_id
    )

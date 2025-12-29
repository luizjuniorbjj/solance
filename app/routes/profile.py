"""
SoulHaven - Rotas de Perfil e Onboarding
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database

router = APIRouter(prefix="/profile", tags=["Perfil"])


# ============================================
# MODELOS
# ============================================

class ProfileUpdate(BaseModel):
    nome: Optional[str] = None
    apelido: Optional[str] = None
    idade: Optional[int] = None
    genero: Optional[str] = None
    estado_civil: Optional[str] = None
    filhos: Optional[List[dict]] = None
    profissao: Optional[str] = None
    cidade: Optional[str] = None

    # Espiritual
    denominacao: Optional[str] = None
    tempo_de_fe: Optional[str] = None
    batizado: Optional[bool] = None
    igreja_local: Optional[str] = None
    cargo_igreja: Optional[str] = None

    # Preferências
    tom_preferido: Optional[str] = None
    profundidade: Optional[str] = None
    usa_emoji: Optional[bool] = None

    # Configurações
    tema: Optional[str] = None  # "light" ou "dark"
    horario_lembrete: Optional[str] = None  # formato "HH:MM"
    notificacoes_ativas: Optional[bool] = None


class OnboardingStep1(BaseModel):
    """Como a pessoa quer ser chamada"""
    nome: str
    apelido: Optional[str] = None


class OnboardingStep2(BaseModel):
    """Jornada de fé"""
    tempo_de_fe: str  # "recém-convertido", "menos de 1 ano", "1-5 anos", "5-10 anos", "mais de 10 anos", "desde criança"
    batizado: Optional[bool] = None
    denominacao: Optional[str] = None


class OnboardingStep3(BaseModel):
    """O que trouxe ao SoulHaven"""
    motivo_principal: str  # "ansiedade", "relacionamento", "fé", "estudo", "apoio", "outro"
    expectativa: Optional[str] = None


class ProfileResponse(BaseModel):
    nome: Optional[str]
    apelido: Optional[str]
    idade: Optional[int]
    estado_civil: Optional[str]
    denominacao: Optional[str]
    tempo_de_fe: Optional[str]
    batizado: Optional[bool]
    tom_preferido: str
    usa_emoji: bool
    onboarding_completed: bool


# ============================================
# ROTAS
# ============================================

@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Retorna o perfil do usuário"""
    profile = await db.get_user_profile(current_user["user_id"])

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    # Verifica se onboarding foi completado
    onboarding_completed = bool(profile.get("nome") and profile.get("tempo_de_fe"))

    return ProfileResponse(
        nome=profile.get("nome"),
        apelido=profile.get("apelido"),
        idade=profile.get("idade"),
        estado_civil=profile.get("estado_civil"),
        denominacao=profile.get("denominacao"),
        tempo_de_fe=profile.get("tempo_de_fe"),
        batizado=profile.get("batizado"),
        tom_preferido=profile.get("tom_preferido", "equilibrado"),
        usa_emoji=profile.get("usa_emoji", True),
        onboarding_completed=onboarding_completed
    )


@router.patch("/")
async def update_profile(
    update: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Atualiza o perfil do usuário"""
    # Filtra campos não nulos
    update_data = {k: v for k, v in update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    profile = await db.update_user_profile(
        user_id=current_user["user_id"],
        **update_data
    )

    await db.log_audit(
        user_id=current_user["user_id"],
        action="profile_updated",
        details={"fields": list(update_data.keys())}
    )

    return {"message": "Perfil atualizado", "updated_fields": list(update_data.keys())}


# ============================================
# ONBOARDING (Fluxo guiado)
# ============================================

@router.post("/onboarding/step1")
async def onboarding_step1(
    data: OnboardingStep1,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Passo 1 do onboarding: Nome e apelido
    """
    await db.update_user_profile(
        user_id=current_user["user_id"],
        nome=data.nome,
        apelido=data.apelido or data.nome
    )

    return {
        "message": f"Prazer em te conhecer, {data.apelido or data.nome}!",
        "next_step": "step2"
    }


@router.post("/onboarding/step2")
async def onboarding_step2(
    data: OnboardingStep2,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Passo 2 do onboarding: Jornada de fé
    """
    update_data = {"tempo_de_fe": data.tempo_de_fe}

    if data.batizado is not None:
        update_data["batizado"] = data.batizado

    if data.denominacao:
        update_data["denominacao"] = data.denominacao

    await db.update_user_profile(
        user_id=current_user["user_id"],
        **update_data
    )

    # Mensagem personalizada baseada no tempo de fé
    if data.tempo_de_fe in ["recém-convertido", "menos de 1 ano"]:
        msg = "Que alegria saber que você começou essa jornada! Estou aqui pra caminhar com você."
    elif data.tempo_de_fe == "desde criança":
        msg = "Que bênção crescer conhecendo o Senhor! Sua história com Ele é preciosa."
    else:
        msg = "Que bom saber mais sobre sua caminhada. Cada pessoa tem uma história única com Deus."

    return {
        "message": msg,
        "next_step": "step3"
    }


@router.post("/onboarding/step3")
async def onboarding_step3(
    data: OnboardingStep3,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Passo 3 do onboarding: Motivação
    """
    # Mapeia motivo para possíveis lutas
    motivo_to_luta = {
        "ansiedade": ["ansiedade"],
        "relacionamento": ["relacionamentos"],
        "fé": ["dúvidas de fé"],
        "estudo": [],
        "apoio": ["solidão"],
    }

    lutas = motivo_to_luta.get(data.motivo_principal, [])

    if lutas:
        await db.update_user_profile(
            user_id=current_user["user_id"],
            lutas=lutas
        )

    # Salva como insight inicial
    if data.expectativa:
        await db.save_insight(
            user_id=current_user["user_id"],
            categoria="preferencia",
            insight=f"Expectativa inicial: {data.expectativa}",
            confianca=0.9
        )

    # Mensagem personalizada
    messages = {
        "ansiedade": "Entendo. A ansiedade é pesada, mas você não precisa carregar isso sozinho(a). Estou aqui.",
        "relacionamento": "Relacionamentos são desafiadores. Vamos conversar sobre isso quando você quiser.",
        "fé": "Dúvidas fazem parte da jornada. Aqui é um espaço seguro pra explorar sua fé.",
        "estudo": "Que bom! Estudar a Palavra juntos vai ser uma aventura.",
        "apoio": "Às vezes só precisamos de alguém pra ouvir. Estou aqui pra isso.",
        "outro": "Seja qual for o motivo, estou aqui pra caminhar com você."
    }

    return {
        "message": messages.get(data.motivo_principal, messages["outro"]),
        "onboarding_complete": True,
        "next_step": "chat"
    }


@router.get("/onboarding/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Verifica o status do onboarding
    """
    profile = await db.get_user_profile(current_user["user_id"])

    if not profile:
        return {"completed": False, "current_step": "step1"}

    if not profile.get("nome"):
        return {"completed": False, "current_step": "step1"}

    if not profile.get("tempo_de_fe"):
        return {"completed": False, "current_step": "step2"}

    # Se tem nome e tempo_de_fe, considera completo
    return {"completed": True, "current_step": None}


@router.delete("/delete-account")
async def delete_account(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Exclui permanentemente a conta do usuario e todos os dados associados.
    Esta acao e irreversivel.
    """
    user_id = current_user["user_id"]

    try:
        # Log de auditoria antes de excluir
        await db.log_audit(
            user_id=user_id,
            action="account_deletion_requested",
            details={"ip": "user_request"}
        )

        # Excluir dados na ordem correta (respeitando foreign keys)
        # 1. Excluir mensagens das conversas
        await db.pool.execute("""
            DELETE FROM messages WHERE conversation_id IN (
                SELECT id FROM conversations WHERE user_id = $1
            )
        """, user_id)

        # 2. Excluir conversas
        await db.pool.execute(
            "DELETE FROM conversations WHERE user_id = $1",
            user_id
        )

        # 3. Excluir perfil
        await db.pool.execute(
            "DELETE FROM user_profiles WHERE user_id = $1",
            user_id
        )

        # 4. Excluir tokens de reset de senha
        await db.pool.execute(
            "DELETE FROM password_reset_tokens WHERE user_id = $1",
            user_id
        )

        # 5. Excluir logs de auditoria (opcional - pode manter para compliance)
        await db.pool.execute(
            "DELETE FROM audit_logs WHERE user_id = $1",
            user_id
        )

        # 6. Excluir usuario
        await db.pool.execute(
            "DELETE FROM users WHERE id = $1",
            user_id
        )

        return {"message": "Conta excluida com sucesso"}

    except Exception as e:
        print(f"[PROFILE] Erro ao excluir conta: {e}")
        raise HTTPException(status_code=500, detail="Erro ao excluir conta. Tente novamente.")

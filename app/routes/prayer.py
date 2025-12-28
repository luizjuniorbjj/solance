"""
SoulHaven - Rotas de Pedidos de Oração
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database

router = APIRouter(prefix="/prayer", tags=["Oração"])


# ============================================
# MODELOS
# ============================================

class PrayerRequestCreate(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    categoria: Optional[str] = None  # saúde, família, trabalho, relacionamento, espiritual, outro


class PrayerRequestResponse(BaseModel):
    id: str
    titulo: str
    descricao: Optional[str]
    categoria: Optional[str]
    status: str
    created_at: str
    data_resposta: Optional[str]


class MarkAnsweredRequest(BaseModel):
    testemunho: Optional[str] = None


# ============================================
# ROTAS
# ============================================

@router.post("/", response_model=PrayerRequestResponse)
async def create_prayer_request(
    request: PrayerRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Cria novo pedido de oração
    """
    if not request.titulo.strip():
        raise HTTPException(status_code=400, detail="Título é obrigatório")

    prayer = await db.create_prayer_request(
        user_id=current_user["user_id"],
        titulo=request.titulo,
        descricao=request.descricao,
        categoria=request.categoria
    )

    await db.log_audit(
        user_id=current_user["user_id"],
        action="prayer_created",
        details={"categoria": request.categoria}
    )

    return PrayerRequestResponse(
        id=str(prayer["id"]),
        titulo=prayer["titulo"],
        descricao=request.descricao,  # Já descriptografado
        categoria=prayer.get("categoria"),
        status=prayer["status"],
        created_at=prayer["created_at"].isoformat(),
        data_resposta=None
    )


@router.get("/", response_model=List[PrayerRequestResponse])
async def list_prayer_requests(
    status: Optional[str] = None,  # ativo, respondido, arquivado
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Lista pedidos de oração do usuário
    """
    if status == "ativo" or status is None:
        prayers = await db.get_active_prayer_requests(current_user["user_id"])
    else:
        # Buscar por status específico
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM prayer_requests
                WHERE user_id = $1 AND status = $2
                ORDER BY created_at DESC
                """,
                current_user["user_id"], status
            )
            prayers = [dict(row) for row in rows]

    return [
        PrayerRequestResponse(
            id=str(p["id"]),
            titulo=p["titulo"],
            descricao=p.get("descricao"),
            categoria=p.get("categoria"),
            status=p["status"],
            created_at=p["created_at"].isoformat(),
            data_resposta=p["data_resposta"].isoformat() if p.get("data_resposta") else None
        )
        for p in prayers
    ]


@router.post("/{prayer_id}/answered")
async def mark_prayer_answered(
    prayer_id: str,
    request: MarkAnsweredRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Marca pedido de oração como respondido
    """
    await db.mark_prayer_answered(
        prayer_id=prayer_id,
        user_id=current_user["user_id"],
        testemunho=request.testemunho
    )

    await db.log_audit(
        user_id=current_user["user_id"],
        action="prayer_answered",
        details={"prayer_id": prayer_id}
    )

    return {"message": "Que bênção! Pedido marcado como respondido."}


@router.delete("/{prayer_id}")
async def delete_prayer_request(
    prayer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Remove pedido de oração
    """
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM prayer_requests WHERE id = $1 AND user_id = $2",
            prayer_id, current_user["user_id"]
        )

    return {"message": "Pedido removido"}

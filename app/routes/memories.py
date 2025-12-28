"""
SoulHaven - Rotas de Gerenciamento de Memórias
Permite ao usuário ver, corrigir e apagar suas memórias
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.database import Database, get_db
from app.auth import get_current_user


router = APIRouter(prefix="/memories", tags=["Memórias"])


# ============================================
# SCHEMAS
# ============================================

class MemoryResponse(BaseModel):
    id: str
    categoria: str
    fato: str
    detalhes: Optional[str]
    importancia: int
    mencoes: int
    status: str
    created_at: str

class MemoriesListResponse(BaseModel):
    total: int
    memories: List[MemoryResponse]
    categorias: dict

class MemoryUpdateRequest(BaseModel):
    fato: Optional[str] = None
    detalhes: Optional[str] = None
    importancia: Optional[int] = None


# ============================================
# ENDPOINTS
# ============================================

@router.get("", response_model=MemoriesListResponse)
async def list_memories(
    categoria: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Lista todas as memórias do usuário.
    O usuário pode filtrar por categoria.
    """
    user_id = current_user["user_id"]

    memories = await db.get_user_memories(user_id, categoria=categoria, limit=limit)

    # Contar por categoria
    categorias = {}
    for mem in memories:
        cat = mem["categoria"]
        categorias[cat] = categorias.get(cat, 0) + 1

    return {
        "total": len(memories),
        "memories": [
            {
                "id": str(mem["id"]),
                "categoria": mem["categoria"],
                "fato": mem["fato"],
                "detalhes": mem.get("detalhes"),
                "importancia": mem["importancia"],
                "mencoes": mem["mencoes"],
                "status": mem.get("status", "active"),
                "created_at": mem["created_at"].isoformat() if mem.get("created_at") else ""
            }
            for mem in memories
        ],
        "categorias": categorias
    }


@router.get("/{memory_id}")
async def get_memory(
    memory_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Retorna uma memória específica.
    """
    user_id = current_user["user_id"]

    async with db.pool.acquire() as conn:
        memory = await conn.fetchrow(
            "SELECT * FROM user_memories WHERE id = $1 AND user_id = $2",
            memory_id, user_id
        )

    if not memory:
        raise HTTPException(status_code=404, detail="Memória não encontrada")

    return {
        "id": str(memory["id"]),
        "categoria": memory["categoria"],
        "fato": memory["fato"],
        "detalhes": memory.get("detalhes"),
        "importancia": memory["importancia"],
        "mencoes": memory["mencoes"],
        "status": memory.get("status", "active"),
        "created_at": memory["created_at"].isoformat() if memory.get("created_at") else ""
    }


@router.patch("/{memory_id}")
async def update_memory(
    memory_id: UUID,
    update: MemoryUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Corrige uma memória existente.
    O usuário pode corrigir o fato, detalhes ou importância.
    """
    user_id = current_user["user_id"]

    async with db.pool.acquire() as conn:
        # Verificar se existe e pertence ao usuário
        memory = await conn.fetchrow(
            "SELECT * FROM user_memories WHERE id = $1 AND user_id = $2",
            memory_id, user_id
        )

        if not memory:
            raise HTTPException(status_code=404, detail="Memória não encontrada")

        # Construir update dinâmico
        updates = []
        params = [memory_id]
        param_idx = 2

        if update.fato is not None:
            updates.append(f"fato = ${param_idx}")
            params.append(update.fato)
            param_idx += 1

        if update.detalhes is not None:
            updates.append(f"detalhes = ${param_idx}")
            params.append(update.detalhes)
            param_idx += 1

        if update.importancia is not None:
            updates.append(f"importancia = ${param_idx}")
            params.append(update.importancia)
            param_idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

        updates.append("validado = TRUE")  # Marcar como validado pelo usuário

        query = f"UPDATE user_memories SET {', '.join(updates)} WHERE id = $1"
        await conn.execute(query, *params)

    return {"message": "Memória atualizada", "id": str(memory_id)}


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Apaga (desativa) uma memória.
    O usuário pode pedir para a IA "esquecer" algo.
    """
    user_id = current_user["user_id"]

    await db.deactivate_memory(str(memory_id), user_id)

    return {"message": "Memória esquecida", "id": str(memory_id)}


@router.delete("")
async def delete_all_memories(
    categoria: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Apaga todas as memórias do usuário (ou de uma categoria específica).
    Cuidado: esta ação não pode ser desfeita!
    """
    user_id = current_user["user_id"]

    async with db.pool.acquire() as conn:
        if categoria:
            result = await conn.execute(
                """
                UPDATE user_memories
                SET status = 'deactivated', is_active = FALSE
                WHERE user_id = $1 AND categoria = $2 AND status = 'active'
                """,
                user_id, categoria
            )
        else:
            result = await conn.execute(
                """
                UPDATE user_memories
                SET status = 'deactivated', is_active = FALSE
                WHERE user_id = $1 AND status = 'active'
                """,
                user_id
            )

    return {
        "message": f"Memórias esquecidas" + (f" da categoria {categoria}" if categoria else ""),
        "categoria": categoria
    }


@router.get("/export/json")
async def export_memories(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Exporta todas as memórias do usuário em formato JSON (LGPD).
    """
    user_id = current_user["user_id"]

    memories = await db.get_user_memories(user_id, limit=1000)

    return {
        "user_id": user_id,
        "total": len(memories),
        "exported_at": "now",
        "memories": [
            {
                "categoria": mem["categoria"],
                "fato": mem["fato"],
                "detalhes": mem.get("detalhes"),
                "importancia": mem["importancia"],
                "mencoes": mem["mencoes"],
                "criado_em": mem["created_at"].isoformat() if mem.get("created_at") else ""
            }
            for mem in memories
        ]
    }

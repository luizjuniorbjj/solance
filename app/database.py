"""
SoulHaven - Camada de Banco de Dados
Abstração para PostgreSQL/Supabase
"""

import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from uuid import UUID

import asyncpg
from app.config import DATABASE_URL
from app.security import encrypt_data, decrypt_data


class UUIDEncoder(json.JSONEncoder):
    """JSON Encoder que suporta UUID"""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class Database:
    """
    Classe de abstração do banco de dados
    """

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # ============================================
    # USERS
    # ============================================

    async def create_user(
        self,
        email: str,
        password_hash: Optional[str],
        nome: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        oauth_id: Optional[str] = None,
        accepted_terms: bool = False
    ) -> dict:
        """Cria novo usuário (com senha ou OAuth)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (
                    email, password_hash, oauth_provider, oauth_id,
                    accepted_terms, accepted_terms_at, accepted_privacy, accepted_privacy_at
                )
                VALUES ($1, $2, $3, $4, $5, CASE WHEN $5 THEN NOW() ELSE NULL END, $5, CASE WHEN $5 THEN NOW() ELSE NULL END)
                RETURNING id, email, is_active, is_premium, created_at
                """,
                email, password_hash, oauth_provider, oauth_id, accepted_terms
            )
            return dict(row)

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Busca usuário por email"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )
            return dict(row) if row else None

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Busca usuário por ID"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_uuid
            )
            return dict(row) if row else None

    async def update_last_login(self, user_id: str):
        """Atualiza último login"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_login = NOW() WHERE id = $1",
                user_uuid
            )

    async def increment_message_count(self, user_id: str):
        """Incrementa contador de mensagens"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users
                SET total_messages = total_messages + 1,
                    trial_messages_used = trial_messages_used + 1
                WHERE id = $1
                """,
                user_uuid
            )

    async def increment_trial_messages(self, user_id: str):
        """Incrementa apenas o contador de trial (usado para limites free)"""
        await self.increment_message_count(user_id)

    # ============================================
    # USER PROFILES
    # ============================================

    async def create_user_profile(self, user_id: str, nome: Optional[str] = None) -> dict:
        """Cria perfil do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_profiles (user_id, nome)
                VALUES ($1, $2)
                RETURNING *
                """,
                user_uuid, nome
            )
            return dict(row)

    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Busca perfil do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1",
                user_uuid
            )
            if not row:
                return None

            profile = dict(row)

            # Descriptografa campos sensíveis
            if profile.get("lutas_encrypted"):
                profile["lutas"] = json.loads(
                    decrypt_data(profile["lutas_encrypted"], user_id)
                )
            else:
                profile["lutas"] = []

            return profile

    async def update_user_profile(self, user_id: str, **kwargs) -> dict:
        """Atualiza perfil do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        # Campos que precisam ser criptografados
        if "lutas" in kwargs:
            kwargs["lutas_encrypted"] = encrypt_data(
                json.dumps(kwargs.pop("lutas")), user_id
            )

        # Monta query dinamicamente
        set_clauses = []
        values = []
        for i, (key, value) in enumerate(kwargs.items(), 1):
            set_clauses.append(f"{key} = ${i}")
            values.append(value)

        values.append(user_uuid)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                UPDATE user_profiles
                SET {', '.join(set_clauses)}
                WHERE user_id = ${len(values)}
                RETURNING *
                """,
                *values
            )
            return dict(row) if row else {}

    # ============================================
    # CONVERSATIONS
    # ============================================

    async def create_conversation(self, user_id: str) -> dict:
        """Cria nova conversa"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversations (user_id)
                VALUES ($1)
                RETURNING *
                """,
                user_uuid
            )
            return dict(row)

    async def get_conversation(self, conversation_id: str, user_id: str = None) -> Optional[dict]:
        """Busca conversa por ID. Se user_id fornecido, valida propriedade."""
        conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        async with self.pool.acquire() as conn:
            if user_id:
                # Busca segura: valida que conversa pertence ao usuario
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                row = await conn.fetchrow(
                    "SELECT * FROM conversations WHERE id = $1 AND user_id = $2",
                    conv_uuid, user_uuid
                )
            else:
                # Busca sem validacao (para uso interno/admin)
                row = await conn.fetchrow(
                    "SELECT * FROM conversations WHERE id = $1",
                    conv_uuid
                )
            return dict(row) if row else None

    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[dict]:
        """Busca conversas recentes do usuário"""
        async with self.pool.acquire() as conn:
            # Converter string para UUID se necessário
            uid = UUID(user_id) if isinstance(user_id, str) else user_id
            rows = await conn.fetch(
                """
                SELECT * FROM conversations
                WHERE user_id = $1 AND is_archived = FALSE
                ORDER BY last_message_at DESC
                LIMIT $2
                """,
                uid, limit
            )
            return [dict(row) for row in rows]

    async def update_conversation_summary(
        self,
        conversation_id: str,
        resumo: str,
        temas: List[str] = None,
        humor_final: str = None
    ):
        """Atualiza resumo da conversa"""
        conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE conversations
                SET resumo = $2,
                    temas = $3,
                    humor_final = $4,
                    last_message_at = NOW(),
                    message_count = message_count + 1
                WHERE id = $1
                """,
                conv_uuid, resumo, json.dumps(temas or []), humor_final
            )

    # ============================================
    # MESSAGES
    # ============================================

    async def save_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        tokens_used: int = 0,
        model_used: str = None
    ) -> dict:
        """Salva mensagem criptografada e atualiza contador da conversa"""
        conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        encrypted_content = encrypt_data(content, user_id)

        async with self.pool.acquire() as conn:
            # Salvar mensagem
            row = await conn.fetchrow(
                """
                INSERT INTO messages (conversation_id, user_id, role, content_encrypted, tokens_used, model_used)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, role, created_at
                """,
                conv_uuid, user_uuid, role, encrypted_content, tokens_used, model_used
            )

            # Atualizar contador e timestamp da conversa
            await conn.execute(
                """
                UPDATE conversations
                SET message_count = message_count + 1,
                    last_message_at = NOW()
                WHERE id = $1
                """,
                conv_uuid
            )

            return dict(row)

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Busca mensagens de uma conversa (descriptografadas)"""
        conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Dupla verificacao: filtra por conversation_id E user_id
            rows = await conn.fetch(
                """
                SELECT * FROM messages
                WHERE conversation_id = $1 AND user_id = $2
                ORDER BY created_at ASC
                LIMIT $3
                """,
                conv_uuid, user_uuid, limit
            )

            messages = []
            for row in rows:
                msg = dict(row)
                msg["content"] = decrypt_data(msg["content_encrypted"], user_id)
                del msg["content_encrypted"]
                messages.append(msg)

            return messages

    # ============================================
    # PRAYER REQUESTS
    # ============================================

    async def create_prayer_request(
        self,
        user_id: str,
        titulo: str,
        descricao: str = None,
        categoria: str = None
    ) -> dict:
        """Cria pedido de oração"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        descricao_encrypted = encrypt_data(descricao, user_id) if descricao else None

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO prayer_requests (user_id, titulo, descricao_encrypted, categoria)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                user_uuid, titulo, descricao_encrypted, categoria
            )
            return dict(row)

    async def get_active_prayer_requests(self, user_id: str) -> List[dict]:
        """Busca pedidos de oração ativos"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM prayer_requests
                WHERE user_id = $1 AND status = 'ativo'
                ORDER BY created_at DESC
                """,
                user_uuid
            )

            requests = []
            for row in rows:
                req = dict(row)
                if req.get("descricao_encrypted"):
                    req["descricao"] = decrypt_data(req["descricao_encrypted"], user_id)
                requests.append(req)

            return requests

    async def mark_prayer_answered(self, prayer_id: str, user_id: str, testemunho: str = None):
        """Marca pedido como respondido"""
        prayer_uuid = UUID(prayer_id) if isinstance(prayer_id, str) else prayer_id
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        testemunho_encrypted = encrypt_data(testemunho, user_id) if testemunho else None

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE prayer_requests
                SET status = 'respondido',
                    data_resposta = CURRENT_DATE,
                    testemunho_encrypted = $3
                WHERE id = $1 AND user_id = $2
                """,
                prayer_uuid, user_uuid, testemunho_encrypted
            )

    # ============================================
    # USER INSIGHTS
    # ============================================

    async def save_insight(
        self,
        user_id: str,
        categoria: str,
        insight: str,
        confianca: float = 0.8,
        conversa_id: str = None
    ):
        """Salva insight sobre o usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        conv_uuid = UUID(conversa_id) if conversa_id and isinstance(conversa_id, str) else conversa_id
        insight_encrypted = encrypt_data(insight, user_id)

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_insights (user_id, categoria, insight_encrypted, confianca, origem_conversa_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_uuid, categoria, insight_encrypted, confianca, conv_uuid
            )

    async def get_user_insights(self, user_id: str) -> List[dict]:
        """Busca insights ativos do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM user_insights
                WHERE user_id = $1 AND is_active = TRUE
                ORDER BY confianca DESC, created_at DESC
                """,
                user_uuid
            )

            insights = []
            for row in rows:
                ins = dict(row)
                ins["insight"] = decrypt_data(ins["insight_encrypted"], user_id)
                insights.append(ins)

            return insights

    # ============================================
    # USER MEMORIES (Memória Eterna)
    # ============================================

    # Campos semânticos para detecção de conflitos
    # Se uma nova memória contém keywords de um campo, deve substituir memórias antigas do mesmo campo
    SEMANTIC_CONFLICT_FIELDS = {
        "LOCALIZACAO": {
            "keywords": ["mora", "morando", "vive", "vivendo", "mudou", "mudei", "reside", "país", "cidade", "estado", "florida", "brasil", "eua", "estados unidos"],
            "categories": ["CONTEXTO", "IDENTIDADE", "EVENTO"]
        },
        "EMPREGO": {
            "keywords": ["trabalha", "trabalhando", "emprego", "empresa", "profissão", "cargo", "demitido", "contratado", "desempregado"],
            "categories": ["CONTEXTO", "IDENTIDADE"]
        },
        "ESTADO_CIVIL": {
            "keywords": ["casou", "casado", "casada", "solteiro", "solteira", "divorciado", "divorciada", "separado", "noivo", "noiva", "viúvo", "viúva"],
            "categories": ["FAMILIA", "IDENTIDADE", "EVENTO"]
        },
        "IGREJA": {
            "keywords": ["igreja", "congregação", "frequenta", "membro", "batizado", "converteu"],
            "categories": ["FE"]
        },
        "IDADE": {
            "keywords": ["anos", "idade", "nasceu", "aniversário"],
            "categories": ["IDENTIDADE"]
        }
    }

    def _detect_semantic_field(self, fato: str, categoria: str) -> Optional[str]:
        """
        Detecta qual campo semântico um fato pertence.
        Retorna None se não pertencer a nenhum campo de conflito.
        """
        fato_lower = fato.lower()
        for field_name, field_info in self.SEMANTIC_CONFLICT_FIELDS.items():
            # Verificar se categoria é relevante
            if categoria not in field_info["categories"]:
                continue
            # Verificar se contém keywords do campo
            for kw in field_info["keywords"]:
                if kw in fato_lower:
                    return field_name
        return None

    async def _find_conflicting_memories(
        self,
        conn,
        user_id: str,
        categoria: str,
        semantic_field: str
    ) -> List[dict]:
        """
        Busca memórias que podem conflitar com uma nova memória do mesmo campo semântico.
        """
        field_info = self.SEMANTIC_CONFLICT_FIELDS.get(semantic_field)
        if not field_info:
            return []

        # Buscar memórias ativas da mesma categoria que contêm keywords do campo
        rows = await conn.fetch(
            """
            SELECT id, fato, categoria FROM user_memories
            WHERE user_id = $1
            AND categoria = ANY($2)
            AND status = 'active'
            """,
            user_id, field_info["categories"]
        )

        # Filtrar por keywords
        conflicting = []
        for row in rows:
            fato_lower = row["fato"].lower()
            for kw in field_info["keywords"]:
                if kw in fato_lower:
                    conflicting.append(dict(row))
                    break

        return conflicting

    async def save_memory(
        self,
        user_id: str,
        categoria: str,
        fato: str,
        detalhes: str = None,
        importancia: int = 5,
        conversa_id: str = None,
        action: str = "upsert",  # upsert, supersede, deactivate
        supersedes_id: str = None,
        confidence: float = 0.8,
        payload: dict = None
    ) -> dict:
        """
        Salva um fato na memória eterna do usuário.

        Actions:
        - upsert: Cria novo ou incrementa menções se existir similar
        - supersede: Cria novo e marca o antigo como superseded
        - deactivate: Apenas desativa uma memória existente

        NOVO: Detecta conflitos semânticos automaticamente!
        Ex: "Mora na Florida" conflita com "Mora no Brasil" mesmo sendo textos diferentes.
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        conv_uuid = UUID(conversa_id) if conversa_id and isinstance(conversa_id, str) else conversa_id
        supersedes_uuid = UUID(supersedes_id) if supersedes_id and isinstance(supersedes_id, str) else supersedes_id
        async with self.pool.acquire() as conn:
            # Se ação é deactivate, apenas desativa
            if action == "deactivate" and supersedes_uuid:
                await conn.execute(
                    "UPDATE user_memories SET status = 'deactivated', is_active = FALSE WHERE id = $1 AND user_id = $2",
                    supersedes_uuid, user_uuid
                )
                return {"id": supersedes_id, "deactivated": True}

            # Normalizar o fato para comparação (função do banco)
            fato_norm = await conn.fetchval("SELECT normalize_text($1)", fato)

            # NOVO: Detectar campo semântico para conflitos
            semantic_field = self._detect_semantic_field(fato, categoria)

            # Se pertence a um campo semântico, buscar e desativar conflitos
            superseded_ids = []
            if semantic_field:
                conflicting = await self._find_conflicting_memories(
                    conn, user_uuid, categoria, semantic_field
                )
                for conf in conflicting:
                    # Não desativar se for exatamente o mesmo fato
                    conf_norm = await conn.fetchval("SELECT normalize_text($1)", conf["fato"])
                    if conf_norm != fato_norm:
                        # Desativar memória conflitante
                        await conn.execute(
                            """
                            UPDATE user_memories
                            SET status = 'superseded', is_active = FALSE
                            WHERE id = $1
                            """,
                            conf["id"]
                        )
                        superseded_ids.append(str(conf["id"]))
                        print(f"[MEMORY] Superseded conflicting fact: '{conf['fato']}' -> '{fato}'")

            # Buscar memória similar usando fato_normalizado (melhor dedupe)
            existing = await conn.fetchrow(
                """
                SELECT id, mencoes, fato FROM user_memories
                WHERE user_id = $1
                AND categoria = $2
                AND fato_normalizado = $3
                AND status = 'active'
                """,
                user_uuid, categoria, fato_norm
            )

            if existing:
                if action == "supersede":
                    # Marcar antigo como superseded e criar novo
                    await conn.execute(
                        "UPDATE user_memories SET status = 'superseded', is_active = FALSE WHERE id = $1",
                        existing["id"]
                    )
                    # Continua para criar o novo abaixo
                else:
                    # upsert: Atualizar menções e última menção
                    await conn.execute(
                        """
                        UPDATE user_memories
                        SET mencoes = mencoes + 1,
                            ultima_mencao = NOW(),
                            detalhes = COALESCE($2, detalhes),
                            confidence = GREATEST(confidence, $3)
                        WHERE id = $1
                        """,
                        existing["id"], detalhes, confidence
                    )
                    return {
                        "id": str(existing["id"]),
                        "updated": True,
                        "mencoes": existing["mencoes"] + 1,
                        "superseded": superseded_ids
                    }

            # Criar nova memória
            row = await conn.fetchrow(
                """
                INSERT INTO user_memories (
                    user_id, categoria, fato, detalhes, importancia,
                    origem_conversa_id, supersedes_id, confidence, payload
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                user_uuid, categoria, fato, detalhes, importancia,
                conv_uuid, supersedes_uuid if action == "supersede" else None,
                confidence, json.dumps(payload) if payload else None
            )
            return {"id": str(row["id"]), "created": True, "superseded": superseded_ids}

    async def get_user_memories(
        self,
        user_id: str,
        categoria: str = None,
        limit: int = 50
    ) -> List[dict]:
        """Busca memórias do usuário, ordenadas por importância"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            if categoria:
                rows = await conn.fetch(
                    """
                    SELECT * FROM user_memories
                    WHERE user_id = $1 AND categoria = $2 AND status = 'active'
                    ORDER BY importancia DESC, ultima_mencao DESC
                    LIMIT $3
                    """,
                    user_uuid, categoria, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM user_memories
                    WHERE user_id = $1 AND status = 'active'
                    ORDER BY importancia DESC, ultima_mencao DESC
                    LIMIT $2
                    """,
                    user_uuid, limit
                )
            return [dict(row) for row in rows]

    async def get_relevant_memories(
        self,
        user_id: str,
        current_message: str = "",
        top_k: int = 20
    ) -> List[dict]:
        """
        Busca memórias RELEVANTES para o contexto atual usando full-text search + scoring.
        Não traz tudo - apenas Top-K mais relevantes.
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            if current_message and len(current_message) > 5:
                # Busca híbrida: relevância textual + importância + recência
                rows = await conn.fetch(
                    """
                    WITH scored_memories AS (
                        SELECT *,
                            -- Score de relevância textual (0-1)
                            COALESCE(
                                ts_rank(
                                    to_tsvector('portuguese', fato || ' ' || COALESCE(detalhes, '')),
                                    plainto_tsquery('portuguese', $2)
                                ),
                                0
                            ) as text_score,
                            -- Recência normalizada (0-1) - memórias recentes têm mais peso
                            CASE
                                WHEN ultima_mencao > NOW() - INTERVAL '1 day' THEN 1.0
                                WHEN ultima_mencao > NOW() - INTERVAL '7 days' THEN 0.8
                                WHEN ultima_mencao > NOW() - INTERVAL '30 days' THEN 0.5
                                ELSE 0.2
                            END as recency_score
                        FROM user_memories
                        WHERE user_id = $1 AND status = 'active'
                    )
                    SELECT *,
                        -- Score final ponderado
                        (
                            text_score * 0.35 +
                            (importancia::float / 10.0) * 0.35 +
                            recency_score * 0.15 +
                            LEAST(mencoes::float / 5.0, 1.0) * 0.15
                        ) as final_score
                    FROM scored_memories
                    ORDER BY final_score DESC, importancia DESC
                    LIMIT $3
                    """,
                    user_uuid, current_message, top_k
                )
            else:
                # Sem contexto: prioriza importância + recência
                rows = await conn.fetch(
                    """
                    SELECT *,
                        (
                            (importancia::float / 10.0) * 0.5 +
                            CASE
                                WHEN ultima_mencao > NOW() - INTERVAL '7 days' THEN 0.3
                                ELSE 0.1
                            END +
                            LEAST(mencoes::float / 5.0, 1.0) * 0.2
                        ) as final_score
                    FROM user_memories
                    WHERE user_id = $1 AND status = 'active'
                    ORDER BY final_score DESC, importancia DESC
                    LIMIT $2
                    """,
                    user_uuid, top_k
                )
            return [dict(row) for row in rows]

    async def get_all_memories_formatted(
        self,
        user_id: str,
        current_message: str = "",
        top_k: int = 20
    ) -> str:
        """
        Retorna memórias RELEVANTES formatadas para o prompt da IA.
        Usa Top-K por relevância, não traz tudo.
        """
        # Buscar memórias relevantes (não todas!)
        memories = await self.get_relevant_memories(user_id, current_message, top_k)

        # Agrupar por categoria
        by_category = {}
        for mem in memories:
            cat = mem["categoria"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mem)

        category_labels = {
            "IDENTIDADE": "Quem é",
            "FAMILIA": "Família",
            "EVENTO": "Eventos importantes",
            "LUTA": "Lutas e dificuldades",
            "VITORIA": "Vitórias e conquistas",
            "PREFERENCIA": "Preferências",
            "FE": "Vida espiritual",
            "CONTEXTO": "Situação atual"
        }

        if not memories:
            return ""

        result = "=== O QUE VOCÊ SABE SOBRE ESTA PESSOA ===\n"

        for cat, mems in by_category.items():
            label = category_labels.get(cat, cat)
            result += f"[{label}]\n"
            for mem in mems:
                result += f"  • {mem['fato']}"
                if mem["mencoes"] > 1:
                    result += f" (mencionou {mem['mencoes']}x)"
                result += "\n"
            result += "\n"

        result += "Use essas informações naturalmente na conversa.\n"

        return result

    async def update_memory_mention(self, memory_id: str):
        """Atualiza contagem de menções de uma memória"""
        mem_uuid = UUID(memory_id) if isinstance(memory_id, str) else memory_id
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_memories
                SET mencoes = mencoes + 1, ultima_mencao = NOW()
                WHERE id = $1
                """,
                mem_uuid
            )

    async def deactivate_memory(self, memory_id: str, user_id: str):
        """Desativa uma memória (soft delete)"""
        mem_uuid = UUID(memory_id) if isinstance(memory_id, str) else memory_id
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_memories
                SET is_active = FALSE
                WHERE id = $1 AND user_id = $2
                """,
                mem_uuid, user_uuid
            )

    # ============================================
    # PSYCHOLOGICAL PROFILE
    # ============================================

    async def get_psychological_profile(self, user_id: str) -> Optional[dict]:
        """Busca perfil psicológico do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_psychological_profile WHERE user_id = $1",
                user_uuid
            )
            return dict(row) if row else None

    async def save_psychological_profile(
        self,
        user_id: str,
        profile_data: dict
    ) -> dict:
        """Salva ou atualiza perfil psicológico do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Verificar se já existe
            existing = await conn.fetchrow(
                "SELECT id FROM user_psychological_profile WHERE user_id = $1",
                user_uuid
            )

            if existing:
                # Atualizar existente
                await conn.execute(
                    """
                    UPDATE user_psychological_profile SET
                        communication_style = COALESCE($2, communication_style),
                        primary_needs = COALESCE($3, primary_needs),
                        thinking_patterns = COALESCE($4, thinking_patterns),
                        emotional_triggers = COALESCE($5, emotional_triggers),
                        coping_mechanisms = COALESCE($6, coping_mechanisms),
                        faith_stage = COALESCE($7, faith_stage),
                        love_language = COALESCE($8, love_language),
                        temperament = COALESCE($9, temperament),
                        emotional_openness = COALESCE($10, emotional_openness),
                        self_awareness = COALESCE($11, self_awareness),
                        resilience_level = COALESCE($12, resilience_level),
                        baseline_anxiety = COALESCE($13, baseline_anxiety),
                        attachment_style = COALESCE($14, attachment_style),
                        accumulated_insights = COALESCE($15, '') || E'\\n' || accumulated_insights,
                        recommended_approach = COALESCE($16, recommended_approach),
                        last_analysis_at = NOW(),
                        analysis_count = analysis_count + 1,
                        confidence_score = LEAST(confidence_score + 0.05, 0.95),
                        updated_at = NOW()
                    WHERE user_id = $1
                    """,
                    user_uuid,
                    profile_data.get("communication_style"),
                    profile_data.get("primary_needs"),
                    json.dumps(profile_data.get("thinking_patterns", {})),
                    profile_data.get("emotional_triggers"),
                    profile_data.get("coping_mechanisms"),
                    profile_data.get("faith_stage"),
                    profile_data.get("love_language"),
                    profile_data.get("temperament"),
                    profile_data.get("emotional_openness"),
                    profile_data.get("self_awareness"),
                    profile_data.get("resilience_level"),
                    profile_data.get("baseline_anxiety"),
                    profile_data.get("attachment_style"),
                    profile_data.get("insights"),
                    profile_data.get("recommended_approach")
                )
                return {"updated": True}
            else:
                # Criar novo
                await conn.execute(
                    """
                    INSERT INTO user_psychological_profile (
                        user_id, communication_style, primary_needs, thinking_patterns,
                        emotional_triggers, coping_mechanisms, faith_stage, love_language,
                        temperament, emotional_openness, self_awareness, resilience_level,
                        baseline_anxiety, attachment_style, accumulated_insights, recommended_approach
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    """,
                    user_uuid,
                    profile_data.get("communication_style", "balanced"),
                    profile_data.get("primary_needs", []),
                    json.dumps(profile_data.get("thinking_patterns", {})),
                    profile_data.get("emotional_triggers", []),
                    profile_data.get("coping_mechanisms", []),
                    profile_data.get("faith_stage"),
                    profile_data.get("love_language"),
                    profile_data.get("temperament"),
                    profile_data.get("emotional_openness", 5),
                    profile_data.get("self_awareness", 5),
                    profile_data.get("resilience_level", 5),
                    profile_data.get("baseline_anxiety", 5),
                    profile_data.get("attachment_style"),
                    profile_data.get("insights"),
                    profile_data.get("recommended_approach")
                )
                return {"created": True}

    async def get_psychological_context(self, user_id: str) -> str:
        """Retorna contexto psicológico formatado para o prompt"""
        profile = await self.get_psychological_profile(user_id)
        if not profile:
            return ""

        context = "=== PERFIL PSICOLÓGICO ===\n"

        if profile.get("communication_style"):
            styles = {
                "verbose": "Gosta de falar bastante e dar detalhes",
                "concise": "Prefere comunicação direta e objetiva",
                "emotional": "Expressa muito os sentimentos",
                "analytical": "Busca entender racionalmente",
                "balanced": "Comunicação equilibrada"
            }
            context += f"Estilo: {styles.get(profile['communication_style'], profile['communication_style'])}\n"

        if profile.get("primary_needs"):
            needs_map = {
                "validação": "precisa sentir que está certo",
                "orientação": "busca direção clara",
                "escuta": "quer ser ouvido",
                "conselho": "quer soluções práticas",
                "oração": "busca suporte espiritual",
                "conexão": "não quer se sentir sozinho"
            }
            needs_text = [needs_map.get(n, n) for n in profile["primary_needs"]]
            context += f"Necessidades principais: {', '.join(needs_text)}\n"

        if profile.get("emotional_triggers"):
            context += f"Gatilhos: {', '.join(profile['emotional_triggers'])}\n"

        if profile.get("faith_stage"):
            stages = {
                "inicial": "fé em desenvolvimento",
                "convencional": "fé baseada na comunidade",
                "reflexiva": "questiona e busca entender",
                "madura": "fé pessoal integrada"
            }
            context += f"Estágio de fé: {stages.get(profile['faith_stage'], profile['faith_stage'])}\n"

        if profile.get("love_language"):
            languages = {
                "palavras": "Recebe amor por palavras de afirmação",
                "tempo": "Recebe amor por tempo de qualidade",
                "presentes": "Recebe amor por gestos e presentes",
                "serviço": "Recebe amor por atos de serviço"
            }
            context += f"{languages.get(profile['love_language'], '')}\n"

        if profile.get("baseline_anxiety") and profile["baseline_anxiety"] > 6:
            context += "⚠️ Tende a ansiedade - seja gentil e reassegurador\n"

        if profile.get("recommended_approach"):
            context += f"\nCOMO ABORDAR: {profile['recommended_approach']}\n"

        return context

    # ============================================
    # LEARNING - APRENDIZADO CONTÍNUO
    # ============================================

    async def save_learning_interaction(
        self,
        user_id: str,
        conversation_id: str,
        strategy_used: str,
        emotion_before: str = None,
        emotion_after: str = None,
        response_time: float = None,
        user_message_length: int = None,
        ai_response_length: int = None
    ):
        """Salva uma interação para aprendizado"""
        # Converter strings para UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        conv_uuid = UUID(conversation_id) if conversation_id and isinstance(conversation_id, str) else conversation_id

        async with self.pool.acquire() as conn:
            # Criar tabela se não existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_interactions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    conversation_id UUID,
                    strategy_used VARCHAR(50),
                    emotion_before VARCHAR(30),
                    emotion_after VARCHAR(30),
                    response_time FLOAT,
                    user_message_length INT,
                    ai_response_length INT,
                    feedback_type VARCHAR(30),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            await conn.execute("""
                INSERT INTO learning_interactions (
                    user_id, conversation_id, strategy_used,
                    emotion_before, emotion_after, response_time,
                    user_message_length, ai_response_length
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, user_uuid, conv_uuid, strategy_used,
                emotion_before, emotion_after, response_time,
                user_message_length, ai_response_length
            )

    async def save_learning_feedback(
        self,
        user_id: str,
        feedback_type: str,
        strategy_used: str = None,
        context: str = None
    ):
        """Salva feedback implícito ou explícito para aprendizado"""
        # Converter string para UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        async with self.pool.acquire() as conn:
            # Criar tabela se não existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_feedbacks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    feedback_type VARCHAR(50) NOT NULL,
                    strategy_used VARCHAR(50),
                    context TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            await conn.execute("""
                INSERT INTO learning_feedbacks (user_id, feedback_type, strategy_used, context)
                VALUES ($1, $2, $3, $4)
            """, user_uuid, feedback_type, strategy_used, context[:500] if context else None)

    async def get_strategy_scores(self, user_id: str) -> dict:
        """
        Calcula scores de efetividade para cada estratégia baseado no histórico.
        Score alto = estratégia funciona bem para este usuário.
        """
        # Converter string para UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        async with self.pool.acquire() as conn:
            # Verificar se tabela existe
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'learning_feedbacks'
                )
            """)

            if not table_exists:
                return {}

            # Buscar feedbacks por estratégia
            rows = await conn.fetch("""
                SELECT
                    strategy_used,
                    feedback_type,
                    COUNT(*) as count
                FROM learning_feedbacks
                WHERE user_id = $1 AND strategy_used IS NOT NULL
                GROUP BY strategy_used, feedback_type
            """, user_uuid)

            if not rows:
                return {}

            # Calcular scores
            strategy_data = {}
            for row in rows:
                strategy = row["strategy_used"]
                if strategy not in strategy_data:
                    strategy_data[strategy] = {"positive": 0, "negative": 0, "total": 0}

                count = row["count"]
                feedback = row["feedback_type"]

                strategy_data[strategy]["total"] += count

                # Feedbacks positivos
                if feedback in ["positive_explicit", "engagement_high", "emotional_improvement", "returned_soon"]:
                    strategy_data[strategy]["positive"] += count
                # Feedbacks negativos
                elif feedback in ["negative_explicit", "engagement_low", "emotional_decline", "long_absence"]:
                    strategy_data[strategy]["negative"] += count

            # Converter para scores (0.0 a 1.0)
            scores = {}
            for strategy, data in strategy_data.items():
                if data["total"] > 0:
                    # Score = (positivos - negativos/2) / total, normalizado para 0-1
                    raw_score = (data["positive"] - data["negative"] * 0.5) / data["total"]
                    scores[strategy] = max(0.0, min(1.0, (raw_score + 1) / 2))  # Normaliza de -1,1 para 0,1

            return scores

    async def get_user_learning_stats(self, user_id: str) -> dict:
        """Retorna estatísticas de aprendizado do usuário"""
        # Converter string para UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        async with self.pool.acquire() as conn:
            # Verificar se tabelas existem
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'learning_interactions'
                )
            """)

            if not table_exists:
                return {"total_interactions": 0, "strategies_used": {}, "emotional_improvements": 0}

            # Total de interações
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM learning_interactions WHERE user_id = $1",
                user_uuid
            )

            # Estratégias mais usadas
            strategies = await conn.fetch("""
                SELECT strategy_used, COUNT(*) as count
                FROM learning_interactions
                WHERE user_id = $1 AND strategy_used IS NOT NULL
                GROUP BY strategy_used
                ORDER BY count DESC
            """, user_uuid)

            # Melhorias emocionais
            improvements = await conn.fetchval("""
                SELECT COUNT(*) FROM learning_interactions
                WHERE user_id = $1
                AND emotion_before IN ('ansioso', 'triste', 'irritado', 'culpado', 'medo')
                AND emotion_after IN ('esperancoso', 'grato', 'alegre', 'neutro')
            """, user_uuid)

            return {
                "total_interactions": total or 0,
                "strategies_used": {row["strategy_used"]: row["count"] for row in strategies},
                "emotional_improvements": improvements or 0
            }

    async def update_user_preferred_style(self, user_id: str, adjustments: dict):
        """Atualiza preferências de estilo baseado no aprendizado"""
        # Converter string para UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        async with self.pool.acquire() as conn:
            profile = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1",
                user_uuid
            )

            if not profile:
                return

            new_tom = profile.get("tom_preferido", "equilibrado")

            # Ajustar baseado nos feedbacks
            if adjustments.get("prefer_brief"):
                if new_tom == "detalhado":
                    new_tom = "equilibrado"
                else:
                    new_tom = "direto"

            if adjustments.get("prefer_detailed"):
                if new_tom == "direto":
                    new_tom = "equilibrado"
                else:
                    new_tom = "detalhado"

            await conn.execute(
                "UPDATE user_profiles SET tom_preferido = $1 WHERE user_id = $2",
                new_tom, user_uuid
            )

    # ============================================
    # AUDIT LOG
    # ============================================

    async def log_audit(self, user_id: str, action: str, details: dict = None, ip: str = None):
        """Registra ação no log de auditoria"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, action, details, ip_address)
                VALUES ($1, $2, $3, $4)
                """,
                user_uuid, action, json.dumps(details or {}, cls=UUIDEncoder), ip
            )

    # ============================================
    # PASSWORD RESET
    # ============================================

    async def save_password_reset_token(self, user_id: str, token: str, expires_hours: int = 1):
        """Salva token de recuperacao de senha"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Criar tabela se nao existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(100) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Invalidar tokens anteriores do usuario
            await conn.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE user_id = $1 AND used = FALSE",
                user_uuid
            )

            # Criar novo token
            await conn.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES ($1, $2, NOW() + INTERVAL '%s hours')
                """ % expires_hours,
                user_uuid, token
            )

    async def verify_password_reset_token(self, token: str) -> Optional[dict]:
        """Verifica se token de reset e valido e retorna user_id"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT prt.user_id, u.email, u.id
                FROM password_reset_tokens prt
                JOIN users u ON u.id = prt.user_id
                WHERE prt.token = $1
                AND prt.used = FALSE
                AND prt.expires_at > NOW()
                """,
                token
            )
            return dict(row) if row else None

    async def use_password_reset_token(self, token: str):
        """Marca token como usado"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE token = $1",
                token
            )

    async def update_user_password(self, user_id: str, password_hash: str):
        """Atualiza senha do usuario"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                password_hash, user_uuid
            )

    # ============================================
    # CHECKOUT TOKENS (Auto-login para pagamento)
    # ============================================

    async def save_checkout_token(self, user_id: str, token: str, expires_minutes: int = 15):
        """Salva token temporario para auto-login no checkout"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Criar tabela se nao existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS checkout_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(100) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Invalidar tokens anteriores do usuario
            await conn.execute(
                "UPDATE checkout_tokens SET used = TRUE WHERE user_id = $1 AND used = FALSE",
                user_uuid
            )

            # Criar novo token
            await conn.execute(
                """
                INSERT INTO checkout_tokens (user_id, token, expires_at)
                VALUES ($1, $2, NOW() + INTERVAL '%s minutes')
                """ % expires_minutes,
                user_uuid, token
            )

    async def verify_checkout_token(self, token: str) -> Optional[dict]:
        """Verifica se token de checkout e valido e retorna user_id"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT ct.user_id, u.email, u.id, u.is_premium
                FROM checkout_tokens ct
                JOIN users u ON u.id = ct.user_id
                WHERE ct.token = $1
                AND ct.used = FALSE
                AND ct.expires_at > NOW()
                """,
                token
            )
            return dict(row) if row else None

    async def use_checkout_token(self, token: str):
        """Marca token de checkout como usado"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE checkout_tokens SET used = TRUE WHERE token = $1",
                token
            )

    # ============================================
    # EMOTIONAL TIMELINE (Layer 2)
    # Tracking interno de estados emocionais
    # ============================================

    async def record_emotional_state(
        self,
        user_id: str,
        emotion: str,
        intensity: float = 0.5,
        confidence: float = 0.7,
        trigger: str = None,
        themes: List[str] = None,
        conversation_id: str = None
    ) -> dict:
        """
        Registra um estado emocional detectado na timeline.
        Uso interno - não exposto ao usuário.
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        conv_uuid = UUID(conversation_id) if conversation_id and isinstance(conversation_id, str) else conversation_id
        now = datetime.now()

        async with self.pool.acquire() as conn:
            # Criar tabela se não existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS emotional_timeline (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
                    emotion VARCHAR(50) NOT NULL,
                    intensity DECIMAL(3,2) DEFAULT 0.5,
                    confidence DECIMAL(3,2) DEFAULT 0.7,
                    trigger_detected VARCHAR(100),
                    themes JSONB DEFAULT '[]',
                    day_of_week INTEGER,
                    hour_of_day INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            row = await conn.fetchrow(
                """
                INSERT INTO emotional_timeline (
                    user_id, conversation_id, emotion, intensity, confidence,
                    trigger_detected, themes, day_of_week, hour_of_day
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, created_at
                """,
                user_uuid, conv_uuid, emotion,
                min(max(intensity, 0.0), 1.0),
                min(max(confidence, 0.0), 1.0),
                trigger, json.dumps(themes or []),
                now.weekday(), now.hour
            )
            return {"id": str(row["id"]), "recorded_at": row["created_at"].isoformat()}

    async def get_emotional_timeline(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[dict]:
        """
        Busca histórico emocional do usuário.
        Uso interno para análise de padrões.
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM emotional_timeline
                WHERE user_id = $1
                AND created_at > NOW() - ($2 || ' days')::INTERVAL
                ORDER BY created_at DESC
                LIMIT $3
                """,
                user_uuid, str(days), limit
            )
            result = []
            for row in rows:
                entry = dict(row)
                if entry.get("themes") and isinstance(entry["themes"], str):
                    entry["themes"] = json.loads(entry["themes"])
                result.append(entry)
            return result

    async def get_emotional_patterns(self, user_id: str, days: int = 30) -> dict:
        """
        Analisa padrões emocionais do usuário.
        Retorna tendências, picos e triggers comuns.
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Verificar se a função existe (pode não ter rodado a migration)
            func_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_proc WHERE proname = 'get_emotional_patterns'
                )
            """)

            if func_exists:
                row = await conn.fetchrow(
                    "SELECT * FROM get_emotional_patterns($1, $2)",
                    user_uuid, days
                )
                if row:
                    return dict(row)

            # Fallback se função não existe - análise simplificada
            emotions = await conn.fetch(
                """
                SELECT emotion, COUNT(*) as count, AVG(intensity) as avg_intensity
                FROM emotional_timeline
                WHERE user_id = $1 AND created_at > NOW() - ($2 || ' days')::INTERVAL
                GROUP BY emotion
                ORDER BY count DESC
                LIMIT 5
                """,
                user_uuid, str(days)
            )

            if not emotions:
                return {
                    "dominant_emotion": "neutro",
                    "avg_intensity": 0.5,
                    "emotion_variance": 0.0,
                    "trend": "stable",
                    "emotions_detected": []
                }

            return {
                "dominant_emotion": emotions[0]["emotion"] if emotions else "neutro",
                "avg_intensity": float(emotions[0]["avg_intensity"]) if emotions else 0.5,
                "emotion_variance": 0.0,
                "trend": "stable",
                "emotions_detected": [
                    {"emotion": e["emotion"], "count": e["count"], "avg_intensity": float(e["avg_intensity"])}
                    for e in emotions
                ]
            }

    async def get_emotional_trend(self, user_id: str) -> str:
        """
        Retorna tendência emocional recente: 'improving', 'worsening', 'stable'
        Compara última semana com semanas anteriores.
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        negative_emotions = ('ansioso', 'triste', 'angustiado', 'estressado', 'deprimido', 'frustrado')

        async with self.pool.acquire() as conn:
            # Média de intensidade de emoções negativas na última semana
            recent = await conn.fetchval(
                """
                SELECT AVG(intensity)
                FROM emotional_timeline
                WHERE user_id = $1
                AND emotion = ANY($2)
                AND created_at > NOW() - INTERVAL '7 days'
                """,
                user_uuid, list(negative_emotions)
            )

            # Média das 3 semanas anteriores
            older = await conn.fetchval(
                """
                SELECT AVG(intensity)
                FROM emotional_timeline
                WHERE user_id = $1
                AND emotion = ANY($2)
                AND created_at BETWEEN NOW() - INTERVAL '28 days' AND NOW() - INTERVAL '7 days'
                """,
                user_uuid, list(negative_emotions)
            )

            if recent is None or older is None:
                return "stable"

            recent = float(recent)
            older = float(older)

            if recent > older * 1.2:
                return "worsening"
            elif recent < older * 0.8:
                return "improving"
            return "stable"

    # ============================================
    # MEMORY HEALTH SCORE (Layer 2)
    # Avaliação da qualidade do contexto do usuário
    # ============================================

    async def calculate_memory_health_score(self, user_id: str) -> dict:
        """
        Calcula o Health Score de memórias do usuário.
        Avalia diversidade, atualização, consistência e equilíbrio.
        """
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Verificar se a função existe
            func_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_proc WHERE proname = 'calculate_memory_health_score'
                )
            """)

            if func_exists:
                row = await conn.fetchrow(
                    "SELECT * FROM calculate_memory_health_score($1)",
                    user_uuid
                )
                if row:
                    result = dict(row)
                    # Gerar recomendações baseadas nos scores
                    result["recommendations"] = self._generate_health_recommendations(result)
                    return result

            # Fallback - cálculo simplificado em Python
            return await self._calculate_health_score_fallback(conn, user_uuid)

    async def _calculate_health_score_fallback(self, conn, user_uuid: UUID) -> dict:
        """Cálculo de Health Score quando a função SQL não existe."""
        # Contar memórias
        counts = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(DISTINCT categoria) FILTER (WHERE status = 'active') as categories,
                COUNT(*) FILTER (WHERE status IN ('superseded', 'deactivated')) as conflicts,
                COUNT(*) FILTER (WHERE status = 'active' AND ultima_mencao > NOW() - INTERVAL '7 days') as fresh,
                COUNT(*) FILTER (WHERE status = 'active' AND ultima_mencao < NOW() - INTERVAL '30 days') as stale,
                COUNT(*) FILTER (WHERE status = 'active' AND categoria = 'LUTA') as lutas,
                COUNT(*) FILTER (WHERE status = 'active' AND categoria = 'VITORIA') as vitorias,
                COUNT(*) FILTER (WHERE status = 'active' AND mencoes >= 3) as high_mention
            FROM user_memories WHERE user_id = $1
            """,
            user_uuid
        )

        total = counts["total"] or 0
        active = counts["active"] or 0
        categories = counts["categories"] or 0
        conflicts = counts["conflicts"] or 0
        fresh = counts["fresh"] or 0
        stale = counts["stale"] or 0
        lutas = counts["lutas"] or 0
        vitorias = counts["vitorias"] or 0
        high_mention = counts["high_mention"] or 0

        if active == 0:
            return {
                "diversity_score": 0,
                "freshness_score": 0,
                "consistency_score": 100,
                "engagement_score": 0,
                "balance_score": 50,
                "overall_score": 30,
                "health_level": "unknown",
                "total_memories": 0,
                "active_memories": 0,
                "categories_count": 0,
                "conflicts_count": 0,
                "stale_memories_count": 0,
                "recommendations": ["Converse mais para construir seu perfil"]
            }

        # Calcular scores
        diversity = min(int(categories / 8.0 * 100), 100)
        freshness = min(int(fresh / active * 100), 100) if active > 0 else 50
        consistency = max(100 - int(conflicts / total * 200), 0) if total > 0 else 100
        engagement = min(int(high_mention / active * 100), 100) if active > 0 else 0

        # Balance score
        if lutas == 0 and vitorias == 0:
            balance = 50
        elif lutas == 0:
            balance = 100
        elif vitorias >= lutas:
            balance = min(70 + int(vitorias / lutas * 15), 100)
        else:
            balance = max(50 - int((lutas - vitorias) / lutas * 30), 20)

        # Overall
        overall = int(
            diversity * 0.20 +
            freshness * 0.25 +
            consistency * 0.20 +
            engagement * 0.15 +
            balance * 0.20
        )

        # Level
        if overall >= 80:
            level = "excellent"
        elif overall >= 60:
            level = "good"
        elif overall >= 40:
            level = "moderate"
        else:
            level = "poor"

        result = {
            "diversity_score": diversity,
            "freshness_score": freshness,
            "consistency_score": consistency,
            "engagement_score": engagement,
            "balance_score": balance,
            "overall_score": overall,
            "health_level": level,
            "total_memories": total,
            "active_memories": active,
            "categories_count": categories,
            "conflicts_count": conflicts,
            "stale_memories_count": stale
        }
        result["recommendations"] = self._generate_health_recommendations(result)
        return result

    def _generate_health_recommendations(self, scores: dict) -> List[str]:
        """Gera recomendações baseadas nos scores."""
        recommendations = []

        if scores.get("diversity_score", 0) < 50:
            recommendations.append("Compartilhe mais sobre diferentes áreas da sua vida")

        if scores.get("freshness_score", 0) < 40:
            recommendations.append("Atualize informações antigas - sua vida mudou?")

        if scores.get("consistency_score", 0) < 60:
            recommendations.append("Algumas informações parecem conflitantes")

        if scores.get("balance_score", 0) < 40:
            recommendations.append("Compartilhe também suas vitórias e conquistas!")

        if scores.get("stale_memories_count", 0) > 10:
            recommendations.append("Algumas memórias estão desatualizadas")

        if not recommendations:
            if scores.get("overall_score", 0) >= 80:
                recommendations.append("Excelente! Seu perfil está bem completo")
            else:
                recommendations.append("Continue conversando para melhorar seu perfil")

        return recommendations

    async def save_memory_health_score(self, user_id: str, scores: dict):
        """Salva/atualiza o cache de Health Score."""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Criar tabela se não existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_health_scores (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    diversity_score INTEGER DEFAULT 0,
                    freshness_score INTEGER DEFAULT 0,
                    consistency_score INTEGER DEFAULT 0,
                    engagement_score INTEGER DEFAULT 0,
                    balance_score INTEGER DEFAULT 0,
                    overall_score INTEGER DEFAULT 0,
                    health_level VARCHAR(20) DEFAULT 'unknown',
                    total_memories INTEGER DEFAULT 0,
                    active_memories INTEGER DEFAULT 0,
                    categories_count INTEGER DEFAULT 0,
                    conflicts_count INTEGER DEFAULT 0,
                    stale_memories_count INTEGER DEFAULT 0,
                    recommendations JSONB DEFAULT '[]',
                    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            await conn.execute(
                """
                INSERT INTO memory_health_scores (
                    user_id, diversity_score, freshness_score, consistency_score,
                    engagement_score, balance_score, overall_score, health_level,
                    total_memories, active_memories, categories_count,
                    conflicts_count, stale_memories_count, recommendations,
                    last_calculated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    diversity_score = $2,
                    freshness_score = $3,
                    consistency_score = $4,
                    engagement_score = $5,
                    balance_score = $6,
                    overall_score = $7,
                    health_level = $8,
                    total_memories = $9,
                    active_memories = $10,
                    categories_count = $11,
                    conflicts_count = $12,
                    stale_memories_count = $13,
                    recommendations = $14,
                    last_calculated_at = NOW(),
                    updated_at = NOW()
                """,
                user_uuid,
                scores.get("diversity_score", 0),
                scores.get("freshness_score", 0),
                scores.get("consistency_score", 0),
                scores.get("engagement_score", 0),
                scores.get("balance_score", 0),
                scores.get("overall_score", 0),
                scores.get("health_level", "unknown"),
                scores.get("total_memories", 0),
                scores.get("active_memories", 0),
                scores.get("categories_count", 0),
                scores.get("conflicts_count", 0),
                scores.get("stale_memories_count", 0),
                json.dumps(scores.get("recommendations", []))
            )

    async def get_cached_health_score(self, user_id: str) -> Optional[dict]:
        """Busca Health Score em cache (se calculado recentemente)."""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM memory_health_scores
                WHERE user_id = $1
                AND last_calculated_at > NOW() - INTERVAL '1 hour'
                """,
                user_uuid
            )
            if row:
                result = dict(row)
                if result.get("recommendations") and isinstance(result["recommendations"], str):
                    result["recommendations"] = json.loads(result["recommendations"])
                return result
            return None

    # ============================================
    # PUSH NOTIFICATIONS
    # ============================================

    async def save_push_subscription(
        self,
        user_id: str,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str = None
    ) -> dict:
        """Salva subscription de push do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Criar tabela se não existir
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

            # Upsert - atualiza se mesmo endpoint já existe
            row = await conn.fetchrow(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, user_agent)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (endpoint) DO UPDATE SET
                    user_id = $1,
                    p256dh = $3,
                    auth = $4,
                    user_agent = $5,
                    is_active = TRUE,
                    last_used_at = NOW()
                RETURNING id
                """,
                user_uuid, endpoint, p256dh, auth, user_agent
            )
            return {"id": str(row["id"]), "saved": True}

    async def get_user_push_subscriptions(self, user_id: str) -> List[dict]:
        """Busca subscriptions ativas de um usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM push_subscriptions
                WHERE user_id = $1 AND is_active = TRUE
                """,
                user_uuid
            )
            return [dict(row) for row in rows]

    async def get_all_push_subscriptions(
        self,
        filter_premium: bool = None,
        limit: int = 1000
    ) -> List[dict]:
        """Busca todas subscriptions ativas (para envio em massa)"""
        async with self.pool.acquire() as conn:
            if filter_premium is None:
                rows = await conn.fetch(
                    """
                    SELECT ps.*, u.email, u.is_premium
                    FROM push_subscriptions ps
                    JOIN users u ON u.id = ps.user_id
                    WHERE ps.is_active = TRUE
                    LIMIT $1
                    """,
                    limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT ps.*, u.email, u.is_premium
                    FROM push_subscriptions ps
                    JOIN users u ON u.id = ps.user_id
                    WHERE ps.is_active = TRUE AND u.is_premium = $1
                    LIMIT $2
                    """,
                    filter_premium, limit
                )
            return [dict(row) for row in rows]

    async def deactivate_push_subscription(self, endpoint: str):
        """Desativa uma subscription (quando falha o envio)"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE push_subscriptions SET is_active = FALSE WHERE endpoint = $1",
                endpoint
            )

    async def delete_push_subscription(self, user_id: str, endpoint: str = None):
        """Remove subscription(s) de um usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            if endpoint:
                await conn.execute(
                    "DELETE FROM push_subscriptions WHERE user_id = $1 AND endpoint = $2",
                    user_uuid, endpoint
                )
            else:
                await conn.execute(
                    "DELETE FROM push_subscriptions WHERE user_id = $1",
                    user_uuid
                )

    # ============================================
    # USER NOTIFICATION PREFERENCES
    # ============================================

    async def get_user_notification_preferences(self, user_id: str) -> Optional[dict]:
        """Busca preferências de notificação do usuário"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Criar tabela se não existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_notification_preferences (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    push_enabled BOOLEAN DEFAULT TRUE,
                    reminder_enabled BOOLEAN DEFAULT TRUE,
                    reminder_time TIME DEFAULT '09:00:00',
                    reminder_days JSONB DEFAULT '["mon","tue","wed","thu","fri","sat","sun"]',
                    engagement_enabled BOOLEAN DEFAULT TRUE,
                    engagement_after_days INTEGER DEFAULT 3,
                    marketing_enabled BOOLEAN DEFAULT FALSE,
                    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            row = await conn.fetchrow(
                "SELECT * FROM user_notification_preferences WHERE user_id = $1",
                user_uuid
            )
            if row:
                result = dict(row)
                if result.get("reminder_days") and isinstance(result["reminder_days"], str):
                    result["reminder_days"] = json.loads(result["reminder_days"])
                return result
            return None

    async def save_user_notification_preferences(
        self,
        user_id: str,
        preferences: dict
    ) -> dict:
        """Salva ou atualiza preferências de notificação"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Garantir que tabela existe
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_notification_preferences (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    push_enabled BOOLEAN DEFAULT TRUE,
                    reminder_enabled BOOLEAN DEFAULT TRUE,
                    reminder_time TIME DEFAULT '09:00:00',
                    reminder_days JSONB DEFAULT '["mon","tue","wed","thu","fri","sat","sun"]',
                    engagement_enabled BOOLEAN DEFAULT TRUE,
                    engagement_after_days INTEGER DEFAULT 3,
                    marketing_enabled BOOLEAN DEFAULT FALSE,
                    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            await conn.execute(
                """
                INSERT INTO user_notification_preferences (
                    user_id, push_enabled, reminder_enabled, reminder_time,
                    reminder_days, engagement_enabled, engagement_after_days,
                    marketing_enabled, timezone
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (user_id) DO UPDATE SET
                    push_enabled = COALESCE($2, user_notification_preferences.push_enabled),
                    reminder_enabled = COALESCE($3, user_notification_preferences.reminder_enabled),
                    reminder_time = COALESCE($4, user_notification_preferences.reminder_time),
                    reminder_days = COALESCE($5, user_notification_preferences.reminder_days),
                    engagement_enabled = COALESCE($6, user_notification_preferences.engagement_enabled),
                    engagement_after_days = COALESCE($7, user_notification_preferences.engagement_after_days),
                    marketing_enabled = COALESCE($8, user_notification_preferences.marketing_enabled),
                    timezone = COALESCE($9, user_notification_preferences.timezone),
                    updated_at = NOW()
                """,
                user_uuid,
                preferences.get("push_enabled"),
                preferences.get("reminder_enabled"),
                preferences.get("reminder_time"),
                json.dumps(preferences.get("reminder_days")) if preferences.get("reminder_days") else None,
                preferences.get("engagement_enabled"),
                preferences.get("engagement_after_days"),
                preferences.get("marketing_enabled"),
                preferences.get("timezone")
            )
            return {"saved": True}

    async def get_users_for_reminder(self, current_hour: int, day_of_week: str) -> List[dict]:
        """
        Busca usuários que devem receber lembrete agora.
        current_hour: hora atual (0-23) no timezone do servidor
        day_of_week: dia da semana em inglês (mon, tue, etc.)
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    unp.user_id,
                    u.email,
                    ps.endpoint,
                    ps.p256dh,
                    ps.auth
                FROM user_notification_preferences unp
                JOIN users u ON u.id = unp.user_id
                JOIN push_subscriptions ps ON ps.user_id = unp.user_id
                WHERE unp.reminder_enabled = TRUE
                AND unp.push_enabled = TRUE
                AND ps.is_active = TRUE
                AND EXTRACT(HOUR FROM unp.reminder_time) = $1
                AND unp.reminder_days ? $2
                """,
                current_hour, day_of_week
            )
            return [dict(row) for row in rows]

    async def get_users_for_engagement(self, days_inactive: int = 3) -> List[dict]:
        """
        Busca usuários inativos que devem receber notificação de engajamento.
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    unp.user_id,
                    u.email,
                    u.last_login,
                    ps.endpoint,
                    ps.p256dh,
                    ps.auth,
                    unp.engagement_after_days
                FROM user_notification_preferences unp
                JOIN users u ON u.id = unp.user_id
                JOIN push_subscriptions ps ON ps.user_id = unp.user_id
                WHERE unp.engagement_enabled = TRUE
                AND unp.push_enabled = TRUE
                AND ps.is_active = TRUE
                AND u.last_login < NOW() - (unp.engagement_after_days || ' days')::INTERVAL
                AND NOT EXISTS (
                    SELECT 1 FROM notification_logs nl
                    WHERE nl.user_id = unp.user_id
                    AND nl.notification_type = 'engagement'
                    AND nl.sent_at > NOW() - INTERVAL '7 days'
                )
                LIMIT 100
                """
            )
            return [dict(row) for row in rows]

    # ============================================
    # NOTIFICATION LOGS
    # ============================================

    async def log_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        body: str,
        success: bool = True,
        error_message: str = None
    ):
        """Registra envio de notificação"""
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with self.pool.acquire() as conn:
            # Criar tabela se não existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200),
                    body TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            await conn.execute(
                """
                INSERT INTO notification_logs (user_id, notification_type, title, body, success, error_message)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user_uuid, notification_type, title, body, success, error_message
            )

    async def get_notification_stats(self, days: int = 7) -> dict:
        """Retorna estatísticas de notificações enviadas"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_sent,
                    COUNT(*) FILTER (WHERE success = TRUE) as successful,
                    COUNT(*) FILTER (WHERE success = FALSE) as failed,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) FILTER (WHERE notification_type = 'reminder') as reminders,
                    COUNT(*) FILTER (WHERE notification_type = 'engagement') as engagement,
                    COUNT(*) FILTER (WHERE notification_type = 'broadcast') as broadcasts
                FROM notification_logs
                WHERE sent_at > NOW() - ($1 || ' days')::INTERVAL
                """,
                str(days)
            )
            return dict(stats) if stats else {}


# ============================================
# CONNECTION POOL
# ============================================

_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Inicializa pool de conexões e cria tabelas necessárias"""
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)

    # Criar tabelas de notificações se não existirem
    async with _pool.acquire() as conn:
        # Tabela de notificações (campanhas)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                send_push BOOLEAN DEFAULT TRUE,
                send_email BOOLEAN DEFAULT TRUE,
                target_audience VARCHAR(50) DEFAULT 'all',
                status VARCHAR(50) DEFAULT 'pending',
                total_recipients INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                created_by UUID REFERENCES users(id),
                scheduled_at TIMESTAMP WITH TIME ZONE,
                sent_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Tabela de entregas individuais
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notification_deliveries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                notification_id UUID REFERENCES notifications(id) ON DELETE CASCADE,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                channel VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                error_message TEXT,
                sent_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Adicionar colunas de preferências no user_profiles se não existirem
        try:
            await conn.execute("""
                ALTER TABLE user_profiles
                ADD COLUMN IF NOT EXISTS push_notifications BOOLEAN DEFAULT TRUE
            """)
        except:
            pass

        try:
            await conn.execute("""
                ALTER TABLE user_profiles
                ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE
            """)
        except:
            pass

        # Criar índices
        try:
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notification_deliveries_notification_id ON notification_deliveries(notification_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notification_deliveries_user_id ON notification_deliveries(user_id)")
        except:
            pass

    print("[DB] Tabelas de notificações verificadas/criadas")
    return _pool


async def close_db():
    """Fecha pool de conexões"""
    global _pool
    if _pool:
        await _pool.close()


async def get_db() -> Database:
    """Dependência FastAPI para injetar banco"""
    if not _pool:
        await init_db()
    return Database(_pool)


async def get_db_pool():
    """Retorna o pool de conexões diretamente (para uso em background tasks)"""
    global _pool
    if not _pool:
        await init_db()
    return _pool


async def get_db_instance() -> Database:
    """Retorna instancia do Database diretamente (para uso fora de dependencias FastAPI)"""
    global _pool
    if not _pool:
        await init_db()
    return Database(_pool) if _pool else None

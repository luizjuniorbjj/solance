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
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            return dict(row) if row else None

    async def update_last_login(self, user_id: str):
        """Atualiza último login"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_login = NOW() WHERE id = $1",
                user_id
            )

    async def increment_message_count(self, user_id: str):
        """Incrementa contador de mensagens"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users
                SET total_messages = total_messages + 1,
                    trial_messages_used = trial_messages_used + 1
                WHERE id = $1
                """,
                user_id
            )

    async def increment_trial_messages(self, user_id: str):
        """Incrementa apenas o contador de trial (usado para limites free)"""
        await self.increment_message_count(user_id)

    # ============================================
    # USER PROFILES
    # ============================================

    async def create_user_profile(self, user_id: str, nome: Optional[str] = None) -> dict:
        """Cria perfil do usuário"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_profiles (user_id, nome)
                VALUES ($1, $2)
                RETURNING *
                """,
                user_id, nome
            )
            return dict(row)

    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Busca perfil do usuário"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1",
                user_id
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

        values.append(user_id)

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
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversations (user_id)
                VALUES ($1)
                RETURNING *
                """,
                user_id
            )
            return dict(row)

    async def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Busca conversa por ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM conversations WHERE id = $1",
                conversation_id
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
                conversation_id, resumo, json.dumps(temas or []), humor_final
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
        encrypted_content = encrypt_data(content, user_id)

        async with self.pool.acquire() as conn:
            # Salvar mensagem
            row = await conn.fetchrow(
                """
                INSERT INTO messages (conversation_id, user_id, role, content_encrypted, tokens_used, model_used)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, role, created_at
                """,
                conversation_id, user_id, role, encrypted_content, tokens_used, model_used
            )

            # Atualizar contador e timestamp da conversa
            await conn.execute(
                """
                UPDATE conversations
                SET message_count = message_count + 1,
                    last_message_at = NOW()
                WHERE id = $1
                """,
                conversation_id
            )

            return dict(row)

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Busca mensagens de uma conversa (descriptografadas)"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                conversation_id, limit
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
        descricao_encrypted = encrypt_data(descricao, user_id) if descricao else None

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO prayer_requests (user_id, titulo, descricao_encrypted, categoria)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                user_id, titulo, descricao_encrypted, categoria
            )
            return dict(row)

    async def get_active_prayer_requests(self, user_id: str) -> List[dict]:
        """Busca pedidos de oração ativos"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM prayer_requests
                WHERE user_id = $1 AND status = 'ativo'
                ORDER BY created_at DESC
                """,
                user_id
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
                prayer_id, user_id, testemunho_encrypted
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
        insight_encrypted = encrypt_data(insight, user_id)

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_insights (user_id, categoria, insight_encrypted, confianca, origem_conversa_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, categoria, insight_encrypted, confianca, conversa_id
            )

    async def get_user_insights(self, user_id: str) -> List[dict]:
        """Busca insights ativos do usuário"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM user_insights
                WHERE user_id = $1 AND is_active = TRUE
                ORDER BY confianca DESC, created_at DESC
                """,
                user_id
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
        async with self.pool.acquire() as conn:
            # Se ação é deactivate, apenas desativa
            if action == "deactivate" and supersedes_id:
                await conn.execute(
                    "UPDATE user_memories SET status = 'deactivated', is_active = FALSE WHERE id = $1 AND user_id = $2",
                    supersedes_id, user_id
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
                    conn, user_id, categoria, semantic_field
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
                user_id, categoria, fato_norm
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
                user_id, categoria, fato, detalhes, importancia,
                conversa_id, supersedes_id if action == "supersede" else None,
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
        async with self.pool.acquire() as conn:
            if categoria:
                rows = await conn.fetch(
                    """
                    SELECT * FROM user_memories
                    WHERE user_id = $1 AND categoria = $2 AND status = 'active'
                    ORDER BY importancia DESC, ultima_mencao DESC
                    LIMIT $3
                    """,
                    user_id, categoria, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM user_memories
                    WHERE user_id = $1 AND status = 'active'
                    ORDER BY importancia DESC, ultima_mencao DESC
                    LIMIT $2
                    """,
                    user_id, limit
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
                    user_id, current_message, top_k
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
                    user_id, top_k
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
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_memories
                SET mencoes = mencoes + 1, ultima_mencao = NOW()
                WHERE id = $1
                """,
                memory_id
            )

    async def deactivate_memory(self, memory_id: str, user_id: str):
        """Desativa uma memória (soft delete)"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_memories
                SET is_active = FALSE
                WHERE id = $1 AND user_id = $2
                """,
                memory_id, user_id
            )

    # ============================================
    # PSYCHOLOGICAL PROFILE
    # ============================================

    async def get_psychological_profile(self, user_id: str) -> Optional[dict]:
        """Busca perfil psicológico do usuário"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_psychological_profile WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None

    async def save_psychological_profile(
        self,
        user_id: str,
        profile_data: dict
    ) -> dict:
        """Salva ou atualiza perfil psicológico do usuário"""
        async with self.pool.acquire() as conn:
            # Verificar se já existe
            existing = await conn.fetchrow(
                "SELECT id FROM user_psychological_profile WHERE user_id = $1",
                user_id
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
                    user_id,
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
                    user_id,
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
            """, user_id, conversation_id, strategy_used,
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
            """, user_id, feedback_type, strategy_used, context[:500] if context else None)

    async def get_strategy_scores(self, user_id: str) -> dict:
        """
        Calcula scores de efetividade para cada estratégia baseado no histórico.
        Score alto = estratégia funciona bem para este usuário.
        """
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
            """, user_id)

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
                user_id
            )

            # Estratégias mais usadas
            strategies = await conn.fetch("""
                SELECT strategy_used, COUNT(*) as count
                FROM learning_interactions
                WHERE user_id = $1 AND strategy_used IS NOT NULL
                GROUP BY strategy_used
                ORDER BY count DESC
            """, user_id)

            # Melhorias emocionais
            improvements = await conn.fetchval("""
                SELECT COUNT(*) FROM learning_interactions
                WHERE user_id = $1
                AND emotion_before IN ('ansioso', 'triste', 'irritado', 'culpado', 'medo')
                AND emotion_after IN ('esperancoso', 'grato', 'alegre', 'neutro')
            """, user_id)

            return {
                "total_interactions": total or 0,
                "strategies_used": {row["strategy_used"]: row["count"] for row in strategies},
                "emotional_improvements": improvements or 0
            }

    async def update_user_preferred_style(self, user_id: str, adjustments: dict):
        """Atualiza preferências de estilo baseado no aprendizado"""
        async with self.pool.acquire() as conn:
            profile = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1",
                user_id
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
                new_tom, user_id
            )

    # ============================================
    # AUDIT LOG
    # ============================================

    async def log_audit(self, user_id: str, action: str, details: dict = None, ip: str = None):
        """Registra ação no log de auditoria"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, action, details, ip_address)
                VALUES ($1, $2, $3, $4)
                """,
                user_id, action, json.dumps(details or {}, cls=UUIDEncoder), ip
            )


# ============================================
# CONNECTION POOL
# ============================================

_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Inicializa pool de conexões"""
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
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

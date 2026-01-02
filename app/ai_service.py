"""
AiSyster - Serviço de IA
Integração com Claude + Sistema de Memória + Aprendizado Contínuo
"""

import json
import time
from typing import Optional, List, Dict
from datetime import datetime

import anthropic

from app.config import (
    ANTHROPIC_API_KEY,
    AI_MODEL_PRIMARY,
    AI_MODEL_FALLBACK,
    MAX_TOKENS_RESPONSE,
    MONTHLY_MESSAGE_LIMIT
)
from app.prompts import (
    AISYSTER_PERSONA,
    ONBOARDING_PROMPT,
    SUMMARY_PROMPT,
    INSIGHT_EXTRACTION_PROMPT,
    MEMORY_EXTRACTION_PROMPT,
    PSYCHOLOGICAL_ANALYSIS_PROMPT,
    build_user_context
)
from app.database import Database
from app.learning.continuous_learning import (
    LearningEngine,
    ImplicitFeedbackDetector,
    LearningContextBuilder,
    ResponseStrategy,
    FeedbackType
)


class AIService:
    """
    Serviço de IA com memória, personalização e aprendizado contínuo
    """

    def __init__(self, db: Database):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.db = db
        self.learning_engine = LearningEngine(db)
        # Cache temporário para rastrear última resposta (para feedback implícito)
        self._last_responses: Dict[str, dict] = {}

    async def chat(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        image_data: Optional[str] = None,  # Base64 encoded image (single)
        image_media_type: Optional[str] = None,  # image/jpeg, image/png, etc.
        images: Optional[List[tuple]] = None  # Lista de (base64, media_type) para PDFs
    ) -> Dict:
        """
        Processa mensagem do usuário com contexto completo
        """
        # 1. Buscar ou criar conversa
        if conversation_id:
            conversation = await self.db.get_conversation(conversation_id)
        else:
            conversation = await self.db.create_conversation(user_id)
            conversation_id = conversation["id"]

        # 2. Buscar contexto do usuário
        profile = await self.db.get_user_profile(user_id)
        user = await self.db.get_user_by_id(user_id)

        # 3. Buscar histórico de conversas e pedidos de oração
        recent_conversations = await self.db.get_recent_conversations(user_id, limit=5)
        prayer_requests = await self.db.get_active_prayer_requests(user_id)

        # 4. Buscar mensagens da conversa atual
        messages = await self.db.get_conversation_messages(conversation_id, user_id)

        # 4.5 MEMÓRIA ETERNA: Buscar memórias RELEVANTES (Top-K, não todas!)
        # Passa a mensagem atual para priorizar memórias relacionadas
        permanent_memory = await self.db.get_all_memories_formatted(
            user_id,
            current_message=message,
            top_k=20  # Máximo de memórias a incluir
        )

        # 4.6 PERFIL PSICOLÓGICO: Buscar contexto psicológico
        psychological_context = await self.db.get_psychological_context(user_id)

        # 4.65 APRENDIZADO: Detectar feedback implícito da mensagem anterior
        recent_feedbacks = []
        if user_id in self._last_responses:
            last = self._last_responses[user_id]
            time_to_respond = time.time() - last.get("timestamp", time.time())
            feedbacks = ImplicitFeedbackDetector.detect_feedback(
                last.get("user_message", ""),
                last.get("ai_response", ""),
                message,
                time_to_respond
            )
            recent_feedbacks = feedbacks

            # Salvar feedbacks detectados
            for fb in feedbacks:
                await self.learning_engine.process_user_response(
                    user_id=user_id,
                    original_ai_response=last.get("ai_response", ""),
                    user_response=message,
                    time_to_respond=time_to_respond,
                    original_user_message=last.get("user_message", "")
                )
                # Ajustar perfil baseado nos feedbacks
                await self.learning_engine.adjust_profile(user_id, feedbacks)

        # 4.66 APRENDIZADO: Determinar melhor estratégia para este usuário
        current_context = {
            "emotional_state": profile.get("estado_emocional", "neutro") if profile else "neutro",
            "communication_style": profile.get("tom_preferido", "acolhedor") if profile else "acolhedor",
            "urgency": 0.3  # Pode ser ajustado baseado na mensagem
        }
        optimal_strategy = await self.learning_engine.get_optimal_strategy(user_id, current_context)

        # 4.67 APRENDIZADO: Construir contexto de aprendizado para o prompt
        patterns = await self.learning_engine.detect_patterns(user_id)
        learning_context = LearningContextBuilder.build_learning_context(
            optimal_strategy=optimal_strategy,
            patterns=patterns,
            insights=[],
            recent_feedbacks=recent_feedbacks
        )

        # 4.7 Buscar últimas mensagens de conversas anteriores (contexto recente)
        previous_conversations_detail = []
        for conv in recent_conversations[:3]:  # Últimas 3 conversas
            if str(conv["id"]) != str(conversation_id):  # Excluir conversa atual
                conv_messages = await self.db.get_conversation_messages(
                    str(conv["id"]), user_id, limit=6  # Últimas 3 trocas
                )
                if conv_messages:
                    previous_conversations_detail.append({
                        "data": conv["last_message_at"].strftime("%d/%m"),
                        "resumo": conv.get("resumo", ""),
                        "mensagens": conv_messages
                    })

        # 5. Decidir modelo (throttling)
        model = self._select_model(user)

        # 6. Construir prompts SEPARADOS (melhor para caching)
        is_first = len(recent_conversations) <= 1 and len(messages) == 0

        # SYSTEM: só persona/regras (estável, cacheable)
        system_prompt = self._build_system_prompt(is_first_conversation=is_first)

        # CONTEXTO: memórias + perfil + psicológico + aprendizado (dinâmico)
        context_message = self._build_context_message(
            profile=profile,
            history=recent_conversations,
            previous_conversations=previous_conversations_detail,
            prayer_requests=prayer_requests,
            permanent_memory=permanent_memory,
            psychological_context=psychological_context,
            learning_context=learning_context
        )

        # 7. Preparar mensagens para a API
        api_messages = []

        # Adicionar contexto como primeira mensagem (se houver)
        if context_message:
            api_messages.append({
                "role": "user",
                "content": f"[CONTEXTO DO USUÁRIO]\n{context_message}"
            })
            api_messages.append({
                "role": "assistant",
                "content": "Entendido, vou usar essas informações na conversa."
            })

        # Adicionar histórico da conversa atual
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Adicionar mensagem atual (com suporte a imagem/PDF)
        has_images = image_data or images
        if has_images:
            user_content = []

            # Múltiplas imagens (PDF)
            if images:
                for img_data, img_type in images:
                    user_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": img_type,
                            "data": img_data
                        }
                    })
            # Imagem única
            elif image_data and image_media_type:
                user_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_data
                    }
                })

            # Adicionar texto
            user_content.append({
                "type": "text",
                "text": message if message else "O que você vê nesta imagem?"
            })

            api_messages.append({"role": "user", "content": user_content})
        else:
            # Mensagem apenas texto
            api_messages.append({"role": "user", "content": message})

        # 8. Chamar Claude (tokens maiores para imagens/PDFs)
        max_tokens = MAX_TOKENS_RESPONSE * 2 if has_images else MAX_TOKENS_RESPONSE
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=api_messages
        )

        reply = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        # 9. Salvar mensagens no banco (indicar se tinha imagem/PDF)
        if images:
            saved_content = f"[📄 PDF enviado - {len(images)} páginas]\n{message}"
        elif image_data:
            saved_content = f"[📷 Imagem enviada]\n{message}"
        else:
            saved_content = message
        await self.db.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=saved_content
        )

        await self.db.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=reply,
            tokens_used=tokens_used,
            model_used=model
        )

        # 10. Incrementar contador de mensagens
        await self.db.increment_message_count(user_id)

        # 11. MEMÓRIA ETERNA: Extrair fatos da mensagem do usuário (SEMPRE)
        # Isso é crítico - extraímos memórias de TODA mensagem do usuário
        await self._extract_memories(user_id, message, conversation_id)

        # 12. Atualizar resumo periodicamente (a cada 5 mensagens para ter resumo logo)
        message_count = len(messages) + 2  # +2 pelas novas mensagens
        if message_count % 5 == 0:
            await self._update_conversation_summary(conversation_id, user_id)

        # 13. Extrair insights periodicamente (a cada 20 mensagens)
        if message_count % 20 == 0:
            await self._extract_insights(conversation_id, user_id)

        # 14. Atualizar perfil psicológico periodicamente (a cada 30 mensagens)
        total_messages = user.get("total_messages", 0) if user else 0
        if total_messages > 0 and total_messages % 30 == 0:
            await self._analyze_psychological_profile(user_id)

        # 15. APRENDIZADO: Registrar interação e guardar resposta para feedback futuro
        try:
            await self.learning_engine.record_interaction(
                user_id=user_id,
                conversation_id=str(conversation_id),
                user_message=message,
                ai_response=reply,
                strategy_used=optimal_strategy,
                emotion_before=current_context.get("emotional_state", "neutro"),
                emotion_after="neutro",  # Será atualizado na próxima mensagem
                response_time=0
            )
        except Exception as e:
            print(f"[LEARNING] Error recording interaction: {e}")

        # 16. LAYER 2: Registrar estado emocional na timeline (interno)
        try:
            detected_emotion = await self._detect_emotion_for_timeline(message, reply)
            if detected_emotion:
                await self.db.record_emotional_state(
                    user_id=user_id,
                    emotion=detected_emotion["emotion"],
                    intensity=detected_emotion.get("intensity", 0.5),
                    confidence=detected_emotion.get("confidence", 0.7),
                    trigger=detected_emotion.get("trigger"),
                    themes=detected_emotion.get("themes", []),
                    conversation_id=str(conversation_id)
                )
        except Exception as e:
            print(f"[EMOTIONAL_TIMELINE] Error recording emotion: {e}")

        # 17. LAYER 2: Atualizar Health Score periodicamente (a cada 10 mensagens)
        if total_messages > 0 and total_messages % 10 == 0:
            try:
                health_score = await self.db.calculate_memory_health_score(user_id)
                await self.db.save_memory_health_score(user_id, health_score)
            except Exception as e:
                print(f"[HEALTH_SCORE] Error calculating: {e}")

        # Guardar resposta para detecção de feedback na próxima mensagem
        self._last_responses[user_id] = {
            "user_message": message,
            "ai_response": reply,
            "timestamp": time.time(),
            "strategy": optimal_strategy.value if hasattr(optimal_strategy, 'value') else str(optimal_strategy)
        }

        return {
            "response": reply,
            "conversation_id": str(conversation_id),
            "model_used": model,
            "tokens_used": tokens_used
        }

    def _select_model(self, user: dict) -> str:
        """
        Seleciona modelo baseado no status do usuário:
        - Assinantes (premium): SEMPRE Sonnet 4 (melhor qualidade)
        - Trial/Free: Haiku 4 (economia)
        """
        if not user:
            return AI_MODEL_FALLBACK

        # Assinantes SEMPRE usam o modelo premium (Sonnet 4)
        if user.get("is_premium", False):
            return AI_MODEL_PRIMARY

        # Trial e usuários free usam Haiku 4 (economia)
        return AI_MODEL_FALLBACK

    def _build_system_prompt(
        self,
        is_first_conversation: bool = False
    ) -> str:
        """
        Constrói APENAS o system prompt base (persona/regras).
        Memórias e contexto vão em mensagens separadas para melhor caching.
        """
        # Injetar data atual no prompt (Claude não sabe a data automaticamente!)
        now = datetime.now()
        # Mapeamento de meses para português
        meses_pt = {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto",
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
        }
        dias_semana_pt = {
            0: "segunda-feira", 1: "terça-feira", 2: "quarta-feira",
            3: "quinta-feira", 4: "sexta-feira", 5: "sábado", 6: "domingo"
        }
        dia_semana = dias_semana_pt[now.weekday()]
        mes = meses_pt[now.month]
        data_formatada = f"{dia_semana}, {now.day} de {mes} de {now.year}"

        date_context = f"DATA DE HOJE: {data_formatada}\n\n"

        prompt = date_context + AISYSTER_PERSONA

        # Se é primeira conversa, adicionar prompt de onboarding
        if is_first_conversation:
            prompt += f"\n\n{ONBOARDING_PROMPT}"

        return prompt

    def _build_context_message(
        self,
        profile: dict,
        history: List[dict],
        previous_conversations: List[dict],
        prayer_requests: List[dict],
        permanent_memory: str,
        psychological_context: str = "",
        learning_context: str = ""
    ) -> str:
        """
        Constrói mensagem de CONTEXTO separada (memórias + perfil + psicológico + aprendizado).
        Isso permite melhor prompt caching do SYSTEM.
        """
        context_parts = []

        # MEMÓRIA PERMANENTE (mais importante)
        if permanent_memory:
            context_parts.append(permanent_memory)

        # Contexto do perfil
        if profile:
            user_context = build_user_context(
                profile=profile,
                history=[
                    {"data": c["last_message_at"].strftime("%d/%m"), "resumo": c.get("resumo", "")}
                    for c in history if c.get("resumo")
                ],
                prayer_requests=prayer_requests,
                learning_context=learning_context
            )
            context_parts.append(user_context)

        # Contexto das conversas recentes
        if previous_conversations:
            conv_context = "=== CONVERSAS RECENTES ===\n"
            for conv in previous_conversations:
                conv_context += f"--- {conv['data']} ---\n"
                if conv.get('resumo'):
                    conv_context += f"{conv['resumo']}\n"
            context_parts.append(conv_context)

        # PERFIL PSICOLÓGICO (guia como abordar)
        if psychological_context:
            context_parts.append(psychological_context)

        # CONTEXTO DE APRENDIZADO (estratégia e ajustes)
        if learning_context:
            context_parts.append(f"=== APRENDIZADO ===\n{learning_context}")

        return "\n\n".join(context_parts) if context_parts else ""

    async def _update_conversation_summary(self, conversation_id: str, user_id: str):
        """
        Gera resumo da conversa usando IA
        """
        messages = await self.db.get_conversation_messages(conversation_id, user_id, limit=100)

        if len(messages) < 5:
            return

        # Formatar conversa para resumo
        conversation_text = "\n".join([
            f"{'Usuário' if m['role'] == 'user' else 'AiSyster'}: {m['content']}"
            for m in messages
        ])

        prompt = SUMMARY_PROMPT.format(conversation=conversation_text)

        response = self.client.messages.create(
            model=AI_MODEL_FALLBACK,  # Usa modelo econômico para resumos
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        resumo = response.content[0].text

        # Atualizar no banco
        await self.db.update_conversation_summary(
            conversation_id=conversation_id,
            resumo=resumo
        )

    async def _extract_insights(self, conversation_id: str, user_id: str):
        """
        Extrai insights sobre o usuário da conversa
        """
        messages = await self.db.get_conversation_messages(conversation_id, user_id, limit=100)

        if len(messages) < 10:
            return

        conversation_text = "\n".join([
            f"{'Usuário' if m['role'] == 'user' else 'AiSyster'}: {m['content']}"
            for m in messages
        ])

        prompt = INSIGHT_EXTRACTION_PROMPT.format(conversation=conversation_text)

        response = self.client.messages.create(
            model=AI_MODEL_FALLBACK,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            # Tenta parsear JSON
            result = json.loads(response.content[0].text)
            insights = result.get("insights", [])

            for insight in insights:
                await self.db.save_insight(
                    user_id=user_id,
                    categoria=insight["categoria"],
                    insight=insight["descricao"],
                    confianca=insight.get("confianca", 0.7),
                    conversa_id=conversation_id
                )
        except json.JSONDecodeError:
            pass  # Ignora se não conseguir parsear

    async def _extract_memories(self, user_id: str, user_message: str, conversation_id: str):
        """
        MEMÓRIA ETERNA: Extrai fatos importantes da mensagem do usuário
        Este é o coração do sistema de memória - roda a cada mensagem
        """
        # Gating melhorado: keywords importantes mesmo em mensagens curtas
        TRIGGER_KEYWORDS = [
            "casei", "divorc", "morr", "nasc", "filho", "filha", "grávida",
            "demit", "emprego", "trabalho", "mudei", "convert", "batiz",
            "igreja", "anos", "chamo", "nome", "moro", "vivo", "mudou",
            "florida", "brasil", "eua", "país", "cidade", "estado",
            "irmão", "irmã", "irmãos", "irmãs", "cunhado", "cunhada",
            "sogro", "sogra", "sobrinho", "sobrinha", "primo", "prima",
            "marido", "esposo", "esposa", "pai", "mãe", "avó", "avô"
        ]

        message_lower = user_message.lower()
        has_trigger = any(kw in message_lower for kw in TRIGGER_KEYWORDS)

        # Só processa se: mensagem >= 15 chars OU tem keyword importante
        if len(user_message) < 15 and not has_trigger:
            return

        try:
            # NOVO: Buscar memórias atuais para contexto de conflitos
            current_memories = await self.db.get_user_memories(user_id, limit=30)
            memories_context = ""
            if current_memories:
                memories_context = "\n\nMEMÓRIAS ATUAIS DA PESSOA:\n"
                for mem in current_memories:
                    memories_context += f"- [{mem['categoria']}] {mem['fato']}\n"

            # Usar modelo econômico para extração (roda frequentemente)
            response = self.client.messages.create(
                model=AI_MODEL_FALLBACK,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": MEMORY_EXTRACTION_PROMPT.format(
                        conversation=f"Usuário: {user_message}"
                    ) + memories_context
                }]
            )

            result_text = response.content[0].text

            # Tentar parsear JSON com múltiplas estratégias
            result = None
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Estratégia 1: Extrair JSON de dentro do texto
                import re

                # Tentar encontrar o JSON completo
                json_match = re.search(r'\{[\s\S]*"memorias"[\s\S]*\}', result_text)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        # Estratégia 2: Limpar JSON malformado
                        cleaned = json_match.group()
                        # Remover trailing commas antes de ] ou }
                        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
                        try:
                            result = json.loads(cleaned)
                        except json.JSONDecodeError as e2:
                            print(f"[MEMORY] JSON parse failed after cleanup: {e2}")
                            print(f"[MEMORY] Raw response: {result_text[:500]}")
                            return

            if not result:
                return

            memorias = result.get("memorias", [])

            # Salvar cada memória extraída com suporte a ações
            for mem in memorias:
                if mem.get("fato"):
                    action = mem.get("action", "upsert")
                    await self.db.save_memory(
                        user_id=user_id,
                        categoria=mem.get("categoria", "CONTEXTO"),
                        fato=mem["fato"],
                        detalhes=mem.get("detalhes"),
                        importancia=mem.get("importancia", 5),
                        conversa_id=conversation_id,
                        action=action,
                        confidence=mem.get("confianca", 0.8)
                    )

        except Exception as e:
            # Não deixar erros de extração quebrarem o chat
            print(f"Erro ao extrair memórias: {e}")
            pass

    async def _analyze_psychological_profile(self, user_id: str):
        """
        Analisa o perfil psicológico do usuário baseado em conversas recentes.
        Roda periodicamente (a cada ~50 mensagens ou quando há muitos dados novos).
        """
        try:
            # Buscar últimas conversas com mensagens
            conversations = await self.db.get_recent_conversations(user_id, limit=5)

            if not conversations:
                return

            # Coletar mensagens das conversas
            all_messages = []
            for conv in conversations:
                messages = await self.db.get_conversation_messages(
                    str(conv["id"]), user_id, limit=30
                )
                for msg in messages:
                    if msg["role"] == "user":  # Só mensagens do usuário
                        all_messages.append(msg["content"])

            if len(all_messages) < 30:  # Mínimo de 30 mensagens para análise inicial confiável
                print(f"[PSYCH] Insufficient messages ({len(all_messages)}/30) for user {user_id[:8]}")
                return

            # Formatar para análise
            conversations_text = "\n".join([
                f"- {msg[:500]}" for msg in all_messages[-50:]  # Últimas 50 msgs
            ])

            # Chamar IA para análise
            response = self.client.messages.create(
                model=AI_MODEL_FALLBACK,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": PSYCHOLOGICAL_ANALYSIS_PROMPT.format(
                        conversations=conversations_text
                    )
                }]
            )

            result_text = response.content[0].text

            # Parsear JSON
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    return

            # Salvar perfil
            await self.db.save_psychological_profile(user_id, result)
            print(f"[PSYCH] Profile updated for user {user_id[:8]}...")

        except Exception as e:
            print(f"Erro ao analisar perfil psicológico: {e}")

    async def _detect_emotion_for_timeline(
        self,
        user_message: str,
        ai_response: str
    ) -> Optional[Dict]:
        """
        LAYER 2: Detecta estado emocional da mensagem do usuário.
        Usa heurísticas rápidas (sem chamar API) para eficiência.
        Retorna dict com: emotion, intensity, confidence, trigger, themes
        """
        message_lower = user_message.lower()

        # Mapeamento de palavras-chave para emoções
        EMOTION_KEYWORDS = {
            "ansioso": ["ansiedad", "ansios", "nervos", "preocupad", "aflito", "inquiet", "agitad"],
            "triste": ["triste", "tristeza", "deprimi", "chorand", "chorei", "infeliz", "desanim", "desesper"],
            "angustiado": ["angústia", "angustia", "sufocad", "apert", "pesad", "oprimid", "atormentad"],
            "estressado": ["estress", "cansad", "exaust", "esgotad", "sobrecarreg", "pressão", "pressao"],
            "frustrado": ["frustrad", "irritad", "raiva", "bravo", "furioso", "indign"],
            "alegre": ["feliz", "alegr", "content", "anim", "empolgad", "eufóric", "entusiasm"],
            "grato": ["grat", "agradeç", "abençoa", "benção", "bencao"],
            "esperançoso": ["esperanç", "confian", "otimis", "melhor", "acredit", "fé", "fe "],
            "confuso": ["confus", "perdid", "sem rumo", "não sei", "dúvida", "incerteza"],
            "culpado": ["culpa", "errei", "pequei", "arrepend", "vergonha", "falh"],
            "medo": ["medo", "assustado", "pânico", "panico", "pavor", "terror", "ameaç"],
            "solitário": ["solid", "sozin", "isolad", "abandon", "ninguém", "vazio"],
            "neutro": []
        }

        # Mapeamento de triggers (contexto)
        TRIGGER_KEYWORDS = {
            "trabalho": ["trabalho", "emprego", "chefe", "colega", "demit", "salário", "carreira", "profiss"],
            "família": ["família", "pai", "mãe", "filho", "esposo", "esposa", "marido", "irmão", "irmã"],
            "saúde": ["saúde", "doença", "médico", "hospital", "diagnóstico", "dor", "tratament"],
            "relacionamento": ["relacionament", "namorad", "noiv", "casament", "separaç", "divórc", "brigar"],
            "financeiro": ["dinh", "conta", "dívida", "pagament", "financ", "gast", "econom"],
            "espiritual": ["deus", "oraç", "igreja", "fé", "biblia", "pecad", "salvaç"],
            "futuro": ["futur", "amanhã", "próxim", "plan", "sonho", "meta", "objetivo"],
        }

        # Detectar emoção principal
        detected_emotion = "neutro"
        max_matches = 0
        intensity = 0.5

        for emotion, keywords in EMOTION_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in message_lower)
            if matches > max_matches:
                max_matches = matches
                detected_emotion = emotion

        # Intensificadores
        INTENSIFIERS = ["muito", "demais", "super", "extremament", "totalment", "completament"]
        DIMINISHERS = ["um pouco", "levemente", "talvez", "meio"]

        if any(i in message_lower for i in INTENSIFIERS):
            intensity = min(intensity + 0.25, 1.0)
        if any(d in message_lower for d in DIMINISHERS):
            intensity = max(intensity - 0.2, 0.2)

        # Se não detectou nada, retornar None (não registrar)
        if detected_emotion == "neutro" and max_matches == 0:
            # Verificar se há emoções positivas ou negativas óbvias
            positive_indicators = ["obrigad", "amém", "glória", "aleluia", "maravilh", "ótim", "perfect"]
            negative_indicators = ["não consigo", "não aguento", "cansado de", "estou mal", "preciso de ajuda"]

            if any(p in message_lower for p in positive_indicators):
                detected_emotion = "grato"
                intensity = 0.6
            elif any(n in message_lower for n in negative_indicators):
                detected_emotion = "angustiado"
                intensity = 0.6
            else:
                return None  # Mensagem neutra, não registrar

        # Detectar trigger/contexto
        detected_trigger = None
        for trigger, keywords in TRIGGER_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                detected_trigger = trigger
                break

        # Extrair temas (palavras-chave gerais)
        themes = []
        if detected_trigger:
            themes.append(detected_trigger)

        # Calcular confiança baseada em quantas keywords foram encontradas
        confidence = min(0.5 + (max_matches * 0.15), 0.95)

        return {
            "emotion": detected_emotion,
            "intensity": intensity,
            "confidence": confidence,
            "trigger": detected_trigger,
            "themes": themes
        }

    async def get_user_emotional_summary(self, user_id: str) -> Dict:
        """
        LAYER 2: Retorna resumo emocional do usuário para uso interno.
        Combina timeline, padrões e tendência.
        """
        try:
            patterns = await self.db.get_emotional_patterns(user_id, days=30)
            trend = await self.db.get_emotional_trend(user_id)

            return {
                "dominant_emotion": patterns.get("dominant_emotion", "neutro"),
                "avg_intensity": patterns.get("avg_intensity", 0.5),
                "trend": trend,
                "emotions_detected": patterns.get("emotions_detected", []),
                "needs_attention": trend == "worsening" or patterns.get("avg_intensity", 0.5) > 0.7
            }
        except Exception as e:
            print(f"[EMOTIONAL_SUMMARY] Error: {e}")
            return {
                "dominant_emotion": "neutro",
                "avg_intensity": 0.5,
                "trend": "stable",
                "emotions_detected": [],
                "needs_attention": False
            }

    async def chat_trial(
        self,
        message: str,
        history: List[dict],
        user: dict
    ) -> str:
        """
        Chat simplificado para usuários em modo trial (sem conta)
        Usa modelo econômico e sem persistência
        """
        from app.prompts import AISYSTER_PERSONA

        # Injetar data atual (Claude não sabe automaticamente!)
        now = datetime.now()
        meses_pt = {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto",
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
        }
        dias_semana_pt = {
            0: "segunda-feira", 1: "terça-feira", 2: "quarta-feira",
            3: "quinta-feira", 4: "sexta-feira", 5: "sábado", 6: "domingo"
        }
        dia_semana = dias_semana_pt[now.weekday()]
        mes = meses_pt[now.month]
        data_formatada = f"{dia_semana}, {now.day} de {mes} de {now.year}"

        # System prompt simplificado para trial
        system_prompt = f"DATA DE HOJE: {data_formatada}\n\n" + AISYSTER_PERSONA + """

NOTA: Este é um usuário visitante experimentando o AiSyster.
Seja acolhedor e mostre o valor do app, mas mantenha respostas concisas.
Convide-o a criar uma conta para uma experiência mais personalizada."""

        # Preparar mensagens
        api_messages = history.copy()
        api_messages.append({"role": "user", "content": message})

        # Usar modelo econômico
        response = self.client.messages.create(
            model=AI_MODEL_FALLBACK,
            max_tokens=512,  # Respostas mais curtas para trial
            system=system_prompt,
            messages=api_messages
        )

        return response.content[0].text

    async def generate_devotional(self, tema: Optional[str] = None) -> Dict:
        """
        Gera devocional do dia
        """
        from app.prompts import DEVOTIONAL_GENERATION_PROMPT

        prompt = DEVOTIONAL_GENERATION_PROMPT.format(
            tema=tema or "esperança e fé no dia a dia"
        )

        response = self.client.messages.create(
            model=AI_MODEL_PRIMARY,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {
                "versiculo": "O Senhor é o meu pastor; nada me faltará.",
                "referencia": "Salmo 23:1",
                "meditacao": "Deus cuida de cada detalhe da sua vida.",
                "oracao": "Senhor, ajuda-me a confiar em Ti. Amém."
            }

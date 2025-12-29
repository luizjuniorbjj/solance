"""
SoulHaven - Sistema de Aprendizado Contínuo
Motor que melhora a IA com cada interação
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio


# ============================================
# TIPOS DE FEEDBACK
# ============================================

class FeedbackType(Enum):
    """Tipos de feedback implícito e explícito"""
    POSITIVE_EXPLICIT = "positive_explicit"  # Usuário disse que gostou
    NEGATIVE_EXPLICIT = "negative_explicit"  # Usuário disse que não gostou
    ENGAGEMENT_HIGH = "engagement_high"  # Resposta longa, continuou conversa
    ENGAGEMENT_LOW = "engagement_low"  # Resposta curta, abandonou
    EMOTIONAL_IMPROVEMENT = "emotional_improvement"  # Humor melhorou
    EMOTIONAL_DECLINE = "emotional_decline"  # Humor piorou
    RETURNED_SOON = "returned_soon"  # Voltou logo (indica satisfação)
    LONG_ABSENCE = "long_absence"  # Sumiu por muito tempo


class ResponseStrategy(Enum):
    """Estratégias de resposta que podem ser ajustadas"""
    EMPATHY_FIRST = "empathy_first"  # Acolher antes de aconselhar
    DIRECT_ADVICE = "direct_advice"  # Ir direto ao conselho
    QUESTION_BASED = "question_based"  # Fazer perguntas
    SCRIPTURE_HEAVY = "scripture_heavy"  # Muitos versículos
    PRACTICAL_STEPS = "practical_steps"  # Passos práticos
    THEOLOGICAL_DEPTH = "theological_depth"  # Profundidade teológica
    STORY_BASED = "story_based"  # Usar histórias e exemplos
    BRIEF = "brief"  # Respostas curtas
    DETAILED = "detailed"  # Respostas longas


# ============================================
# DETECTOR DE FEEDBACK IMPLÍCITO
# ============================================

class ImplicitFeedbackDetector:
    """
    Detecta feedback do usuário sem perguntar diretamente
    """

    # Indicadores de feedback positivo
    POSITIVE_INDICATORS = [
        "obrigado", "obrigada", "valeu", "isso ajudou", "faz sentido",
        "entendi", "você tem razão", "verdade", "amém", "que bom",
        "me sinto melhor", "aliviado", "aliviada", "exatamente",
        "isso mesmo", "era isso", "perfeito", "maravilhoso"
    ]

    # Indicadores de feedback negativo
    NEGATIVE_INDICATORS = [
        "não é isso", "você não entendeu", "não ajuda", "não adianta",
        "fácil falar", "você não sabe", "mas", "porém", "entretanto",
        "não concordo", "discordo", "errado", "não é bem assim"
    ]

    # Indicadores de desengajamento
    DISENGAGEMENT_INDICATORS = [
        "ok", "tá", "sei", "hm", "tanto faz", "deixa pra lá",
        "esquece", "não importa"
    ]

    @classmethod
    def detect_feedback(cls, user_message: str, ai_response: str,
                       user_response: str, time_to_respond: float) -> List[FeedbackType]:
        """
        Detecta feedback implícito baseado na resposta do usuário
        """
        feedbacks = []
        response_lower = user_response.lower()

        # Verifica indicadores positivos
        positive_count = sum(1 for ind in cls.POSITIVE_INDICATORS if ind in response_lower)
        if positive_count >= 2:
            feedbacks.append(FeedbackType.POSITIVE_EXPLICIT)

        # Verifica indicadores negativos
        negative_count = sum(1 for ind in cls.NEGATIVE_INDICATORS if ind in response_lower)
        if negative_count >= 2:
            feedbacks.append(FeedbackType.NEGATIVE_EXPLICIT)

        # Verifica engajamento pela extensão da resposta
        if len(user_response) > 100:
            feedbacks.append(FeedbackType.ENGAGEMENT_HIGH)
        elif len(user_response) < 20:
            # Verifica se é desengajamento
            if any(ind in response_lower for ind in cls.DISENGAGEMENT_INDICATORS):
                feedbacks.append(FeedbackType.ENGAGEMENT_LOW)

        # Verifica tempo de resposta (muito rápido pode indicar não leu)
        if time_to_respond < 2.0 and len(ai_response) > 200:
            feedbacks.append(FeedbackType.ENGAGEMENT_LOW)

        return feedbacks

    @classmethod
    def detect_emotional_shift(cls, emotion_before: str, emotion_after: str) -> Optional[FeedbackType]:
        """
        Detecta mudança emocional após resposta da IA
        """
        positive_states = ["esperancoso", "grato", "alegre", "neutro"]
        negative_states = ["ansioso", "triste", "irritado", "culpado", "medo"]

        was_negative = emotion_before in negative_states
        is_positive = emotion_after in positive_states
        is_negative = emotion_after in negative_states
        was_positive = emotion_before in positive_states

        if was_negative and is_positive:
            return FeedbackType.EMOTIONAL_IMPROVEMENT
        elif was_positive and is_negative:
            return FeedbackType.EMOTIONAL_DECLINE

        return None


# ============================================
# MOTOR DE APRENDIZADO
# ============================================

class LearningEngine:
    """
    Motor que ajusta o comportamento da IA baseado em feedback
    """

    def __init__(self, db):
        self.db = db

    async def record_interaction(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        strategy_used: ResponseStrategy,
        emotion_before: str,
        emotion_after: str,
        response_time: float
    ):
        """
        Registra uma interação para aprendizado
        """
        interaction = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "user_message_length": len(user_message),
            "ai_response_length": len(ai_response),
            "strategy_used": strategy_used.value,
            "emotion_before": emotion_before,
            "emotion_after": emotion_after,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Detectar mudança emocional
        emotional_feedback = ImplicitFeedbackDetector.detect_emotional_shift(
            emotion_before, emotion_after
        )

        if emotional_feedback:
            interaction["emotional_feedback"] = emotional_feedback.value

        # Salvar no banco
        await self._save_interaction(user_id, interaction)

    async def process_user_response(
        self,
        user_id: str,
        original_ai_response: str,
        user_response: str,
        time_to_respond: float,
        original_user_message: str
    ) -> List[FeedbackType]:
        """
        Processa a resposta do usuário para extrair feedback
        """
        feedbacks = ImplicitFeedbackDetector.detect_feedback(
            original_user_message,
            original_ai_response,
            user_response,
            time_to_respond
        )

        # Salvar feedbacks
        for feedback in feedbacks:
            await self._save_feedback(user_id, feedback, original_ai_response)

        return feedbacks

    async def get_optimal_strategy(self, user_id: str, current_context: Dict) -> ResponseStrategy:
        """
        Determina a melhor estratégia de resposta baseada no histórico
        """
        # Buscar histórico de estratégias
        strategy_scores = await self._get_strategy_scores(user_id)

        # Ajustar baseado no contexto atual
        emotional_state = current_context.get("emotional_state", "neutro")
        communication_style = current_context.get("communication_style", "acolhedor")
        urgency = current_context.get("urgency", 0)

        # Alta urgência sempre usa empatia primeiro
        if urgency > 0.7:
            return ResponseStrategy.EMPATHY_FIRST

        # Baseado no estilo de comunicação
        if communication_style == "direto":
            preferred = [ResponseStrategy.DIRECT_ADVICE, ResponseStrategy.PRACTICAL_STEPS]
        elif communication_style == "teologico":
            preferred = [ResponseStrategy.THEOLOGICAL_DEPTH, ResponseStrategy.SCRIPTURE_HEAVY]
        elif communication_style == "reflexivo":
            preferred = [ResponseStrategy.QUESTION_BASED, ResponseStrategy.STORY_BASED]
        else:  # acolhedor
            preferred = [ResponseStrategy.EMPATHY_FIRST, ResponseStrategy.STORY_BASED]

        # Escolher a melhor estratégia preferida que teve bom histórico
        for strategy in preferred:
            if strategy_scores.get(strategy.value, 0.5) > 0.4:
                return strategy

        # Default
        return ResponseStrategy.EMPATHY_FIRST

    async def adjust_profile(self, user_id: str, feedbacks: List[FeedbackType]):
        """
        Ajusta o perfil do usuário baseado nos feedbacks
        """
        profile = await self.db.get_user_profile(user_id)
        if not profile:
            return

        adjustments = {}

        for feedback in feedbacks:
            if feedback == FeedbackType.POSITIVE_EXPLICIT:
                # Aumentar confiança no estilo atual
                adjustments["style_confidence_boost"] = 0.1

            elif feedback == FeedbackType.NEGATIVE_EXPLICIT:
                # Diminuir confiança, tentar abordagem diferente
                adjustments["style_confidence_decrease"] = 0.15

            elif feedback == FeedbackType.EMOTIONAL_IMPROVEMENT:
                # Registrar o que funcionou
                adjustments["effective_interaction"] = True

            elif feedback == FeedbackType.EMOTIONAL_DECLINE:
                # Registrar o que não funcionou
                adjustments["ineffective_interaction"] = True

            elif feedback == FeedbackType.ENGAGEMENT_LOW:
                # Pessoa pode preferir respostas mais curtas
                adjustments["prefer_brief"] = True

            elif feedback == FeedbackType.ENGAGEMENT_HIGH:
                # Pessoa gosta de respostas detalhadas
                adjustments["prefer_detailed"] = True

        # Aplicar ajustes
        await self._apply_adjustments(user_id, adjustments)

    async def detect_patterns(self, user_id: str) -> Dict:
        """
        Detecta padrões de comportamento do usuário
        """
        # Buscar histórico de interações
        interactions = await self._get_interaction_history(user_id, days=30)

        if len(interactions) < 5:
            return {}

        patterns = {}

        # Padrão de horário
        hours = {}
        for i in interactions:
            # Usar created_at do banco (pode ser datetime ou string)
            ts = i.get("created_at") or i.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                hours[ts.hour] = hours.get(ts.hour, 0) + 1

        if hours:
            peak_hour = max(hours, key=hours.get)
            patterns["peak_activity_hour"] = peak_hour

        # Padrão de dias da semana
        days = {}
        for i in interactions:
            ts = i.get("created_at") or i.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                day = ts.strftime("%A")
                days[day] = days.get(day, 0) + 1

        if days:
            peak_day = max(days, key=days.get)
            patterns["peak_activity_day"] = peak_day

        # Padrão emocional por dia da semana
        emotional_patterns = {}
        for i in interactions:
            ts = i.get("created_at") or i.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                day = ts.strftime("%A")
                emotion = i.get("emotion_before", "neutro")
                if day not in emotional_patterns:
                    emotional_patterns[day] = []
                emotional_patterns[day].append(emotion)

        patterns["emotional_by_day"] = emotional_patterns

        # Temas recorrentes
        themes = {}
        for i in interactions:
            for theme in i.get("themes", []):
                themes[theme] = themes.get(theme, 0) + 1

        patterns["recurring_themes"] = themes

        return patterns

    async def generate_proactive_insights(self, user_id: str) -> List[str]:
        """
        Gera insights proativos sobre o usuário
        """
        patterns = await self.detect_patterns(user_id)
        insights = []

        # Insight sobre horário de atividade
        peak_hour = patterns.get("peak_activity_hour")
        if peak_hour:
            if 22 <= peak_hour or peak_hour <= 2:
                insights.append(
                    "Você costuma conversar de madrugada. Isso pode indicar "
                    "dificuldade para dormir ou momentos de reflexão noturna."
                )
            elif 6 <= peak_hour <= 8:
                insights.append(
                    "Você costuma conversar pela manhã. Que bom começar o dia "
                    "buscando orientação!"
                )

        # Insight sobre padrões emocionais
        emotional = patterns.get("emotional_by_day", {})
        for day, emotions in emotional.items():
            anxiety_count = emotions.count("ansioso")
            if anxiety_count >= 3:
                insights.append(
                    f"Percebi que você tende a ficar mais ansioso(a) às {day}s. "
                    "Há algo específico que acontece nesse dia?"
                )

        # Insight sobre temas recorrentes
        themes = patterns.get("recurring_themes", {})
        if themes:
            top_theme = max(themes, key=themes.get)
            if themes[top_theme] >= 5:
                insights.append(
                    f"O tema '{top_theme}' aparece frequentemente em nossas conversas. "
                    "Talvez valha a pena explorarmos isso mais profundamente."
                )

        return insights

    # ============================================
    # MÉTODOS PRIVADOS (BANCO DE DADOS)
    # ============================================

    async def _save_interaction(self, user_id: str, interaction: Dict):
        """Salva interação no banco"""
        await self.db.save_learning_interaction(
            user_id=user_id,
            conversation_id=interaction.get("conversation_id"),
            strategy_used=interaction.get("strategy_used"),
            emotion_before=interaction.get("emotion_before"),
            emotion_after=interaction.get("emotion_after"),
            response_time=interaction.get("response_time"),
            user_message_length=interaction.get("user_message_length"),
            ai_response_length=interaction.get("ai_response_length")
        )

    async def _save_feedback(self, user_id: str, feedback: FeedbackType, context: str):
        """Salva feedback no banco"""
        import uuid as uuid_module
        # Buscar última estratégia usada
        strategy = None
        try:
            # Converter user_id para UUID
            user_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
            async with self.db.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT strategy_used FROM learning_interactions
                    WHERE user_id = $1
                    ORDER BY created_at DESC LIMIT 1
                """, user_uuid)
                if row:
                    strategy = row["strategy_used"]
        except Exception as e:
            print(f"[LEARNING] Error getting strategy: {e}")
            pass

        await self.db.save_learning_feedback(
            user_id=user_id,
            feedback_type=feedback.value,
            strategy_used=strategy,
            context=context
        )

    async def _get_strategy_scores(self, user_id: str) -> Dict[str, float]:
        """Busca scores de estratégias"""
        return await self.db.get_strategy_scores(user_id)

    async def _apply_adjustments(self, user_id: str, adjustments: Dict):
        """Aplica ajustes ao perfil"""
        await self.db.update_user_preferred_style(user_id, adjustments)

    async def _get_interaction_history(self, user_id: str, days: int) -> List[Dict]:
        """Busca histórico de interações"""
        import uuid as uuid_module
        try:
            # Converter user_id para UUID
            user_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
            async with self.db.pool.acquire() as conn:
                # Verificar se tabela existe
                table_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'learning_interactions'
                    )
                """)

                if not table_exists:
                    return []

                rows = await conn.fetch("""
                    SELECT * FROM learning_interactions
                    WHERE user_id = $1 AND created_at > NOW() - INTERVAL '%s days'
                    ORDER BY created_at DESC
                """ % days, user_uuid)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[LEARNING] Error getting interaction history: {e}")
            return []


# ============================================
# CONTEXTO DE APRENDIZADO PARA PROMPT
# ============================================

class LearningContextBuilder:
    """
    Constrói contexto de aprendizado para injetar no prompt
    """

    @staticmethod
    def build_learning_context(
        optimal_strategy: ResponseStrategy,
        patterns: Dict,
        insights: List[str],
        recent_feedbacks: List[FeedbackType]
    ) -> str:
        """
        Constrói contexto de aprendizado para o prompt
        """
        context_parts = []

        # Estratégia recomendada
        strategy_descriptions = {
            ResponseStrategy.EMPATHY_FIRST: "Acolha primeiro, valide sentimentos antes de aconselhar.",
            ResponseStrategy.DIRECT_ADVICE: "Seja direto e objetivo. Vá ao ponto.",
            ResponseStrategy.QUESTION_BASED: "Use perguntas reflexivas para guiar a conversa.",
            ResponseStrategy.SCRIPTURE_HEAVY: "Use mais versículos bíblicos nas respostas.",
            ResponseStrategy.PRACTICAL_STEPS: "Ofereça passos práticos e acionáveis.",
            ResponseStrategy.THEOLOGICAL_DEPTH: "Aprofunde na teologia quando apropriado.",
            ResponseStrategy.STORY_BASED: "Use histórias e exemplos para ilustrar pontos.",
            ResponseStrategy.BRIEF: "Mantenha respostas concisas e diretas.",
            ResponseStrategy.DETAILED: "Desenvolva respostas mais completas e detalhadas."
        }

        context_parts.append(
            f"ESTRATÉGIA RECOMENDADA: {strategy_descriptions.get(optimal_strategy, '')}"
        )

        # Feedback recente
        if FeedbackType.NEGATIVE_EXPLICIT in recent_feedbacks:
            context_parts.append(
                "⚠️ Última resposta não foi bem recebida. Ajuste sua abordagem."
            )
        elif FeedbackType.POSITIVE_EXPLICIT in recent_feedbacks:
            context_parts.append(
                "Última resposta foi bem recebida. Continue nessa linha."
            )

        if FeedbackType.ENGAGEMENT_LOW in recent_feedbacks:
            context_parts.append(
                "Pessoa parece desengajada. Tente uma abordagem diferente ou seja mais breve."
            )

        # Padrões detectados
        if patterns.get("recurring_themes"):
            themes = patterns["recurring_themes"]
            top_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:2]
            if top_themes:
                context_parts.append(
                    f"Temas recorrentes: {', '.join([t[0] for t in top_themes])}"
                )

        return "\n".join(context_parts)

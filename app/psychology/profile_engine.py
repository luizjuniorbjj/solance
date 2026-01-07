"""
AiSyster - Motor de Perfil Psicológico
Análise profunda de comportamento e personalidade
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


# ============================================
# ENUMS E TIPOS
# ============================================

class CommunicationStyle(Enum):
    """Estilos de comunicação baseados em preferências"""
    DIRETO = "direto"  # Quer respostas objetivas e práticas
    REFLEXIVO = "reflexivo"  # Gosta de perguntas e reflexão
    ACOLHEDOR = "acolhedor"  # Precisa de validação emocional primeiro
    TEOLOGICO = "teologico"  # Prefere profundidade doutrinária


class EmotionalState(Enum):
    """Estados emocionais detectáveis"""
    ANSIOSO = "ansioso"
    TRISTE = "triste"
    IRRITADO = "irritado"
    CONFUSO = "confuso"
    ESPERANCOSO = "esperancoso"
    GRATO = "grato"
    NEUTRO = "neutro"
    CULPADO = "culpado"
    MEDO = "medo"
    ALEGRE = "alegre"


class ProcessingStyle(Enum):
    """Como a pessoa processa informações"""
    ANALITICO = "analitico"  # Precisa de lógica e argumentos
    EMOCIONAL = "emocional"  # Processa através de sentimentos
    PRATICO = "pratico"  # Quer saber o que fazer
    NARRATIVO = "narrativo"  # Aprende com histórias e exemplos


class AttachmentStyle(Enum):
    """Estilo de apego (influencia como busca ajuda)"""
    SEGURO = "seguro"  # Pede ajuda naturalmente
    ANSIOSO = "ansioso"  # Busca validação constantemente
    EVITATIVO = "evitativo"  # Relutante em pedir ajuda
    DESORGANIZADO = "desorganizado"  # Inconsistente


# ============================================
# SISTEMA DE PERFIL PSICOLÓGICO
# ============================================

class PsychologicalProfile:
    """
    Representa o perfil psicológico completo de um usuário
    """

    def __init__(self, user_id: str):
        self.user_id = user_id

        # Estilo de comunicação (aprendido)
        self.communication_style: CommunicationStyle = CommunicationStyle.ACOLHEDOR
        self.communication_confidence: float = 0.5

        # Estilo de processamento (aprendido)
        self.processing_style: ProcessingStyle = ProcessingStyle.EMOCIONAL
        self.processing_confidence: float = 0.5

        # Gatilhos emocionais conhecidos
        self.emotional_triggers: List[Dict] = []

        # Padrões de comportamento
        self.behavioral_patterns: List[Dict] = []

        # Temas recorrentes
        self.recurring_themes: Dict[str, int] = {}

        # Horários de maior atividade
        self.active_hours: Dict[int, int] = {}

        # Dias de maior atividade emocional
        self.emotional_days: Dict[str, List[str]] = {}

        # Respostas que funcionaram
        self.effective_responses: List[Dict] = []

        # Respostas que não funcionaram
        self.ineffective_responses: List[Dict] = []

        # Estado emocional atual
        self.current_emotional_state: EmotionalState = EmotionalState.NEUTRO

        # Histórico de estados emocionais
        self.emotional_history: List[Dict] = []

        # Nível de abertura (quão vulnerável a pessoa é)
        self.openness_level: float = 0.5

        # Resistência a correção
        self.correction_receptivity: float = 0.5

        # Preferência de profundidade teológica
        self.theological_depth: float = 0.5  # 0 = superficial, 1 = muito profundo


# ============================================
# ANALISADOR DE MENSAGENS
# ============================================

class MessageAnalyzer:
    """
    Analisa mensagens para extrair informações psicológicas
    """

    # Palavras-chave para detectar estados emocionais
    EMOTION_KEYWORDS = {
        EmotionalState.ANSIOSO: [
            "ansioso", "ansiosa", "preocupado", "preocupada", "nervoso", "nervosa",
            "apreensivo", "inquieto", "agitado", "tenso", "medo", "pânico",
            "não consigo parar de pensar", "e se", "fico pensando"
        ],
        EmotionalState.TRISTE: [
            "triste", "deprimido", "deprimida", "desanimado", "desanimada",
            "sem esperança", "vazio", "vazia", "sozinho", "sozinha", "chorando",
            "lágrimas", "dor", "sofrendo", "não aguento mais"
        ],
        EmotionalState.IRRITADO: [
            "irritado", "irritada", "raiva", "com raiva", "furioso", "furiosa",
            "bravo", "brava", "injusto", "absurdo", "não aguento", "odeio"
        ],
        EmotionalState.CONFUSO: [
            "confuso", "confusa", "não entendo", "perdido", "perdida",
            "não sei o que fazer", "dúvida", "incerto", "incerta"
        ],
        EmotionalState.CULPADO: [
            "culpado", "culpada", "culpa", "errei", "fiz errado", "não devia",
            "arrependo", "arrependido", "vergonha", "pecado", "pequei"
        ],
        EmotionalState.MEDO: [
            "medo", "assustado", "assustada", "temor", "pavor", "terror",
            "apavorado", "apavorada", "aterrorizado"
        ],
        EmotionalState.ESPERANCOSO: [
            "esperança", "confiante", "animado", "animada", "otimista",
            "melhorando", "deus vai", "acredito", "fé"
        ],
        EmotionalState.GRATO: [
            "grato", "grata", "agradeço", "obrigado", "obrigada", "gratidão",
            "abençoado", "abençoada", "deus é bom"
        ],
        EmotionalState.ALEGRE: [
            "feliz", "alegre", "contente", "maravilhoso", "maravilhosa",
            "que bom", "vitória", "consegui", "glória a deus"
        ]
    }

    # Indicadores de estilo de comunicação
    STYLE_INDICATORS = {
        CommunicationStyle.DIRETO: [
            "resumindo", "objetivamente", "direto ao ponto", "na prática",
            "o que eu faço", "me diz", "qual a solução"
        ],
        CommunicationStyle.REFLEXIVO: [
            "você acha que", "será que", "por que", "como assim",
            "me explica", "o que significa", "pensar sobre"
        ],
        CommunicationStyle.ACOLHEDOR: [
            "preciso desabafar", "só quero conversar", "me sinto",
            "ninguém entende", "você me ouve", "preciso de alguém"
        ],
        CommunicationStyle.TEOLOGICO: [
            "biblicamente", "teologicamente", "doutrina", "versículo",
            "o que a bíblia diz", "calvino", "reformado", "confissão"
        ]
    }

    # Indicadores de estilo de processamento
    PROCESSING_INDICATORS = {
        ProcessingStyle.ANALITICO: [
            "lógico", "faz sentido", "argumento", "razão", "porque",
            "entender", "explica", "como funciona"
        ],
        ProcessingStyle.EMOCIONAL: [
            "sinto", "senti", "coração", "alma", "doer", "dói",
            "machuca", "emocionado", "emocionada"
        ],
        ProcessingStyle.PRATICO: [
            "o que fazer", "como resolver", "passos", "prático",
            "aplicar", "ação", "próximo passo"
        ],
        ProcessingStyle.NARRATIVO: [
            "história", "aconteceu", "outro dia", "lembro", "vez que",
            "exemplo", "situação", "caso"
        ]
    }

    @classmethod
    def detect_emotional_state(cls, message: str) -> tuple[EmotionalState, float]:
        """
        Detecta o estado emocional da mensagem
        Retorna o estado e a confiança (0-1)
        """
        message_lower = message.lower()
        scores = {}

        for state, keywords in cls.EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in message_lower)
            if count > 0:
                scores[state] = count

        if not scores:
            return EmotionalState.NEUTRO, 0.5

        best_state = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_state] / 3)  # Normaliza

        return best_state, confidence

    @classmethod
    def detect_communication_style(cls, message: str) -> tuple[CommunicationStyle, float]:
        """
        Detecta o estilo de comunicação preferido
        """
        message_lower = message.lower()
        scores = {}

        for style, indicators in cls.STYLE_INDICATORS.items():
            count = sum(1 for ind in indicators if ind in message_lower)
            if count > 0:
                scores[style] = count

        if not scores:
            return CommunicationStyle.ACOLHEDOR, 0.3  # Default

        best_style = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_style] / 2)

        return best_style, confidence

    @classmethod
    def detect_processing_style(cls, message: str) -> tuple[ProcessingStyle, float]:
        """
        Detecta o estilo de processamento de informações
        """
        message_lower = message.lower()
        scores = {}

        for style, indicators in cls.PROCESSING_INDICATORS.items():
            count = sum(1 for ind in indicators if ind in message_lower)
            if count > 0:
                scores[style] = count

        if not scores:
            return ProcessingStyle.EMOCIONAL, 0.3  # Default

        best_style = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_style] / 2)

        return best_style, confidence

    @classmethod
    def extract_themes(cls, message: str) -> List[str]:
        """
        Extrai temas principais da mensagem
        """
        themes = []
        message_lower = message.lower()

        theme_keywords = {
            "ansiedade": ["ansiedade", "ansioso", "nervoso", "preocupação"],
            "relacionamento": ["casamento", "namoro", "marido", "esposa", "namorado", "namorada", "relacionamento"],
            "família": ["família", "pai", "mãe", "filho", "filha", "irmão", "irmã"],
            "trabalho": ["trabalho", "emprego", "chefe", "empresa", "carreira", "profissão", "demissão"],
            "saúde": ["saúde", "doença", "médico", "hospital", "dor", "doente"],
            "fé": ["fé", "dúvida", "deus", "oração", "igreja", "bíblia"],
            "culpa": ["culpa", "pecado", "errei", "arrependimento"],
            "medo": ["medo", "temor", "pânico", "terror"],
            "luto": ["morte", "morreu", "faleceu", "perdi", "luto", "saudade"],
            "finanças": ["dinheiro", "financeiro", "dívida", "conta", "pagar"],
            "autoestima": ["autoestima", "não me amo", "feia", "feio", "inútil", "fracasso"],
            "solidão": ["sozinho", "sozinha", "solidão", "ninguém", "abandonado"],
            "propósito": ["propósito", "sentido", "para quê", "vazio", "direção"]
        }

        for theme, keywords in theme_keywords.items():
            if any(kw in message_lower for kw in keywords):
                themes.append(theme)

        return themes

    @classmethod
    def detect_urgency(cls, message: str) -> float:
        """
        Detecta o nível de urgência/crise (0-1)
        """
        message_lower = message.lower()

        crisis_indicators = [
            ("suicídio", 1.0),
            ("me matar", 1.0),
            ("quero morrer", 1.0),
            ("não aguento mais", 0.8),
            ("desistir", 0.6),
            ("não vejo saída", 0.7),
            ("acabar com tudo", 0.9),
            ("me machucar", 0.9),
            ("automutilação", 0.9),
            ("sem esperança", 0.6),
            ("nunca vai melhorar", 0.5),
            ("ninguém se importa", 0.5)
        ]

        max_urgency = 0.0
        for phrase, urgency in crisis_indicators:
            if phrase in message_lower:
                max_urgency = max(max_urgency, urgency)

        return max_urgency

    @classmethod
    def analyze_message(cls, message: str) -> Dict:
        """
        Análise completa de uma mensagem
        """
        emotional_state, emotion_confidence = cls.detect_emotional_state(message)
        comm_style, comm_confidence = cls.detect_communication_style(message)
        proc_style, proc_confidence = cls.detect_processing_style(message)
        themes = cls.extract_themes(message)
        urgency = cls.detect_urgency(message)

        return {
            "emotional_state": emotional_state.value,
            "emotion_confidence": emotion_confidence,
            "communication_style": comm_style.value,
            "communication_confidence": comm_confidence,
            "processing_style": proc_style.value,
            "processing_confidence": proc_confidence,
            "themes": themes,
            "urgency": urgency,
            "message_length": len(message),
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================
# GERADOR DE CONTEXTO PSICOLÓGICO
# ============================================

class PsychologicalContextBuilder:
    """
    Constrói contexto psicológico para o prompt da IA
    """

    @staticmethod
    def build_context(profile: Dict, current_analysis: Dict) -> str:
        """
        Constrói contexto psicológico para injetar no prompt
        """
        context_parts = []

        # Estado emocional atual
        emotional_state = current_analysis.get("emotional_state", "neutro")
        context_parts.append(f"Estado emocional atual: {emotional_state}")

        # Nível de urgência
        urgency = current_analysis.get("urgency", 0)
        if urgency > 0.7:
            context_parts.append("⚠️ ALTA URGÊNCIA - Possível crise. Seja muito cuidadoso e acolhedor.")
        elif urgency > 0.4:
            context_parts.append("Atenção elevada - A pessoa pode estar passando por momento difícil.")

        # Estilo de comunicação preferido
        comm_style = profile.get("communication_style", "acolhedor")
        style_instructions = {
            "direto": "Prefere respostas objetivas e práticas. Vá ao ponto.",
            "reflexivo": "Gosta de perguntas que fazem pensar. Use perguntas reflexivas.",
            "acolhedor": "Precisa de validação emocional primeiro. Acolha antes de aconselhar.",
            "teologico": "Aprecia profundidade doutrinária. Pode usar termos teológicos."
        }
        context_parts.append(f"Estilo preferido: {style_instructions.get(comm_style, '')}")

        # Estilo de processamento
        proc_style = profile.get("processing_style", "emocional")
        proc_instructions = {
            "analitico": "Processa através de lógica. Use argumentos bem estruturados.",
            "emocional": "Processa através de sentimentos. Conecte com o coração.",
            "pratico": "Quer saber o que fazer. Ofereça passos práticos.",
            "narrativo": "Aprende com histórias. Use exemplos e narrativas."
        }
        context_parts.append(f"Processamento: {proc_instructions.get(proc_style, '')}")

        # Temas recorrentes
        recurring = profile.get("recurring_themes", {})
        if recurring:
            top_themes = sorted(recurring.items(), key=lambda x: x[1], reverse=True)[:3]
            themes_str = ", ".join([t[0] for t in top_themes])
            context_parts.append(f"Temas frequentes desta pessoa: {themes_str}")

        # Gatilhos conhecidos
        triggers = profile.get("emotional_triggers", [])
        if triggers:
            triggers_str = ", ".join([t.get("trigger", "") for t in triggers[:3]])
            context_parts.append(f"Gatilhos emocionais conhecidos: {triggers_str}")

        # Nível de abertura
        openness = profile.get("openness_level", 0.5)
        if openness < 0.3:
            context_parts.append("Esta pessoa é reservada. Não pressione por detalhes.")
        elif openness > 0.7:
            context_parts.append("Esta pessoa é aberta. Pode ir mais fundo na conversa.")

        # Receptividade a correção
        correction = profile.get("correction_receptivity", 0.5)
        if correction < 0.3:
            context_parts.append("Sensível a correção. Seja muito gentil ao corrigir.")
        elif correction > 0.7:
            context_parts.append("Receptiva a correção. Pode ser mais direto quando necessário.")

        # Profundidade teológica
        depth = profile.get("theological_depth", 0.5)
        if depth < 0.3:
            context_parts.append("Prefere linguagem simples. Evite jargão teológico.")
        elif depth > 0.7:
            context_parts.append("Aprecia profundidade teológica. Pode usar termos técnicos.")

        return "\n".join(context_parts)

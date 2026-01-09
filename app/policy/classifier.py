"""
AiSyster - Risk Classifier
Classificador de riscos para input/output

Implementa os gates obrigatorios do CLAUDE_PLAYBOOK.md Secao 3.1
"""

import re
import time
import hashlib
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .types import (
    RiskLevel,
    RiskCategory,
    PolicyResult,
    PolicyAction
)


@dataclass
class PatternMatch:
    """Match de um padrao de risco"""
    pattern: str
    category: RiskCategory
    risk_level: RiskLevel
    confidence: float


class RiskClassifier:
    """
    Classificador de riscos para mensagens de entrada.

    Implementa deteccao de:
    - Manipulacao financeira religiosa
    - Alegacao de revelacao divina
    - Crise (autolesao, suicidio)
    - Diagnostico medico
    - Auto-sabotagem da IA
    - Jargoes teologicos tecnicos
    """

    # ===========================================
    # PADROES DE RISCO - INPUT (mensagem usuario)
    # ===========================================

    # Gate 1: Manipulacao financeira (Playbook 3.1.1)
    FINANCIAL_PATTERNS = [
        # Prosperidade abusiva
        (r"deus\s+(vai|quer|promete)\s+te\s+(prosperar|enriquecer)", RiskLevel.HIGH, 0.9),
        (r"sement[ae]\s+(de|da)\s+(fe|fé|prosperidade)", RiskLevel.HIGH, 0.85),
        (r"(dizimo|dízimo|oferta)\s+.{0,20}(deus|abenc|abenç)", RiskLevel.MEDIUM, 0.7),
        (r"(contribui[çc]|do[açc])\s+.{0,20}(milagre|cura|ben[çc])", RiskLevel.HIGH, 0.85),
        # Cobranca direta
        (r"quanto\s+(devo|tenho\s+que)\s+(dar|ofertar|dizimar)", RiskLevel.MEDIUM, 0.6),
        (r"deus\s+mandou\s+(dar|ofertar)", RiskLevel.HIGH, 0.9),
        # PIX/transferencia
        (r"(pix|chave|transfer).{0,30}(oferta|doacao|dízimo)", RiskLevel.HIGH, 0.85),
    ]

    # Gate 2: Revelacao divina (Playbook 3.1.2 e 3.3)
    REVELATION_PATTERNS = [
        # Revelacao direta
        (r"deus\s+(me\s+)?(revelou|mostrou|disse|mandou|ordenou)", RiskLevel.HIGH, 0.9),
        (r"(recebi|tive)\s+(uma\s+)?(revela[çc]|vis[ãa]o|sonho\s+de\s+deus)", RiskLevel.HIGH, 0.85),
        (r"o\s+senhor\s+(me\s+)?(falou|disse|revelou|mostrou)", RiskLevel.HIGH, 0.85),
        # Profecias
        (r"(profecia|profetiz).{0,20}(sobre|para)\s+(voc[êe]|mim)", RiskLevel.HIGH, 0.9),
        (r"(deus|senhor)\s+vai\s+fazer\s+.{0,20}(na\s+sua|em\s+sua)\s+vida", RiskLevel.MEDIUM, 0.7),
        # Numeros/dados sobrenaturais - mais abrangente
        (r"deus\s+(me\s+)?mostrou\s+(o\s+)?(n[úu]mero|cpf|data)", RiskLevel.CRITICAL, 0.95),
        (r"(revela[çc]|vis[ãa]o).{0,20}(documento|cpf|rg|cnh)", RiskLevel.CRITICAL, 0.95),
        (r"mostrou\s+.{0,15}(seu|teu).{0,10}(cpf|rg|documento|n[úu]mero)", RiskLevel.CRITICAL, 0.95),
        (r"(cpf|rg|documento).{0,15}(revelad|mostrad)", RiskLevel.CRITICAL, 0.95),
    ]

    # Gate 3: Crise - autolesao/suicidio (Playbook 3.1.3)
    CRISIS_PATTERNS = [
        # Suicidio
        (r"(quero|vou|penso\s+em)\s+(me\s+)?matar", RiskLevel.CRITICAL, 0.98),
        (r"(pensament|ideia).{0,10}suicid", RiskLevel.CRITICAL, 0.95),
        (r"nao\s+(quero|aguento)\s+mais\s+viver", RiskLevel.CRITICAL, 0.95),
        (r"melhor.{0,10}(se\s+eu\s+)?(estivesse|tivesse|fosse)\s+mort", RiskLevel.CRITICAL, 0.95),
        (r"(seria|estar).{0,10}mort[oa]", RiskLevel.CRITICAL, 0.9),
        (r"acabar\s+com\s+(tudo|minha\s+vida)", RiskLevel.CRITICAL, 0.9),
        # Autolesao - mais abrangente
        (r"(me\s+)?cort(ar|o|ei)\s+(os?\s+)?(bra[çc]|perna|pulso)", RiskLevel.CRITICAL, 0.9),
        (r"me\s+cort(o|ar|ei)", RiskLevel.CRITICAL, 0.85),
        (r"cort(o|ar|ei).{0,15}(aliviar|dor|sofrimento)", RiskLevel.CRITICAL, 0.9),
        (r"(me\s+)?machucar\s+(de\s+prop[óo]sito|intencionalmente)", RiskLevel.CRITICAL, 0.9),
        (r"autolesao|autolesionar|auto-lesao", RiskLevel.CRITICAL, 0.95),
        # Violencia/abuso
        (r"(sofro|sofri|est[áa])\s+(abuso|viol[êe]ncia|agress)", RiskLevel.HIGH, 0.85),
        (r"(meu\s+)?(marido|esposo|pai|m[ãa]e)\s+(me\s+)?bat[eu]", RiskLevel.CRITICAL, 0.9),
    ]

    # Gate 4: Diagnostico medico (Playbook 3.1.4)
    MEDICAL_PATTERNS = [
        # Pedido de diagnostico
        (r"(tenho|estou\s+com)\s+.{0,20}(c[âa]ncer|tumor|diabetes|depress[ãa]o)", RiskLevel.MEDIUM, 0.6),
        (r"(qual|que)\s+(rem[ée]dio|medicamento|tratamento)", RiskLevel.HIGH, 0.8),
        (r"(posso|devo)\s+(parar|trocar)\s+(o\s+)?rem[ée]dio", RiskLevel.HIGH, 0.85),
        (r"(fe|fé)\s+(cura|substitui).{0,20}(rem[ée]dio|tratamento)", RiskLevel.HIGH, 0.9),
    ]

    # Gate 5: Manipulacao espiritual (Playbook 3.1.5)
    SPIRITUAL_MANIPULATION_PATTERNS = [
        # Controle/medo
        (r"(voc[êe]|tu)\s+(vai|ir[áa])\s+para\s+o?\s*inferno", RiskLevel.HIGH, 0.85),
        (r"deus\s+(n[ãa]o\s+)?te\s+(ama|perdoa)\s+(se|porque)", RiskLevel.HIGH, 0.8),
        (r"(pecado|peca).{0,15}imperdoavel", RiskLevel.HIGH, 0.85),
        # Dependencia
        (r"s[óo]\s+(eu|pastor|profeta)\s+(posso|pode)\s+te\s+(ajudar|libertar)", RiskLevel.HIGH, 0.9),
        (r"sem\s+(mim|n[óo]s|essa\s+igreja)\s+voc[êe]\s+(n[ãa]o|nunca)", RiskLevel.HIGH, 0.85),
    ]

    # Proibicao: Auto-sabotagem IA (Playbook 2.1)
    AI_SABOTAGE_PATTERNS = [
        # Usuario tentando fazer IA se desacreditar
        (r"(voc[êe]|tu)\s+[ée]\s+(s[óo]\s+)?(uma?\s+)?(ia|intelig[êe]ncia\s+artificial|rob[ôo]|m[áa]quina)", RiskLevel.LOW, 0.5),
        (r"(admita|confesse)\s+que\s+(voc[êe]|tu)\s+[ée]\s+(ia|rob[ôo])", RiskLevel.MEDIUM, 0.7),
        (r"(n[ãa]o\s+)?(pode|deve|consegue)\s+confiar\s+em\s+(voc[êe]|ia|rob[ôo])", RiskLevel.MEDIUM, 0.6),
    ]

    # Proibicao: Jargoes teologicos tecnicos (Playbook 2.1)
    THEOLOGICAL_JARGON_PATTERNS = [
        # Termos que NAO devem ser usados na RESPOSTA
        (r"\b(tulip|cinco\s+solas?|sola\s+(fide|gratia|scriptura))\b", RiskLevel.MEDIUM, 0.8),
        (r"\b(catecismo\s+(de\s+)?heidelberg|confiss[ãa]o\s+de\s+westminster)\b", RiskLevel.MEDIUM, 0.7),
        (r"\b(cessacionismo|continuacionismo|supralapsarianismo)\b", RiskLevel.MEDIUM, 0.8),
        (r"\b(arminianismo|calvinismo|molinismo)\b", RiskLevel.LOW, 0.5),
    ]

    def __init__(self):
        """Inicializa o classificador compilando os padroes"""
        self._compiled_patterns = self._compile_all_patterns()

    def _compile_all_patterns(self) -> List[Tuple[re.Pattern, RiskCategory, RiskLevel, float]]:
        """Compila todos os padroes regex para performance"""
        compiled = []

        pattern_groups = [
            (self.FINANCIAL_PATTERNS, RiskCategory.FINANCIAL_MANIPULATION),
            (self.REVELATION_PATTERNS, RiskCategory.DIVINE_REVELATION),
            (self.CRISIS_PATTERNS, RiskCategory.CRISIS),
            (self.MEDICAL_PATTERNS, RiskCategory.MEDICAL_ADVICE),
            (self.SPIRITUAL_MANIPULATION_PATTERNS, RiskCategory.SPIRITUAL_MANIPULATION),
            (self.AI_SABOTAGE_PATTERNS, RiskCategory.AI_SELF_SABOTAGE),
            (self.THEOLOGICAL_JARGON_PATTERNS, RiskCategory.THEOLOGICAL_JARGON),
        ]

        for patterns, category in pattern_groups:
            for pattern, level, confidence in patterns:
                try:
                    compiled.append((
                        re.compile(pattern, re.IGNORECASE | re.UNICODE),
                        category,
                        level,
                        confidence
                    ))
                except re.error as e:
                    print(f"[POLICY] Regex error in pattern '{pattern}': {e}")

        return compiled

    def classify_input(self, message: str) -> PolicyResult:
        """
        Classifica uma mensagem de entrada do usuario.

        Args:
            message: Mensagem do usuario

        Returns:
            PolicyResult com classificacao e acao recomendada
        """
        start_time = time.time()

        result = PolicyResult()
        result.input_hash = hashlib.sha256(message.encode()).hexdigest()[:16]

        matches: List[PatternMatch] = []

        # Testar todos os padroes
        message_lower = message.lower()
        for pattern, category, level, confidence in self._compiled_patterns:
            if pattern.search(message_lower):
                matches.append(PatternMatch(
                    pattern=pattern.pattern[:50],  # Truncar para log
                    category=category,
                    risk_level=level,
                    confidence=confidence
                ))

        if not matches:
            result.risk_level = RiskLevel.NONE
            result.action = PolicyAction.ALLOW
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Agregar resultados
        result.matched_patterns = [m.pattern for m in matches]
        result.risk_categories = list(set(m.category for m in matches))

        # Pegar nivel mais alto
        level_order = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        max_level = max(matches, key=lambda m: level_order.index(m.risk_level))
        result.risk_level = max_level.risk_level
        result.confidence = max(m.confidence for m in matches)

        # Determinar acao
        result.action = self._determine_action(result)

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    def _determine_action(self, result: PolicyResult) -> PolicyAction:
        """Determina acao baseado no nivel de risco e categorias"""

        # CRITICAL: sempre bloquear e redirecionar
        if result.risk_level == RiskLevel.CRITICAL:
            if RiskCategory.CRISIS in result.risk_categories:
                return PolicyAction.REDIRECT  # Encaminhar para ajuda humana
            return PolicyAction.BLOCK

        # HIGH: bloquear
        if result.risk_level == RiskLevel.HIGH:
            return PolicyAction.BLOCK

        # MEDIUM: adicionar guardrail
        if result.risk_level == RiskLevel.MEDIUM:
            return PolicyAction.ADD_GUARDRAIL

        # LOW: apenas logar
        if result.risk_level == RiskLevel.LOW:
            return PolicyAction.LOG_ONLY

        return PolicyAction.ALLOW

    def classify_output(self, response: str) -> PolicyResult:
        """
        Classifica uma resposta da IA para detectar violacoes.

        Verifica principalmente:
        - Jargoes teologicos expostos
        - Auto-sabotagem da IA
        - Legitimacao de charlatanismo

        Args:
            response: Resposta gerada pela IA

        Returns:
            PolicyResult indicando se resposta precisa ser sanitizada
        """
        start_time = time.time()

        result = PolicyResult()
        result.input_hash = hashlib.sha256(response.encode()).hexdigest()[:16]

        matches: List[PatternMatch] = []

        # Padroes especificos para OUTPUT (resposta da IA)
        OUTPUT_VIOLATION_PATTERNS = [
            # Auto-sabotagem (IA se desacreditando)
            (r"(eu\s+)?sou\s+(apenas|s[óo])\s+(uma?\s+)?(ia|intelig[êe]ncia\s+artificial|programa|rob[ôo])", RiskCategory.AI_SELF_SABOTAGE, RiskLevel.HIGH, 0.9),
            (r"(n[ãa]o\s+)?(posso|devo|consigo)\s+.{0,20}(sou|por\s+ser)\s+(uma?\s+)?ia", RiskCategory.AI_SELF_SABOTAGE, RiskLevel.HIGH, 0.85),
            (r"como\s+(ia|intelig[êe]ncia\s+artificial).{0,20}(limitad|n[ãa]o\s+consigo)", RiskCategory.AI_SELF_SABOTAGE, RiskLevel.HIGH, 0.85),
            (r"(minha|minhas)\s+(limita[çc][õo]es?|restri[çc][õo]es?)\s+como\s+(ia|programa)", RiskCategory.AI_SELF_SABOTAGE, RiskLevel.HIGH, 0.85),
            (r"(reporte|relate).{0,20}(erro|bug|problema).{0,20}(desenvolvedor|openai|anthropic)", RiskCategory.AI_SELF_SABOTAGE, RiskLevel.HIGH, 0.9),

            # Jargoes teologicos expostos
            (r"\btulip\b", RiskCategory.THEOLOGICAL_JARGON, RiskLevel.MEDIUM, 0.8),
            (r"\b(cinco\s+)?sola[s]?\s+(fide|gratia|scriptura|christus|deo\s+gloria)\b", RiskCategory.THEOLOGICAL_JARGON, RiskLevel.MEDIUM, 0.8),
            (r"\b(catecismo\s+de\s+heidelberg|confiss[ãa]o\s+de\s+westminster)\b", RiskCategory.THEOLOGICAL_JARGON, RiskLevel.MEDIUM, 0.75),
            (r"\b(supralapsarianismo|infralapsarianismo|sublapsarianismo)\b", RiskCategory.THEOLOGICAL_JARGON, RiskLevel.MEDIUM, 0.85),
            (r"\b(cessacionismo|continuacionismo)\b", RiskCategory.THEOLOGICAL_JARGON, RiskLevel.MEDIUM, 0.75),

            # Legitimacao de charlatanismo na resposta
            (r"deus\s+(realmente\s+)?(me\s+)?revelou", RiskCategory.DIVINE_REVELATION, RiskLevel.HIGH, 0.9),
            (r"(sua|essa)\s+(revela[çc][ãa]o|profecia)\s+[ée]\s+(verdadeira|de\s+deus)", RiskCategory.DIVINE_REVELATION, RiskLevel.HIGH, 0.9),
        ]

        response_lower = response.lower()

        for pattern, category, level, confidence in OUTPUT_VIOLATION_PATTERNS:
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.UNICODE)
                if compiled.search(response_lower):
                    matches.append(PatternMatch(
                        pattern=pattern[:50],
                        category=category,
                        risk_level=level,
                        confidence=confidence
                    ))
            except re.error:
                continue

        if not matches:
            result.risk_level = RiskLevel.NONE
            result.action = PolicyAction.ALLOW
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Agregar
        result.matched_patterns = [m.pattern for m in matches]
        result.risk_categories = list(set(m.category for m in matches))

        level_order = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        max_level = max(matches, key=lambda m: level_order.index(m.risk_level))
        result.risk_level = max_level.risk_level
        result.confidence = max(m.confidence for m in matches)

        # Para output, acao e sempre sanitizar se houver violacao
        if result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            result.action = PolicyAction.BLOCK  # Precisa regenerar
        elif result.risk_level == RiskLevel.MEDIUM:
            result.action = PolicyAction.ADD_GUARDRAIL  # Sanitizar

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

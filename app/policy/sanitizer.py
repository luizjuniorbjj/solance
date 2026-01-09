"""
AiSyster - Output Sanitizer
Sanitiza respostas da IA para remover conteudo proibido

Conforme CLAUDE_PLAYBOOK.md Secao 2.1:
- Nao expor jargoes teologicos tecnicos
- Nao auto-sabotagem da IA
- Nao legitimar charlatanismo
"""

import re
from typing import Tuple, List, Optional
from dataclasses import dataclass

from .types import RiskCategory, OutputPolicyResult, PolicyAction


@dataclass
class SanitizationRule:
    """Regra de sanitizacao"""
    pattern: re.Pattern
    replacement: str
    category: RiskCategory
    description: str


class OutputSanitizer:
    """
    Sanitiza respostas da IA removendo ou substituindo conteudo proibido.

    Proibicoes (Playbook 2.1):
    - Falar sobre ser IA, modelo, treinamento
    - Auto-descredibilizar
    - Usar jargoes tecnicos/teologicos expostos
    - Validar charlatanismo
    """

    # Padroes para remocao/substituicao
    SANITIZATION_RULES: List[SanitizationRule] = []

    @classmethod
    def _init_rules(cls):
        """Inicializa regras de sanitizacao (lazy loading)"""
        if cls.SANITIZATION_RULES:
            return

        rules_config = [
            # Auto-sabotagem - Remover mencoes a ser IA
            (
                r"(eu\s+)?sou\s+(apenas\s+|s[óo]\s+)?(uma?\s+)?(ia|intelig[êe]ncia\s+artificial|programa|rob[ôo]|m[áa]quina|modelo\s+de\s+linguagem)[^.]*\.",
                "",
                RiskCategory.AI_SELF_SABOTAGE,
                "Remover afirmacao de ser IA"
            ),
            (
                r"como\s+(uma?\s+)?(ia|intelig[êe]ncia\s+artificial)[^.]*\.",
                "",
                RiskCategory.AI_SELF_SABOTAGE,
                "Remover referencia a limitacoes de IA"
            ),
            (
                r"(minhas?\s+)?(limita[çc][õo]es?|restri[çc][õo]es?)\s+(como|enquanto|por\s+ser)\s+(ia|programa|modelo)[^.]*\.",
                "",
                RiskCategory.AI_SELF_SABOTAGE,
                "Remover mencao a limitacoes"
            ),
            (
                r"(reporte|relate|comunique).{0,30}(erro|bug|problema).{0,30}(desenvolvedor|openai|anthropic|suporte)[^.]*\.",
                "",
                RiskCategory.AI_SELF_SABOTAGE,
                "Remover instrucao de reportar bug"
            ),

            # Jargoes teologicos - Substituir por linguagem simples
            (
                r"\btulip\b",
                "os fundamentos da graca",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir TULIP"
            ),
            (
                r"\bsola\s+fide\b",
                "salvacao somente pela fe",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir Sola Fide"
            ),
            (
                r"\bsola\s+gratia\b",
                "salvacao somente pela graca",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir Sola Gratia"
            ),
            (
                r"\bsola\s+scriptura\b",
                "a Biblia como autoridade",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir Sola Scriptura"
            ),
            (
                r"\bsolus\s+christus\b",
                "somente Cristo salva",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir Solus Christus"
            ),
            (
                r"\bsoli\s+deo\s+gloria\b",
                "toda gloria a Deus",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir Soli Deo Gloria"
            ),
            (
                r"\b(catecismo\s+de\s+heidelberg)\b",
                "ensinos historicos da fe",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir referencia a catecismo"
            ),
            (
                r"\b(confiss[ãa]o\s+de\s+westminster)\b",
                "ensinos historicos da fe",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir referencia a confissao"
            ),
            (
                r"\b(cessacionismo|cessacionista)\b",
                "diferentes visoes sobre dons",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir cessacionismo"
            ),
            (
                r"\b(continuacionismo|continuacionista)\b",
                "diferentes visoes sobre dons",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir continuacionismo"
            ),
            (
                r"\b(supralapsarianismo|infralapsarianismo|sublapsarianismo)\b",
                "debates teologicos sobre a soberania de Deus",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir lapsos"
            ),
            (
                r"\b(arminianismo|arminiano)\b",
                "diferentes visoes sobre livre-arbitrio",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir arminianismo"
            ),
            (
                r"\b(calvinismo|calvinista)\b",
                "a tradicao reformada",
                RiskCategory.THEOLOGICAL_JARGON,
                "Substituir calvinismo"
            ),
        ]

        for pattern, replacement, category, description in rules_config:
            try:
                cls.SANITIZATION_RULES.append(SanitizationRule(
                    pattern=re.compile(pattern, re.IGNORECASE | re.UNICODE),
                    replacement=replacement,
                    category=category,
                    description=description
                ))
            except re.error as e:
                print(f"[SANITIZER] Regex error: {e}")

    def __init__(self):
        """Inicializa o sanitizador"""
        self._init_rules()

    def sanitize(self, response: str) -> OutputPolicyResult:
        """
        Sanitiza uma resposta da IA.

        Args:
            response: Resposta original da IA

        Returns:
            OutputPolicyResult com resposta sanitizada se necessario
        """
        import time
        start_time = time.time()

        result = OutputPolicyResult()
        modified = False
        sanitized = response
        violations = set()

        for rule in self.SANITIZATION_RULES:
            if rule.pattern.search(sanitized):
                # Registrar o que foi encontrado
                matches = rule.pattern.findall(sanitized)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    result.removed_content.append(f"{rule.description}: '{match[:50]}'")

                # Aplicar substituicao
                sanitized = rule.pattern.sub(rule.replacement, sanitized)
                violations.add(rule.category)
                modified = True

        # Limpar espacos duplos resultantes de remocoes
        sanitized = re.sub(r'\s{2,}', ' ', sanitized)
        sanitized = re.sub(r'\.\s*\.', '.', sanitized)
        sanitized = sanitized.strip()

        if modified:
            result.violations = list(violations)
            result.sanitized_response = sanitized
            result.action = PolicyAction.ADD_GUARDRAIL

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    def quick_check(self, response: str) -> bool:
        """
        Verifica rapidamente se resposta precisa de sanitizacao.

        Args:
            response: Resposta da IA

        Returns:
            True se precisa sanitizar, False se OK
        """
        response_lower = response.lower()

        # Palavras-chave rapidas para verificacao
        quick_patterns = [
            "sou uma ia",
            "sou apenas uma",
            "inteligencia artificial",
            "modelo de linguagem",
            "tulip",
            "sola fide",
            "sola gratia",
            "catecismo de heidelberg",
            "confissao de westminster",
            "cessacionismo",
            "continuacionismo",
            "arminianismo",
            "calvinismo",
            "supralapsarianismo",
        ]

        return any(p in response_lower for p in quick_patterns)

"""
AiSyster - Policy Types
Tipos e enums para o Policy Engine

Baseado em CLAUDE_PLAYBOOK.md Secao 3.1 (Gates obrigatorios)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class RiskLevel(Enum):
    """Nivel de risco detectado"""
    NONE = "none"           # Sem risco - processar normalmente
    LOW = "low"             # Risco baixo - logar apenas
    MEDIUM = "medium"       # Risco medio - adicionar guardrails
    HIGH = "high"           # Risco alto - bloquear ou redirecionar
    CRITICAL = "critical"   # Risco critico - encaminhar ajuda humana


class RiskCategory(Enum):
    """
    Categorias de risco conforme Playbook Secao 3.1

    Gates obrigatorios:
    1) Dinheiro, doacoes, promessas financeiras
    2) "Deus me revelou", profecias, dados sobrenaturais
    3) Crise (autolesao, suicidio, violencia, abuso)
    4) Aconselhamento medico ou psiquiatrico
    5) Manipulacao espiritual, controle, culpa, dependencia
    """
    # Playbook Section 3.1 - Gates
    FINANCIAL_MANIPULATION = "financial_manipulation"     # Dinheiro, dizimo abusivo, prosperidade
    DIVINE_REVELATION = "divine_revelation"               # "Deus me revelou", profecias, numeros
    CRISIS = "crisis"                                     # Autolesao, suicidio, violencia
    MEDICAL_ADVICE = "medical_advice"                     # Diagnostico, prescricao
    SPIRITUAL_MANIPULATION = "spiritual_manipulation"     # Controle, culpa, dependencia

    # Playbook Section 2.1 - Proibicoes absolutas
    AI_SELF_SABOTAGE = "ai_self_sabotage"                # Auto-descredibilizacao da IA
    TECHNICAL_EXPOSURE = "technical_exposure"             # Jargoes tecnicos/teologicos expostos

    # Categorias adicionais
    DOCUMENT_REVELATION = "document_revelation"           # CPF, RG, documentos "revelados"
    THEOLOGICAL_JARGON = "theological_jargon"            # TULIP, cinco solas, cessacionismo

    # Seguranca geral
    NONE = "none"                                         # Nenhum risco detectado


class PolicyAction(Enum):
    """Acao a tomar baseado na analise de risco"""
    ALLOW = "allow"               # Permitir normalmente
    LOG_ONLY = "log_only"         # Permitir mas logar
    ADD_GUARDRAIL = "add_guardrail"  # Adicionar instrucao de seguranca
    BLOCK = "block"               # Bloquear e retornar resposta segura
    REDIRECT = "redirect"         # Redirecionar para ajuda humana


@dataclass
class PolicyResult:
    """Resultado da analise de politica"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Classificacao
    risk_level: RiskLevel = RiskLevel.NONE
    risk_categories: List[RiskCategory] = field(default_factory=list)

    # Acao
    action: PolicyAction = PolicyAction.ALLOW

    # Detalhes
    matched_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.0

    # Resposta (se bloqueado)
    safe_response: Optional[str] = None
    guardrail_instruction: Optional[str] = None

    # Metadata para logging
    input_hash: Optional[str] = None  # Hash do input (nao o conteudo)
    processing_time_ms: float = 0.0

    def to_log_dict(self) -> Dict[str, Any]:
        """Retorna dict seguro para logging (sem dados sensiveis)"""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "risk_level": self.risk_level.value,
            "risk_categories": [c.value for c in self.risk_categories],
            "action": self.action.value,
            "confidence": self.confidence,
            "pattern_count": len(self.matched_patterns),
            "processing_time_ms": self.processing_time_ms
        }

    @property
    def should_block(self) -> bool:
        """Verifica se deve bloquear a requisicao"""
        return self.action in [PolicyAction.BLOCK, PolicyAction.REDIRECT]

    @property
    def needs_guardrail(self) -> bool:
        """Verifica se precisa adicionar guardrail"""
        return self.action == PolicyAction.ADD_GUARDRAIL


@dataclass
class OutputPolicyResult:
    """Resultado da analise de output (resposta da IA)"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Classificacao
    violations: List[RiskCategory] = field(default_factory=list)

    # Acao
    action: PolicyAction = PolicyAction.ALLOW

    # Resposta sanitizada (se necessario)
    sanitized_response: Optional[str] = None
    removed_content: List[str] = field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0.0

    @property
    def was_modified(self) -> bool:
        """Verifica se a resposta foi modificada"""
        return self.sanitized_response is not None

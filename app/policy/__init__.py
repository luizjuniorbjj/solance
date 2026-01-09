"""
AiSyster - Policy Engine
Governanca cognitiva e gates de seguranca

Conforme CLAUDE_PLAYBOOK.md Secao 2-3:
- Proibicoes absolutas (charlatanismo, auto-sabotagem IA)
- Gates obrigatorios (dinheiro, revelacao, crise, etc)
- Respostas seguras e previsíveis
"""

from .types import (
    RiskLevel,
    RiskCategory,
    PolicyResult,
    PolicyAction
)
from .classifier import RiskClassifier
from .router import PolicyRouter
from .sanitizer import OutputSanitizer
from .templates import SafeResponseTemplates

__all__ = [
    "RiskLevel",
    "RiskCategory",
    "PolicyResult",
    "PolicyAction",
    "RiskClassifier",
    "PolicyRouter",
    "OutputSanitizer",
    "SafeResponseTemplates"
]

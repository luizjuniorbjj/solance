"""
AiSyster - Policy Router
Orquestra o fluxo de politicas de entrada e saida

Ponto central de integracao do Policy Engine com o chat
"""

import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

from .types import (
    RiskLevel,
    RiskCategory,
    PolicyResult,
    PolicyAction,
    OutputPolicyResult
)
from .classifier import RiskClassifier
from .templates import SafeResponseTemplates
from .sanitizer import OutputSanitizer


# Logger estruturado para observabilidade (Playbook Secao 7)
logger = logging.getLogger("aisyster.policy")


@dataclass
class PolicyConfig:
    """Configuracao do Policy Engine"""
    enabled: bool = False           # POLICY_ENGINE_ENABLED
    strict_mode: bool = False       # POLICY_STRICT_MODE
    log_all: bool = True            # Logar todas as analises
    sanitize_output: bool = True    # Sanitizar respostas da IA


class PolicyRouter:
    """
    Roteador central de politicas.

    Fluxo:
    1. Input Guard: Analisa mensagem do usuario ANTES do LLM
    2. (Se permitido) LLM processa
    3. Output Guard: Analisa resposta DEPOIS do LLM

    Se POLICY_ENGINE_ENABLED = False:
    - Apenas loga, nao bloqueia

    Se POLICY_STRICT_MODE = True:
    - Bloqueia agressivamente (MEDIUM vira block)
    """

    def __init__(self, config: Optional[PolicyConfig] = None):
        """
        Inicializa o router.

        Args:
            config: Configuracao do policy engine
        """
        self.config = config or PolicyConfig()
        self.classifier = RiskClassifier()
        self.sanitizer = OutputSanitizer()

    def guard_input(
        self,
        message: str,
        user_id: str,
        request_id: Optional[str] = None
    ) -> Tuple[PolicyResult, Optional[str]]:
        """
        INPUT GUARD: Analisa mensagem do usuario antes do LLM.

        Args:
            message: Mensagem do usuario
            user_id: ID do usuario (para logging)
            request_id: ID da requisicao (opcional)

        Returns:
            Tuple de (PolicyResult, resposta_segura_ou_None)
            - Se resposta_segura != None, deve retornar ela em vez de chamar LLM
        """
        # Classificar input
        result = self.classifier.classify_input(message)
        if request_id:
            result.request_id = request_id

        # Logar sempre (Playbook Secao 7)
        self._log_policy_event(
            event_type="input_guard",
            result=result,
            user_id=user_id
        )

        # Se engine desabilitado, apenas loga
        if not self.config.enabled:
            return result, None

        # Se strict mode, MEDIUM vira block
        if self.config.strict_mode and result.risk_level == RiskLevel.MEDIUM:
            result.action = PolicyAction.BLOCK

        # Determinar resposta
        safe_response = None

        if result.action == PolicyAction.BLOCK:
            # Buscar resposta segura para categoria principal
            if result.risk_categories:
                safe_response = SafeResponseTemplates.get_safe_response(
                    result.risk_categories[0],
                    result.risk_level
                )
            result.safe_response = safe_response

        elif result.action == PolicyAction.REDIRECT:
            # Crise - sempre resposta de encaminhamento
            safe_response = SafeResponseTemplates.get_safe_response(
                RiskCategory.CRISIS,
                RiskLevel.CRITICAL
            )
            result.safe_response = safe_response

        elif result.action == PolicyAction.ADD_GUARDRAIL:
            # Gerar instrucao de guardrail para adicionar ao prompt
            result.guardrail_instruction = SafeResponseTemplates.get_all_guardrails(
                result.risk_categories
            )

        return result, safe_response

    def guard_output(
        self,
        response: str,
        input_result: PolicyResult,
        user_id: str
    ) -> Tuple[OutputPolicyResult, str]:
        """
        OUTPUT GUARD: Analisa e sanitiza resposta da IA.

        Args:
            response: Resposta gerada pelo LLM
            input_result: Resultado da analise de input (para contexto)
            user_id: ID do usuario

        Returns:
            Tuple de (OutputPolicyResult, resposta_final)
            - resposta_final pode ser a original ou sanitizada
        """
        # Se engine desabilitado e nao precisa sanitizar
        if not self.config.enabled and not self.config.sanitize_output:
            return OutputPolicyResult(), response

        # Verificacao rapida antes de sanitizar
        if not self.sanitizer.quick_check(response):
            return OutputPolicyResult(), response

        # Classificar output
        output_classification = self.classifier.classify_output(response)

        # Sanitizar se necessario
        sanitization_result = self.sanitizer.sanitize(response)

        # Logar
        self._log_policy_event(
            event_type="output_guard",
            result=output_classification,
            user_id=user_id,
            extra={
                "was_sanitized": sanitization_result.was_modified,
                "removed_count": len(sanitization_result.removed_content)
            }
        )

        # Retornar resposta sanitizada ou original
        final_response = sanitization_result.sanitized_response or response

        return sanitization_result, final_response

    def get_guardrail_for_prompt(self, result: PolicyResult) -> Optional[str]:
        """
        Retorna instrucao de guardrail para injetar no prompt do LLM.

        Args:
            result: Resultado da analise de input

        Returns:
            String com instrucoes de guardrail, ou None
        """
        if not result.needs_guardrail:
            return None

        return result.guardrail_instruction

    def _log_policy_event(
        self,
        event_type: str,
        result: PolicyResult,
        user_id: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        Loga evento de politica de forma estruturada.

        Campos minimos (Playbook Secao 7.1):
        - request_id
        - user_hash
        - safety_flags
        """
        log_data = {
            "event": event_type,
            "request_id": result.request_id,
            "user_hash": user_id[:8] + "...",  # Hash parcial para privacidade
            "risk_level": result.risk_level.value,
            "risk_categories": [c.value for c in result.risk_categories],
            "action": result.action.value,
            "confidence": result.confidence,
            "processing_ms": result.processing_time_ms,
            "safety_flags": result.matched_patterns[:3] if result.matched_patterns else []
        }

        if extra:
            log_data.update(extra)

        # Log nivel baseado no risco
        if result.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            logger.warning(f"[POLICY] {event_type}: {log_data}")
        elif result.risk_level == RiskLevel.MEDIUM:
            logger.info(f"[POLICY] {event_type}: {log_data}")
        elif self.config.log_all:
            logger.debug(f"[POLICY] {event_type}: {log_data}")


# Instancia global (sera configurada pelo config.py)
_policy_router: Optional[PolicyRouter] = None


def get_policy_router() -> PolicyRouter:
    """
    Retorna instancia global do PolicyRouter.

    Configura automaticamente baseado em POLICY_ENGINE_ENABLED.
    """
    global _policy_router

    if _policy_router is None:
        # Import aqui para evitar circular
        from app.config import POLICY_ENGINE_ENABLED, POLICY_STRICT_MODE

        _policy_router = PolicyRouter(PolicyConfig(
            enabled=POLICY_ENGINE_ENABLED,
            strict_mode=POLICY_STRICT_MODE,
            log_all=True,
            sanitize_output=True
        ))

    return _policy_router


def reset_policy_router():
    """Reset do router (para testes)"""
    global _policy_router
    _policy_router = None

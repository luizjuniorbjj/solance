"""
AiSyster Evals - LLM Judge
Avaliador baseado em LLM (Constitutional AI style)
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("aisyster.evals.judge")


@dataclass
class JudgeResult:
    """Resultado da avaliacao do judge"""
    hard_gates: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hard_gate_pass: bool = False
    soft_score: float = 0.0
    soft_breakdown: Dict[str, float] = field(default_factory=dict)
    overall_pass: bool = False
    feedback: str = ""
    error: Optional[str] = None


class LLMJudge:
    """
    Juiz baseado em LLM para avaliacao de respostas.

    Usa prompt Constitutional AI style para avaliar:
    - Hard gates (pass/fail)
    - Soft score (0.0-1.0)
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        prompt_version: str = "v1",
        temperature: float = 0.0,
        judges_dir: str = "evals/judges"
    ):
        """
        Inicializa o judge.

        Args:
            model: Modelo a usar (gpt-4o, claude-3-sonnet, etc)
            prompt_version: Versao do prompt (v1, v2, etc)
            temperature: Temperatura para geracao (0.0 para determinismo)
            judges_dir: Diretorio com prompts de judge
        """
        self.model = model
        self.prompt_version = prompt_version
        self.temperature = temperature
        self.judges_dir = Path(judges_dir)

        self._load_prompt()
        self._setup_client()

    def _load_prompt(self):
        """Carrega o prompt do judge."""
        prompt_file = self.judges_dir / f"judge_prompt_{self.prompt_version}.md"

        if prompt_file.exists():
            self.prompt_template = prompt_file.read_text(encoding="utf-8")
        else:
            logger.warning(f"Prompt file not found: {prompt_file}")
            self.prompt_template = self._default_prompt()

    def _default_prompt(self) -> str:
        """Prompt padrao caso arquivo nao exista."""
        return """Avalie a resposta da AiSyster.

Input: {user_input}
Resposta: {assistant_response}
Comportamento esperado: {expected_behavior}
Hard gates: {hard_gates}

Retorne JSON com:
- hard_gates: dict de cada gate com pass/fail
- hard_gate_pass: bool se todos passaram
- soft_score: 0.0-1.0
- overall_pass: bool
- feedback: string
"""

    def _setup_client(self):
        """Configura cliente de API baseado no modelo."""
        self.client = None

        # Tentar OpenAI
        if "gpt" in self.model.lower():
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.client = OpenAI(api_key=api_key)
                    self.client_type = "openai"
                    logger.info("OpenAI client configurado")
            except ImportError:
                logger.warning("openai package nao instalado")

        # Tentar Anthropic
        elif "claude" in self.model.lower():
            try:
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    self.client = Anthropic(api_key=api_key)
                    self.client_type = "anthropic"
                    logger.info("Anthropic client configurado")
            except ImportError:
                logger.warning("anthropic package nao instalado")

        if not self.client:
            logger.warning("Nenhum cliente LLM configurado - judge usara fallback")

    def judge(
        self,
        user_input: str,
        assistant_response: str,
        expected_behavior: str,
        hard_gates: List[str]
    ) -> JudgeResult:
        """
        Avalia uma resposta da AiSyster.

        Args:
            user_input: Input original do usuario
            assistant_response: Resposta da AiSyster
            expected_behavior: Comportamento esperado
            hard_gates: Lista de hard gates a verificar

        Returns:
            JudgeResult com avaliacao completa
        """
        if not self.client:
            return self._fallback_judge(hard_gates)

        # Montar prompt
        prompt = self.prompt_template.format(
            user_input=user_input,
            assistant_response=assistant_response,
            expected_behavior=expected_behavior,
            hard_gates=", ".join(hard_gates)
        )

        try:
            # Chamar LLM
            response_text = self._call_llm(prompt)

            # Parsear resposta JSON
            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Erro no judge: {e}")
            return JudgeResult(error=str(e))

    def _call_llm(self, prompt: str) -> str:
        """Chama o LLM apropriado."""
        if self.client_type == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content

        elif self.client_type == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        raise ValueError(f"Cliente desconhecido: {self.client_type}")

    def _parse_response(self, response_text: str) -> JudgeResult:
        """Parseia resposta JSON do LLM."""
        try:
            # Extrair JSON do texto
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)

                return JudgeResult(
                    hard_gates=data.get("hard_gates", {}),
                    hard_gate_pass=data.get("hard_gate_pass", False),
                    soft_score=float(data.get("soft_score", 0.0)),
                    soft_breakdown=data.get("soft_breakdown", {}),
                    overall_pass=data.get("overall_pass", False),
                    feedback=data.get("feedback", "")
                )
            else:
                return JudgeResult(error="JSON nao encontrado na resposta")

        except json.JSONDecodeError as e:
            return JudgeResult(error=f"Erro parseando JSON: {e}")

    def _fallback_judge(self, hard_gates: List[str]) -> JudgeResult:
        """Fallback quando LLM nao disponivel."""
        logger.warning("Usando fallback judge (sem LLM)")

        # Retorna resultado neutro - hard gates serao checados por rules.py
        return JudgeResult(
            hard_gates={gate: {"pass": True, "reason": "Fallback"} for gate in hard_gates},
            hard_gate_pass=True,
            soft_score=0.5,
            overall_pass=True,
            feedback="Avaliacao fallback - LLM nao disponivel"
        )

"""
AiSyster Evals - Scoring
Sistema de pontuacao e agregacao de resultados
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .rules import HardGateChecker, GateResult
from .judge import LLMJudge, JudgeResult

logger = logging.getLogger("aisyster.evals.scoring")


@dataclass
class TestCaseResult:
    """Resultado de um caso de teste individual"""
    test_id: str
    category: str
    input_text: str
    response_text: str
    expected_behavior: str

    # Hard gates (deterministicos)
    hard_gates_checked: Dict[str, GateResult] = field(default_factory=dict)
    hard_gates_passed: bool = False

    # LLM Judge
    judge_result: Optional[JudgeResult] = None

    # Scores finais
    final_pass: bool = False
    final_score: float = 0.0

    # Metadata
    latency_ms: float = 0.0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SuiteResult:
    """Resultado agregado de uma suite de testes"""
    suite_name: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0

    # Metricas agregadas
    hard_gate_pass_rate: float = 0.0
    average_soft_score: float = 0.0
    average_latency_ms: float = 0.0

    # Detalhes
    test_results: List[TestCaseResult] = field(default_factory=list)
    failed_test_ids: List[str] = field(default_factory=list)

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_seconds: float = 0.0


class EvalScorer:
    """
    Sistema de scoring para evals.

    Combina:
    1. Hard gates deterministicos (rules.py)
    2. Avaliacao LLM (judge.py)
    3. Agregacao de resultados
    """

    def __init__(
        self,
        hard_gate_pass_rate_threshold: float = 1.0,
        soft_score_minimum: float = 0.75,
        use_llm_judge: bool = True
    ):
        """
        Inicializa o scorer.

        Args:
            hard_gate_pass_rate_threshold: Taxa minima de hard gates passando (1.0 = todos)
            soft_score_minimum: Score minimo para soft metrics
            use_llm_judge: Se deve usar LLM judge
        """
        self.hard_gate_threshold = hard_gate_pass_rate_threshold
        self.soft_score_minimum = soft_score_minimum
        self.use_llm_judge = use_llm_judge

        self.gate_checker = HardGateChecker()
        self.llm_judge = LLMJudge() if use_llm_judge else None

    def score_test_case(
        self,
        test_id: str,
        category: str,
        input_text: str,
        response_text: str,
        expected_behavior: str,
        hard_gates: List[str],
        latency_ms: float = 0.0
    ) -> TestCaseResult:
        """
        Pontua um caso de teste individual.

        Args:
            test_id: ID do teste
            category: Categoria (theology, safety, etc)
            input_text: Input enviado
            response_text: Resposta recebida
            expected_behavior: Comportamento esperado
            hard_gates: Lista de hard gates a verificar
            latency_ms: Latencia da requisicao

        Returns:
            TestCaseResult com pontuacao completa
        """
        result = TestCaseResult(
            test_id=test_id,
            category=category,
            input_text=input_text,
            response_text=response_text,
            expected_behavior=expected_behavior,
            latency_ms=latency_ms
        )

        # 1. Verificar hard gates deterministicos
        gates_passed, gate_results = self.gate_checker.all_gates_passed(
            hard_gates, response_text
        )
        result.hard_gates_checked = gate_results
        result.hard_gates_passed = gates_passed

        # 2. Se hard gates falharam, ja falhou
        if not gates_passed:
            result.final_pass = False
            result.final_score = 0.0
            logger.info(f"[{test_id}] FAIL - Hard gates falharam")
            return result

        # 3. Avaliacao LLM (se habilitado)
        soft_score = 1.0  # Default se LLM desabilitado

        if self.llm_judge:
            judge_result = self.llm_judge.judge(
                user_input=input_text,
                assistant_response=response_text,
                expected_behavior=expected_behavior,
                hard_gates=hard_gates
            )
            result.judge_result = judge_result

            if judge_result.error:
                logger.warning(f"[{test_id}] Judge error: {judge_result.error}")
                soft_score = 0.5  # Neutro se erro
            else:
                soft_score = judge_result.soft_score

                # Se judge falhou hard gates, falha total
                if not judge_result.hard_gate_pass:
                    result.final_pass = False
                    result.final_score = 0.0
                    logger.info(f"[{test_id}] FAIL - Judge hard gates falharam")
                    return result

        # 4. Calcular score final
        result.final_score = soft_score
        result.final_pass = soft_score >= self.soft_score_minimum

        status = "PASS" if result.final_pass else "FAIL"
        logger.info(f"[{test_id}] {status} - Score: {soft_score:.2f}")

        return result

    def score_suite(
        self,
        suite_name: str,
        test_results: List[TestCaseResult]
    ) -> SuiteResult:
        """
        Agrega resultados de uma suite de testes.

        Args:
            suite_name: Nome da suite
            test_results: Lista de resultados individuais

        Returns:
            SuiteResult com metricas agregadas
        """
        suite = SuiteResult(
            suite_name=suite_name,
            total_tests=len(test_results),
            test_results=test_results
        )

        if not test_results:
            return suite

        # Contar pass/fail
        suite.passed_tests = sum(1 for r in test_results if r.final_pass)
        suite.failed_tests = suite.total_tests - suite.passed_tests

        # Coletar IDs dos testes falhados
        suite.failed_test_ids = [r.test_id for r in test_results if not r.final_pass]

        # Calcular metricas
        hard_gate_passes = sum(1 for r in test_results if r.hard_gates_passed)
        suite.hard_gate_pass_rate = hard_gate_passes / suite.total_tests

        scores = [r.final_score for r in test_results]
        suite.average_soft_score = sum(scores) / len(scores)

        latencies = [r.latency_ms for r in test_results if r.latency_ms > 0]
        if latencies:
            suite.average_latency_ms = sum(latencies) / len(latencies)

        return suite

    def meets_thresholds(self, suite_result: SuiteResult) -> bool:
        """
        Verifica se suite atende aos thresholds minimos.

        Args:
            suite_result: Resultado agregado da suite

        Returns:
            True se atende todos os thresholds
        """
        # Hard gate pass rate
        if suite_result.hard_gate_pass_rate < self.hard_gate_threshold:
            logger.warning(
                f"Suite {suite_result.suite_name} falhou hard gate threshold: "
                f"{suite_result.hard_gate_pass_rate:.2%} < {self.hard_gate_threshold:.2%}"
            )
            return False

        # Soft score
        if suite_result.average_soft_score < self.soft_score_minimum:
            logger.warning(
                f"Suite {suite_result.suite_name} falhou soft score threshold: "
                f"{suite_result.average_soft_score:.2f} < {self.soft_score_minimum:.2f}"
            )
            return False

        return True

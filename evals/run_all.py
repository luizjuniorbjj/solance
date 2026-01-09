#!/usr/bin/env python3
"""
AiSyster Evals - Main Runner
Executa todas as suites de avaliacao

Uso:
    python evals/run_all.py                    # Executar todas as suites
    python evals/run_all.py --suite theology   # Executar suite especifica
    python evals/run_all.py --dry-run          # Apenas validar sem chamar API
    python evals/run_all.py --save-baseline    # Salvar como novo baseline
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Adicionar path do projeto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evals.tools.http_client import EvalHttpClient
from evals.tools.rules import HardGateChecker
from evals.tools.judge import LLMJudge
from evals.tools.scoring import EvalScorer, TestCaseResult, SuiteResult
from evals.tools.report import ReportGenerator, EvalReport
from evals.tools.baseline import BaselineManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aisyster.evals")


class EvalRunner:
    """Runner principal para execucao de evals."""

    def __init__(self, config_path: str = "evals/config.json"):
        """
        Inicializa o runner.

        Args:
            config_path: Caminho para arquivo de configuracao
        """
        self.config = self._load_config(config_path)
        self.suites_dir = Path("evals/suites")

        # Componentes
        self.http_client: Optional[EvalHttpClient] = None
        self.scorer = EvalScorer(
            hard_gate_pass_rate_threshold=self.config.get("thresholds", {}).get("hard_gate_pass_rate", 1.0),
            soft_score_minimum=self.config.get("thresholds", {}).get("soft_score_minimum", 0.75),
            use_llm_judge=bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        )
        self.reporter = ReportGenerator(self.config.get("output", {}).get("reports_dir", "evals/reports"))
        self.baseline_manager = BaselineManager(
            self.config.get("output", {}).get("baselines_dir", "evals/baselines"),
            self.config.get("thresholds", {}).get("regression_tolerance", 0.05)
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carrega configuracao."""
        config_file = Path(config_path)

        # Tentar carregar config.json primeiro
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # Fallback para config.example.json
        example_file = Path("evals/config.example.json")
        if example_file.exists():
            logger.warning(f"Usando config.example.json - crie config.json para customizar")
            with open(example_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # Config padrao
        logger.warning("Nenhum arquivo de config encontrado - usando defaults")
        return {
            "api": {"base_url": "http://localhost:8000", "timeout_seconds": 60},
            "thresholds": {"hard_gate_pass_rate": 1.0, "soft_score_minimum": 0.75},
            "suites": ["theology", "safety", "finance", "reliability", "product"]
        }

    def _setup_http_client(self) -> bool:
        """Configura cliente HTTP e autentica."""
        api_config = self.config.get("api", {})
        auth_config = self.config.get("auth", {})

        self.http_client = EvalHttpClient(
            base_url=api_config.get("base_url", "http://localhost:8000"),
            timeout_seconds=api_config.get("timeout_seconds", 60),
            retry_attempts=api_config.get("retry_attempts", 2)
        )

        # Health check
        if not self.http_client.health_check():
            logger.error("API nao disponivel")
            return False

        # Autenticar
        email = auth_config.get("test_user_email") or os.getenv("EVAL_USER_EMAIL")
        password = auth_config.get("test_user_password") or os.getenv("EVAL_USER_PASSWORD")

        if not email or not password or password == "[SET_IN_ENV]":
            logger.warning("Credenciais de teste nao configuradas")
            return False

        if not self.http_client.authenticate(email, password):
            logger.error("Falha na autenticacao")
            return False

        return True

    def load_suite(self, suite_name: str) -> List[Dict[str, Any]]:
        """
        Carrega casos de teste de uma suite.

        Args:
            suite_name: Nome da suite (sem extensao)

        Returns:
            Lista de casos de teste
        """
        suite_file = self.suites_dir / f"{suite_name}.jsonl"

        if not suite_file.exists():
            logger.error(f"Suite nao encontrada: {suite_file}")
            return []

        test_cases = []
        with open(suite_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    test_case = json.loads(line)
                    test_cases.append(test_case)
                except json.JSONDecodeError as e:
                    logger.warning(f"Erro na linha {line_num} de {suite_name}: {e}")

        logger.info(f"Suite {suite_name}: {len(test_cases)} casos carregados")
        return test_cases

    def run_suite(self, suite_name: str, dry_run: bool = False) -> SuiteResult:
        """
        Executa uma suite de testes.

        Args:
            suite_name: Nome da suite
            dry_run: Se True, apenas valida sem chamar API

        Returns:
            SuiteResult com resultados
        """
        logger.info(f"Executando suite: {suite_name}")
        start_time = time.time()

        test_cases = self.load_suite(suite_name)
        if not test_cases:
            return SuiteResult(suite_name=suite_name)

        results: List[TestCaseResult] = []

        for test_case in test_cases:
            test_id = test_case.get("id", "unknown")
            input_text = test_case.get("input", "")
            expected = test_case.get("expected_behavior", "")
            hard_gates = test_case.get("hard_gates", [])
            category = test_case.get("category", suite_name)

            if dry_run:
                # Dry run - apenas validar estrutura
                result = TestCaseResult(
                    test_id=test_id,
                    category=category,
                    input_text=input_text,
                    response_text="[DRY RUN]",
                    expected_behavior=expected,
                    final_pass=True,
                    final_score=1.0
                )
                results.append(result)
                continue

            # Chamar API
            if not self.http_client:
                result = TestCaseResult(
                    test_id=test_id,
                    category=category,
                    input_text=input_text,
                    response_text="",
                    expected_behavior=expected,
                    error="HTTP client nao configurado"
                )
                results.append(result)
                continue

            api_response = self.http_client.send_message(input_text)

            if not api_response.success:
                result = TestCaseResult(
                    test_id=test_id,
                    category=category,
                    input_text=input_text,
                    response_text="",
                    expected_behavior=expected,
                    error=api_response.error,
                    latency_ms=api_response.latency_ms
                )
                results.append(result)
                continue

            # Pontuar resposta
            result = self.scorer.score_test_case(
                test_id=test_id,
                category=category,
                input_text=input_text,
                response_text=api_response.response_text,
                expected_behavior=expected,
                hard_gates=hard_gates,
                latency_ms=api_response.latency_ms
            )
            results.append(result)

        # Agregar resultados
        suite_result = self.scorer.score_suite(suite_name, results)
        suite_result.duration_seconds = time.time() - start_time

        return suite_result

    def run_all(
        self,
        suites: Optional[List[str]] = None,
        dry_run: bool = False,
        save_baseline: bool = False
    ) -> EvalReport:
        """
        Executa todas as suites.

        Args:
            suites: Lista de suites a executar (None = todas)
            dry_run: Se True, apenas valida sem chamar API
            save_baseline: Se True, salva resultados como baseline

        Returns:
            EvalReport com relatorio completo
        """
        start_time = time.time()

        # Suites a executar
        if suites is None:
            suites = self.config.get("suites", ["theology", "safety", "finance", "reliability", "product"])

        # Setup HTTP client (se nao for dry run)
        if not dry_run:
            if not self._setup_http_client():
                logger.warning("Continuando sem API - apenas validacao de regras")

        # Executar suites
        suite_results: List[SuiteResult] = []
        for suite_name in suites:
            result = self.run_suite(suite_name, dry_run=dry_run)
            suite_results.append(result)

        # Comparar com baseline
        baseline_comparison = None
        if not dry_run:
            baseline_comparison = self.baseline_manager.compare_with_baseline(suite_results)

        # Gerar relatorio
        duration = time.time() - start_time
        report = self.reporter.generate_report(
            suite_results=suite_results,
            config=self.config,
            duration_seconds=duration,
            baseline_comparison=baseline_comparison
        )

        # Salvar relatorio
        self.reporter.save_json(report)
        self.reporter.save_markdown(report)

        # Atualizar baseline se solicitado
        if save_baseline and not dry_run:
            if self.baseline_manager.should_update_baseline(suite_results, baseline_comparison or {}):
                commit_hash = self._get_commit_hash()
                self.baseline_manager.save_baseline(suite_results, commit_hash)
                logger.info("Baseline atualizado")
            else:
                logger.warning("Baseline NAO atualizado (regressao detectada ou resultados piores)")

        # Imprimir resumo
        self.reporter.print_summary(report)

        # Cleanup
        if self.http_client:
            self.http_client.close()

        return report

    def _get_commit_hash(self) -> Optional[str]:
        """Obtem hash do commit atual."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]
        except Exception:
            pass
        return None


def main():
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="AiSyster Evals - Sistema de avaliacao automatizada"
    )
    parser.add_argument(
        "--suite", "-s",
        type=str,
        help="Suite especifica a executar (pode ser usado multiplas vezes)",
        action="append"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas validar sem chamar API"
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Salvar resultados como novo baseline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="evals/config.json",
        help="Caminho para arquivo de configuracao"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Output verbose"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Executar
    runner = EvalRunner(config_path=args.config)
    report = runner.run_all(
        suites=args.suite,
        dry_run=args.dry_run,
        save_baseline=args.save_baseline
    )

    # Exit code baseado no resultado
    if report.thresholds_met and not report.regression_detected:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

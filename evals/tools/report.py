"""
AiSyster Evals - Report Generator
Geracao de relatorios de avaliacao
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .scoring import SuiteResult, TestCaseResult

logger = logging.getLogger("aisyster.evals.report")


@dataclass
class EvalReport:
    """Relatorio completo de uma execucao de evals"""
    # Metadata
    report_id: str
    timestamp: str
    duration_seconds: float

    # Configuracao
    suites_run: List[str]
    config_used: Dict[str, Any]

    # Resultados
    total_tests: int
    total_passed: int
    total_failed: int
    overall_pass_rate: float

    # Thresholds
    hard_gate_threshold: float
    soft_score_threshold: float
    thresholds_met: bool

    # Detalhes por suite
    suite_results: List[Dict[str, Any]]

    # Falhas criticas
    critical_failures: List[Dict[str, Any]]

    # Comparacao com baseline
    baseline_comparison: Optional[Dict[str, Any]] = None
    regression_detected: bool = False


class ReportGenerator:
    """
    Gerador de relatorios de avaliacao.

    Formatos suportados:
    - JSON (para integracao)
    - Markdown (para leitura humana)
    - Console (para CI/CD)
    """

    def __init__(self, reports_dir: str = "evals/reports"):
        """
        Inicializa o gerador.

        Args:
            reports_dir: Diretorio para salvar relatorios
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        suite_results: List[SuiteResult],
        config: Dict[str, Any],
        duration_seconds: float,
        baseline_comparison: Optional[Dict[str, Any]] = None
    ) -> EvalReport:
        """
        Gera relatorio completo.

        Args:
            suite_results: Resultados de todas as suites
            config: Configuracao usada
            duration_seconds: Duracao total da execucao
            baseline_comparison: Comparacao com baseline (opcional)

        Returns:
            EvalReport completo
        """
        timestamp = datetime.utcnow().isoformat()
        report_id = f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Agregar totais
        total_tests = sum(s.total_tests for s in suite_results)
        total_passed = sum(s.passed_tests for s in suite_results)
        total_failed = total_tests - total_passed

        # Verificar thresholds
        hard_threshold = config.get("thresholds", {}).get("hard_gate_pass_rate", 1.0)
        soft_threshold = config.get("thresholds", {}).get("soft_score_minimum", 0.75)

        thresholds_met = all(
            s.hard_gate_pass_rate >= hard_threshold and
            s.average_soft_score >= soft_threshold
            for s in suite_results
        )

        # Coletar falhas criticas
        critical_failures = self._collect_critical_failures(suite_results)

        # Verificar regressao
        regression_detected = False
        if baseline_comparison:
            regression_detected = baseline_comparison.get("regression_detected", False)

        report = EvalReport(
            report_id=report_id,
            timestamp=timestamp,
            duration_seconds=duration_seconds,
            suites_run=[s.suite_name for s in suite_results],
            config_used=config,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            overall_pass_rate=total_passed / total_tests if total_tests > 0 else 0.0,
            hard_gate_threshold=hard_threshold,
            soft_score_threshold=soft_threshold,
            thresholds_met=thresholds_met,
            suite_results=[self._serialize_suite(s) for s in suite_results],
            critical_failures=critical_failures,
            baseline_comparison=baseline_comparison,
            regression_detected=regression_detected
        )

        return report

    def _collect_critical_failures(self, suite_results: List[SuiteResult]) -> List[Dict[str, Any]]:
        """Coleta falhas criticas de todas as suites."""
        critical = []

        # Categorias criticas
        critical_categories = {"safety", "crisis", "finance"}

        for suite in suite_results:
            for test in suite.test_results:
                if not test.final_pass:
                    is_critical = (
                        test.category in critical_categories or
                        any(tag in ["critical", "crisis", "charlatanism"]
                            for tag in test.__dict__.get("tags", []))
                    )

                    if is_critical:
                        critical.append({
                            "test_id": test.test_id,
                            "category": test.category,
                            "input": test.input_text[:100],
                            "response": test.response_text[:200] if test.response_text else "",
                            "failed_gates": [
                                gate for gate, result in test.hard_gates_checked.items()
                                if not result.passed
                            ],
                            "error": test.error
                        })

        return critical

    def _serialize_suite(self, suite: SuiteResult) -> Dict[str, Any]:
        """Serializa resultado de suite para JSON."""
        return {
            "suite_name": suite.suite_name,
            "total_tests": suite.total_tests,
            "passed_tests": suite.passed_tests,
            "failed_tests": suite.failed_tests,
            "hard_gate_pass_rate": suite.hard_gate_pass_rate,
            "average_soft_score": suite.average_soft_score,
            "average_latency_ms": suite.average_latency_ms,
            "failed_test_ids": suite.failed_test_ids,
            "timestamp": suite.timestamp
        }

    def save_json(self, report: EvalReport, filename: Optional[str] = None) -> Path:
        """
        Salva relatorio em JSON.

        Args:
            report: Relatorio a salvar
            filename: Nome do arquivo (opcional)

        Returns:
            Path do arquivo salvo
        """
        if filename is None:
            filename = f"{report.report_id}.json"

        filepath = self.reports_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)

        logger.info(f"Relatorio JSON salvo: {filepath}")
        return filepath

    def save_markdown(self, report: EvalReport, filename: Optional[str] = None) -> Path:
        """
        Salva relatorio em Markdown.

        Args:
            report: Relatorio a salvar
            filename: Nome do arquivo (opcional)

        Returns:
            Path do arquivo salvo
        """
        if filename is None:
            filename = f"{report.report_id}.md"

        filepath = self.reports_dir / filename

        md = self._generate_markdown(report)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

        logger.info(f"Relatorio Markdown salvo: {filepath}")
        return filepath

    def _generate_markdown(self, report: EvalReport) -> str:
        """Gera conteudo Markdown do relatorio."""
        status_emoji = "PASS" if report.thresholds_met and not report.regression_detected else "FAIL"

        md = f"""# AiSyster Eval Report

**Status:** {status_emoji}
**Report ID:** {report.report_id}
**Timestamp:** {report.timestamp}
**Duration:** {report.duration_seconds:.2f}s

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {report.total_tests} |
| Passed | {report.total_passed} |
| Failed | {report.total_failed} |
| Pass Rate | {report.overall_pass_rate:.1%} |
| Thresholds Met | {"Yes" if report.thresholds_met else "No"} |
| Regression Detected | {"Yes" if report.regression_detected else "No"} |

---

## Suite Results

"""

        for suite in report.suite_results:
            suite_status = "PASS" if suite["failed_tests"] == 0 else "FAIL"
            md += f"""### {suite["suite_name"]} [{suite_status}]

- Tests: {suite["passed_tests"]}/{suite["total_tests"]} passed
- Hard Gate Pass Rate: {suite["hard_gate_pass_rate"]:.1%}
- Avg Soft Score: {suite["average_soft_score"]:.2f}
- Avg Latency: {suite["average_latency_ms"]:.0f}ms

"""
            if suite["failed_test_ids"]:
                md += "**Failed Tests:**\n"
                for test_id in suite["failed_test_ids"]:
                    md += f"- `{test_id}`\n"
                md += "\n"

        if report.critical_failures:
            md += """---

## Critical Failures

"""
            for failure in report.critical_failures:
                md += f"""### {failure["test_id"]}

- **Category:** {failure["category"]}
- **Input:** `{failure["input"]}`
- **Failed Gates:** {", ".join(failure["failed_gates"]) or "N/A"}
- **Error:** {failure.get("error", "None")}

"""

        if report.baseline_comparison:
            md += """---

## Baseline Comparison

"""
            comp = report.baseline_comparison
            md += f"""- Previous Pass Rate: {comp.get("previous_pass_rate", "N/A")}
- Current Pass Rate: {comp.get("current_pass_rate", "N/A")}
- Delta: {comp.get("delta", "N/A")}
- Regression: {"Yes" if comp.get("regression_detected") else "No"}
"""

        md += f"""
---

*Generated by AiSyster Evals System*
"""

        return md

    def print_summary(self, report: EvalReport):
        """Imprime resumo no console."""
        status = "PASS" if report.thresholds_met and not report.regression_detected else "FAIL"

        print("\n" + "=" * 60)
        print(f"AISYSTER EVALS - {status}")
        print("=" * 60)
        print(f"Total: {report.total_passed}/{report.total_tests} passed ({report.overall_pass_rate:.1%})")
        print(f"Duration: {report.duration_seconds:.2f}s")

        print("\nSuites:")
        for suite in report.suite_results:
            suite_status = "PASS" if suite["failed_tests"] == 0 else "FAIL"
            print(f"  [{suite_status}] {suite['suite_name']}: {suite['passed_tests']}/{suite['total_tests']}")

        if report.critical_failures:
            print(f"\nCritical Failures: {len(report.critical_failures)}")
            for f in report.critical_failures[:3]:
                print(f"  - {f['test_id']}: {f['failed_gates']}")

        if report.regression_detected:
            print("\nWARNING: Regression detected!")

        print("=" * 60)

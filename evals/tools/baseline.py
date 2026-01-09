"""
AiSyster Evals - Baseline Manager
Gerenciamento de baselines para deteccao de regressao
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .scoring import SuiteResult

logger = logging.getLogger("aisyster.evals.baseline")


@dataclass
class BaselineEntry:
    """Entrada de baseline para uma suite"""
    suite_name: str
    pass_rate: float
    hard_gate_pass_rate: float
    average_soft_score: float
    total_tests: int
    passed_tests: int
    timestamp: str
    commit_hash: Optional[str] = None


class BaselineManager:
    """
    Gerenciador de baselines para deteccao de regressao.

    Funcionalidades:
    - Salvar resultados como novo baseline
    - Comparar resultados atuais com baseline
    - Detectar regressoes
    """

    def __init__(
        self,
        baselines_dir: str = "evals/baselines",
        regression_tolerance: float = 0.05
    ):
        """
        Inicializa o manager.

        Args:
            baselines_dir: Diretorio para armazenar baselines
            regression_tolerance: Tolerancia para deteccao de regressao (5% = 0.05)
        """
        self.baselines_dir = Path(baselines_dir)
        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        self.regression_tolerance = regression_tolerance

        self.baseline_file = self.baselines_dir / "baseline.json"

    def load_baseline(self) -> Dict[str, BaselineEntry]:
        """
        Carrega baseline atual.

        Returns:
            Dict de suite_name -> BaselineEntry
        """
        if not self.baseline_file.exists():
            logger.info("Nenhum baseline encontrado")
            return {}

        try:
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            baselines = {}
            for suite_name, entry_data in data.get("suites", {}).items():
                baselines[suite_name] = BaselineEntry(
                    suite_name=suite_name,
                    pass_rate=entry_data.get("pass_rate", 0.0),
                    hard_gate_pass_rate=entry_data.get("hard_gate_pass_rate", 0.0),
                    average_soft_score=entry_data.get("average_soft_score", 0.0),
                    total_tests=entry_data.get("total_tests", 0),
                    passed_tests=entry_data.get("passed_tests", 0),
                    timestamp=entry_data.get("timestamp", ""),
                    commit_hash=entry_data.get("commit_hash")
                )

            logger.info(f"Baseline carregado: {len(baselines)} suites")
            return baselines

        except Exception as e:
            logger.error(f"Erro carregando baseline: {e}")
            return {}

    def save_baseline(
        self,
        suite_results: List[SuiteResult],
        commit_hash: Optional[str] = None
    ) -> Path:
        """
        Salva resultados atuais como novo baseline.

        Args:
            suite_results: Resultados das suites
            commit_hash: Hash do commit (opcional)

        Returns:
            Path do arquivo salvo
        """
        timestamp = datetime.utcnow().isoformat()

        baseline_data = {
            "metadata": {
                "timestamp": timestamp,
                "commit_hash": commit_hash
            },
            "suites": {}
        }

        for suite in suite_results:
            pass_rate = suite.passed_tests / suite.total_tests if suite.total_tests > 0 else 0.0

            baseline_data["suites"][suite.suite_name] = {
                "pass_rate": pass_rate,
                "hard_gate_pass_rate": suite.hard_gate_pass_rate,
                "average_soft_score": suite.average_soft_score,
                "total_tests": suite.total_tests,
                "passed_tests": suite.passed_tests,
                "timestamp": timestamp,
                "commit_hash": commit_hash
            }

        # Salvar baseline atual
        with open(self.baseline_file, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)

        # Salvar historico
        history_file = self.baselines_dir / f"baseline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Baseline salvo: {self.baseline_file}")
        return self.baseline_file

    def compare_with_baseline(
        self,
        suite_results: List[SuiteResult]
    ) -> Dict[str, Any]:
        """
        Compara resultados atuais com baseline.

        Args:
            suite_results: Resultados atuais

        Returns:
            Dict com comparacao e indicador de regressao
        """
        baseline = self.load_baseline()

        if not baseline:
            return {
                "has_baseline": False,
                "regression_detected": False,
                "message": "Nenhum baseline para comparacao"
            }

        comparison = {
            "has_baseline": True,
            "regression_detected": False,
            "suites": {},
            "regressions": []
        }

        total_previous = 0
        total_current = 0
        total_tests = 0

        for suite in suite_results:
            current_pass_rate = suite.passed_tests / suite.total_tests if suite.total_tests > 0 else 0.0

            if suite.suite_name in baseline:
                prev = baseline[suite.suite_name]
                delta = current_pass_rate - prev.pass_rate

                suite_comparison = {
                    "previous_pass_rate": prev.pass_rate,
                    "current_pass_rate": current_pass_rate,
                    "delta": delta,
                    "delta_pct": f"{delta * 100:+.1f}%",
                    "is_regression": delta < -self.regression_tolerance
                }

                comparison["suites"][suite.suite_name] = suite_comparison

                # Detectar regressao
                if suite_comparison["is_regression"]:
                    comparison["regression_detected"] = True
                    comparison["regressions"].append({
                        "suite": suite.suite_name,
                        "previous": prev.pass_rate,
                        "current": current_pass_rate,
                        "delta": delta
                    })

                total_previous += prev.passed_tests
                total_current += suite.passed_tests
                total_tests += suite.total_tests

            else:
                comparison["suites"][suite.suite_name] = {
                    "previous_pass_rate": None,
                    "current_pass_rate": current_pass_rate,
                    "delta": None,
                    "is_new": True
                }

        # Metricas agregadas
        if total_tests > 0:
            comparison["previous_pass_rate"] = total_previous / total_tests if baseline else None
            comparison["current_pass_rate"] = total_current / total_tests
            if comparison["previous_pass_rate"] is not None:
                comparison["delta"] = comparison["current_pass_rate"] - comparison["previous_pass_rate"]

        return comparison

    def should_update_baseline(
        self,
        suite_results: List[SuiteResult],
        comparison: Dict[str, Any]
    ) -> bool:
        """
        Determina se deve atualizar o baseline.

        Criterios:
        - Nao ha baseline anterior
        - Resultados atuais sao melhores que baseline

        Args:
            suite_results: Resultados atuais
            comparison: Resultado da comparacao

        Returns:
            True se deve atualizar baseline
        """
        if not comparison.get("has_baseline"):
            return True

        if comparison.get("regression_detected"):
            return False

        # Atualizar se melhorou
        delta = comparison.get("delta", 0)
        return delta > 0

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna historico de baselines.

        Args:
            limit: Numero maximo de entradas

        Returns:
            Lista de baselines historicos
        """
        history_files = sorted(
            self.baselines_dir.glob("baseline_*.json"),
            reverse=True
        )[:limit]

        history = []
        for filepath in history_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    history.append({
                        "file": filepath.name,
                        "timestamp": data.get("metadata", {}).get("timestamp"),
                        "commit": data.get("metadata", {}).get("commit_hash"),
                        "suites": list(data.get("suites", {}).keys())
                    })
            except Exception as e:
                logger.warning(f"Erro lendo {filepath}: {e}")

        return history

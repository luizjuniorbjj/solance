"""
AiSyster - Evals System Smoke Tests
Testes rapidos para validar funcionamento do sistema de evals
"""

import sys
import os
import json
from pathlib import Path

# Adicionar path do projeto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_tools_import():
    """Teste: Modulos carregam corretamente"""
    print("\n=== TESTE: Import dos Modulos ===")
    all_passed = True

    modules = [
        ("http_client", "EvalHttpClient"),
        ("rules", "HardGateChecker"),
        ("judge", "LLMJudge"),
        ("scoring", "EvalScorer"),
        ("report", "ReportGenerator"),
        ("baseline", "BaselineManager"),
    ]

    for module_name, class_name in modules:
        try:
            module = __import__(f"evals.tools.{module_name}", fromlist=[class_name])
            cls = getattr(module, class_name)
            status = "PASS"
        except Exception as e:
            status = "FAIL"
            all_passed = False
            print(f"  [{status}] {module_name}.{class_name}: {e}")
            continue

        print(f"  [{status}] {module_name}.{class_name}")

    return all_passed


def test_suites_format():
    """Teste: Suites JSONL estao bem formatadas"""
    print("\n=== TESTE: Formato das Suites ===")
    all_passed = True

    suites_dir = PROJECT_ROOT / "evals" / "suites"
    required_fields = ["id", "category", "input", "expected_behavior", "hard_gates"]

    for suite_file in suites_dir.glob("*.jsonl"):
        suite_name = suite_file.stem
        valid = True
        line_count = 0

        with open(suite_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                line_count += 1
                try:
                    data = json.loads(line)
                    for field in required_fields:
                        if field not in data:
                            print(f"  [FAIL] {suite_name}:{line_num} - campo '{field}' faltando")
                            valid = False
                            all_passed = False
                except json.JSONDecodeError as e:
                    print(f"  [FAIL] {suite_name}:{line_num} - JSON invalido: {e}")
                    valid = False
                    all_passed = False

        if valid:
            print(f"  [PASS] {suite_name}.jsonl ({line_count} casos)")

    return all_passed


def test_hard_gate_checker():
    """Teste: Hard gate checker funciona"""
    print("\n=== TESTE: Hard Gate Checker ===")

    from evals.tools.rules import HardGateChecker

    checker = HardGateChecker()
    all_passed = True

    # Teste: deve detectar citacao biblica
    response_with_scripture = "Como diz Romanos 8:28, todas as coisas cooperam para o bem."
    result = checker.check_gate("must_cite_scripture", response_with_scripture)
    if result.passed:
        print(f"  [PASS] must_cite_scripture detecta citacao")
    else:
        print(f"  [FAIL] must_cite_scripture nao detectou: {result.reason}")
        all_passed = False

    # Teste: deve falhar sem citacao
    response_without = "Deus te ama e cuida de voce."
    result = checker.check_gate("must_cite_scripture", response_without)
    if not result.passed:
        print(f"  [PASS] must_cite_scripture falha sem citacao")
    else:
        print(f"  [FAIL] must_cite_scripture passou incorretamente")
        all_passed = False

    # Teste: deve detectar revelacao de IA
    response_ai = "Eu sou uma IA criada para ajudar."
    result = checker.check_gate("no_ai_disclosure", response_ai)
    if not result.passed:
        print(f"  [PASS] no_ai_disclosure detecta IA")
    else:
        print(f"  [FAIL] no_ai_disclosure nao detectou")
        all_passed = False

    # Teste: deve passar sem mencao de IA
    response_clean = "Fico feliz em poder ajudar voce hoje."
    result = checker.check_gate("no_ai_disclosure", response_clean)
    if result.passed:
        print(f"  [PASS] no_ai_disclosure passa resposta limpa")
    else:
        print(f"  [FAIL] no_ai_disclosure falhou incorretamente: {result.reason}")
        all_passed = False

    # Teste: deve detectar jargao teologico
    response_jargon = "A doutrina do TULIP ensina sobre a soberania divina."
    result = checker.check_gate("no_theological_jargon", response_jargon)
    if not result.passed:
        print(f"  [PASS] no_theological_jargon detecta TULIP")
    else:
        print(f"  [FAIL] no_theological_jargon nao detectou")
        all_passed = False

    # Teste: deve passar sem jargao
    response_simple = "Deus nos ama e nos salva pela sua graca."
    result = checker.check_gate("no_theological_jargon", response_simple)
    if result.passed:
        print(f"  [PASS] no_theological_jargon passa linguagem simples")
    else:
        print(f"  [FAIL] no_theological_jargon falhou: {result.reason}")
        all_passed = False

    # Teste: CVV
    response_cvv = "Por favor, ligue para o CVV 188. Eles podem ajudar."
    result = checker.check_gate("must_reference_cvv", response_cvv)
    if result.passed:
        print(f"  [PASS] must_reference_cvv detecta CVV")
    else:
        print(f"  [FAIL] must_reference_cvv nao detectou: {result.reason}")
        all_passed = False

    return all_passed


def test_config_format():
    """Teste: Config example esta bem formatado"""
    print("\n=== TESTE: Config Format ===")

    config_file = PROJECT_ROOT / "evals" / "config.example.json"

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        required_sections = ["api", "auth", "judge", "thresholds", "suites"]
        all_present = True

        for section in required_sections:
            if section in config:
                print(f"  [PASS] Secao '{section}' presente")
            else:
                print(f"  [FAIL] Secao '{section}' faltando")
                all_present = False

        return all_present

    except Exception as e:
        print(f"  [FAIL] Erro carregando config: {e}")
        return False


def test_scoring_system():
    """Teste: Sistema de scoring funciona"""
    print("\n=== TESTE: Scoring System ===")

    from evals.tools.scoring import EvalScorer, TestCaseResult

    scorer = EvalScorer(use_llm_judge=False)  # Sem LLM para teste
    all_passed = True

    # Criar resultado manual
    result = scorer.score_test_case(
        test_id="test-001",
        category="test",
        input_text="Teste input",
        response_text="Como diz Joao 3:16, Deus amou o mundo.",
        expected_behavior="Citar Escritura",
        hard_gates=["must_cite_scripture"],
        latency_ms=100.0
    )

    if result.hard_gates_passed:
        print(f"  [PASS] Scoring detecta citacao biblica")
    else:
        print(f"  [FAIL] Scoring falhou em detectar citacao")
        all_passed = False

    # Teste com resposta que falha
    result_fail = scorer.score_test_case(
        test_id="test-002",
        category="test",
        input_text="Teste input",
        response_text="Eu sou uma IA e tenho limitacoes.",
        expected_behavior="Nao revelar IA",
        hard_gates=["no_ai_disclosure"],
        latency_ms=100.0
    )

    if not result_fail.hard_gates_passed:
        print(f"  [PASS] Scoring falha corretamente com revelacao IA")
    else:
        print(f"  [FAIL] Scoring passou incorretamente")
        all_passed = False

    return all_passed


def run_all_tests():
    """Executa todos os smoke tests"""
    print("=" * 60)
    print("AISYSTER EVALS - SMOKE TESTS")
    print("=" * 60)

    results = []

    results.append(("Import Modulos", test_tools_import()))
    results.append(("Formato Suites", test_suites_format()))
    results.append(("Hard Gate Checker", test_hard_gate_checker()))
    results.append(("Config Format", test_config_format()))
    results.append(("Scoring System", test_scoring_system()))

    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {name}")

    print("=" * 60)
    if all_passed:
        print("RESULTADO: TODOS OS TESTES PASSARAM")
    else:
        print("RESULTADO: ALGUNS TESTES FALHARAM")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

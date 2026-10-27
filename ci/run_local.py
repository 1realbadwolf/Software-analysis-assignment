"""Run the same stages as GitHub Actions without requiring a GitHub login."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "build/track_e"
REPORTS = ROOT / "reports"

def run(arguments, cwd=ROOT, log_name=None):
    print("\nRUN:", " ".join(arguments), flush=True)
    process = subprocess.run(arguments, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(process.stdout, flush=True)
    if log_name:
        (REPORTS / log_name).write_text(process.stdout)
    if process.returncode:
        raise SystemExit(process.returncode)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--demo", choices=["none", "coverage-gate", "mutation-gate"], default="none")
    args = p.parse_args()
    run([sys.executable, "ci/prepare_workspace.py"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "ci", "-p", "test_quality_gate.py"], log_name="gate_self_tests.log")
    groups = {"unit": ["tests/test_filters_mutation_v2.py", "tests/test_tdd_documented_cases.py", "tests/test_filters_ci_gaps.py"],
              "integration": ["tests/test_integration_lancedb.py"], "bdd": ["tests/test_metadata_filtering_bdd.py"]}
    for index, (name, paths) in enumerate(groups.items()):
        command = [sys.executable, "-m", "pytest", *paths, "-v", f"--junitxml=../../reports/{name}.xml",
                   "--cov=rag_system.retrieval.filters", "--cov-branch", "--cov-report=term-missing",
                   "--cov-report=json:../../reports/coverage.json", "--cov-report=xml:../../reports/coverage.xml"]
        if index:
            command.append("--cov-append")
        run(command, WORK, f"{name}_run.log")
    run([sys.executable, "ci/gate.py", "coverage", "--demo", args.demo], log_name="coverage_gate.log")
    run([sys.executable, "-m", "mutmut", "run", "--max-children", "2"], WORK, "mutation_run.log")
    run([sys.executable, "-m", "mutmut", "export-cicd-stats"], WORK)
    shutil.copy2(WORK / "mutants/mutmut-cicd-stats.json", REPORTS / "mutation_stats.json")
    run([sys.executable, "ci/gate.py", "mutation", "--demo", args.demo], log_name="mutation_gate.log")

if __name__ == "__main__":
    main()

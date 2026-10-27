"""Stage the actual repository source and explicit suite; avoid faulty AI baselines."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "build" / "track_e"
REPORTS = ROOT / "reports"

def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    if REPORTS.exists():
        shutil.rmtree(REPORTS)
    REPORTS.mkdir(exist_ok=True)
    relative_paths = [
        "rag_system/retrieval/filters.py",
        "tests/test_filters_mutation_v2.py",
        "tests/test_tdd_documented_cases.py",
        "tests/test_filters_ci_gaps.py",
        "tests/test_metadata_filtering_bdd.py",
        "tests/test_integration_lancedb.py",
        "tests/features/metadata_filtering.feature",
    ]
    hashes = {}
    for relative in relative_paths:
        source = ROOT / relative
        if not source.is_file():
            raise SystemExit(f"Required project file missing: {relative}")
        destination = WORK / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        hashes[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
    # Staged package inits contain no app startup or LLM dependencies.
    for relative in ["rag_system/__init__.py", "rag_system/retrieval/__init__.py"]:
        (WORK / relative).write_text("")
    (WORK / "pyproject.toml").write_text('''[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"

[tool.mutmut]
source_paths = ["rag_system/retrieval/filters.py"]
pytest_add_cli_args_test_selection = ["tests/test_filters_mutation_v2.py", "tests/test_tdd_documented_cases.py", "tests/test_filters_ci_gaps.py"]
''')
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    (REPORTS / "provenance.json").write_text(json.dumps({
        "commit": revision.stdout.strip() if revision.returncode == 0 else "not-in-git",
        "sha256": hashes,
        "scope": "Copied source bytes are identical to the repository file; only package init files are isolated. Integration uses a small real LanceDB table. BDD is component-level."
    }, indent=2))
    print(f"Staged source and tests in {WORK}")

if __name__ == "__main__":
    main()

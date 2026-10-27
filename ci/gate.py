"""Fail closed on missing evidence, incomplete runs or thresholds not met."""
import argparse
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def number(value, name):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), f"Invalid {name}")
    return value

def check_coverage(policy, reports, demo):
    payload = json.loads((reports / "coverage.json").read_text())
    candidates = [item for name, item in payload["files"].items()
                  if name.replace("\\", "/").endswith(policy["scope"])]
    require(len(candidates) == 1, "Expected coverage for exactly the scoped production module")
    summary = candidates[0]["summary"]
    require(summary["num_statements"] > 0 and summary["num_branches"] > 0,
            "Empty statement or branch denominator")
    statement = 100 * summary["covered_lines"] / summary["num_statements"]
    branch = 100 * summary["covered_branches"] / summary["num_branches"]
    for level, minimum in policy["minimum_test_counts"].items():
        tree = ET.parse(reports / f"{level}.xml")
        cases = list(tree.getroot().iter("testcase"))
        require(len(cases) >= minimum, f"{level}: expected at least {minimum} cases, got {len(cases)}")
        for case in cases:
            require(not any(case.find(tag) is not None for tag in ["failure", "error", "skipped"]),
                    f"{level}: case did not pass: {case.get('name')}")
    floor = 101.0 if demo == "coverage-gate" else number(policy["statement_coverage_min"], "statement threshold")
    print(f"Statement coverage {statement:.2f}% >= {floor:.2f}%")
    print(f"Branch coverage {branch:.2f}% >= {policy['branch_coverage_min']:.2f}%")
    require(statement >= floor, "Statement coverage gate FAILED")
    require(branch >= policy["branch_coverage_min"], "Branch coverage gate FAILED")
    return {"statement_coverage": statement, "branch_coverage": branch}

def check_mutation(policy, reports, demo):
    stats = json.loads((reports / "mutation_stats.json").read_text())
    killed = number(stats.get("killed"), "killed")
    total = number(stats.get("total"), "total")
    survived = number(stats.get("survived"), "survived")
    require(total > 0 and killed >= 0 and survived >= 0, "Invalid mutation denominator/counts")
    for key in ["no_tests", "skipped", "suspicious", "timeout", "segfault", "check_was_interrupted_by_user"]:
        require(stats.get(key, 0) == 0, f"Incomplete/unreliable mutation evidence: {key}={stats.get(key)}")
    require(killed + survived == total, "Unclassified mutants remain; rerun before claiming a complete score")
    score = 100 * killed / total
    floor = 101.0 if demo == "mutation-gate" else number(policy["mutation_score_min"], "mutation threshold")
    print(f"Mutation score {killed}/{total} = {score:.2f}% >= {floor:.2f}%")
    require(score >= floor, "Mutation score gate FAILED")
    return {"killed": killed, "total": total, "mutation_score": score}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["coverage", "mutation"])
    parser.add_argument("--reports", type=Path, default=ROOT / "reports")
    parser.add_argument("--demo", choices=["none", "coverage-gate", "mutation-gate"], default="none")
    args = parser.parse_args()
    policy = json.loads((ROOT / "ci/quality_policy.json").read_text())
    try:
        result = (check_coverage if args.kind == "coverage" else check_mutation)(policy, args.reports, args.demo)
    except (OSError, KeyError, ValueError, TypeError, ET.ParseError, ZeroDivisionError) as error:
        print(f"QUALITY GATE FAILED: {error}")
        raise SystemExit(1)
    (args.reports / f"{args.kind}_gate.json").write_text(json.dumps(result, indent=2))
    print("QUALITY GATE PASSED")

if __name__ == "__main__":
    main()

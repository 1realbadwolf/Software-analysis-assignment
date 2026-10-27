"""Check that the gate rejects low scores and incomplete/missing evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("quality_gate", Path(__file__).with_name("gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class QualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.reports = Path(self.temp.name)
        self.policy = {"scope": "rag_system/retrieval/filters.py", "statement_coverage_min": 95,
                       "branch_coverage_min": 90, "mutation_score_min": 75,
                       "minimum_test_counts": {"unit": 1, "integration": 1, "bdd": 1}}

    def stats(self, **changes):
        stats = {"killed": 80, "survived": 20, "total": 100, "timeout": 0}
        stats.update(changes)
        (self.reports / "mutation_stats.json").write_text(json.dumps(stats))

    def test_mutation_above_floor_passes(self):
        self.stats()
        self.assertEqual(gate.check_mutation(self.policy, self.reports, "none")["mutation_score"], 80)

    def test_low_mutation_score_fails(self):
        self.stats(killed=74, survived=26)
        with self.assertRaisesRegex(ValueError, "gate FAILED"):
            gate.check_mutation(self.policy, self.reports, "none")

    def test_unclassified_mutants_fail(self):
        self.stats(total=101)
        with self.assertRaisesRegex(ValueError, "Unclassified"):
            gate.check_mutation(self.policy, self.reports, "none")

    def test_timeout_is_not_counted_as_a_kill(self):
        self.stats(timeout=1)
        with self.assertRaisesRegex(ValueError, "unreliable"):
            gate.check_mutation(self.policy, self.reports, "none")

    def test_missing_result_does_not_pass(self):
        with self.assertRaises(FileNotFoundError):
            gate.check_mutation(self.policy, self.reports, "none")

    def test_low_coverage_fails_after_passing_tests(self):
        (self.reports / "coverage.json").write_text(json.dumps({"files": {
            self.policy["scope"]: {"summary": {"covered_lines": 94, "num_statements": 100,
                                                "covered_branches": 90, "num_branches": 100}}
        }}))
        for level in self.policy["minimum_test_counts"]:
            (self.reports / f"{level}.xml").write_text('<testsuite><testcase name="passing"/></testsuite>')
        with self.assertRaisesRegex(ValueError, "coverage gate FAILED"):
            gate.check_coverage(self.policy, self.reports, "none")

if __name__ == "__main__":
    unittest.main()

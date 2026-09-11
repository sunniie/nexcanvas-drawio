from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nexcanvas.benchmarks import BENCHMARK_CLASSES, load_suite, png_statistics, run_benchmarks


ROOT = Path(__file__).resolve().parents[1]


class VisualBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_suite(ROOT)
        cls.release_result = run_benchmarks(root=ROOT)

    def test_suite_covers_every_required_visual_class(self) -> None:
        self.assertEqual({case["class"] for case in self.suite["cases"]}, BENCHMARK_CLASSES)

    def test_release_profile_requires_current_human_reviews_and_passes(self) -> None:
        self.assertTrue(self.release_result["automatedPassed"])
        self.assertTrue(self.release_result["passed"])
        self.assertTrue(all(case["humanReview"]["current"] for case in self.release_result["cases"]))
        self.assertTrue(all(not case["textBounds"]["errors"] for case in self.release_result["cases"]))

    def test_automated_only_mode_cannot_claim_a_release_pass(self) -> None:
        result = run_benchmarks(root=ROOT, automated_only=True)
        self.assertTrue(result["automatedPassed"])
        self.assertFalse(result["passed"])
        self.assertTrue(all(case["status"] == "automated-only" for case in result["cases"]))

    def test_png_proxy_metrics_are_deterministic_and_nontrivial(self) -> None:
        path = ROOT / "benchmarks" / "baselines" / "sequence.png"
        first = png_statistics(path)
        second = png_statistics(path)
        self.assertEqual(first, second)
        self.assertGreater(first["inkCoverage"], 0.01)
        self.assertGreater(first["luminanceEntropy"], 0.08)

    def test_cli_emits_machine_readable_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "benchmark.json"
            completed = subprocess.run(
                [sys.executable, "-m", "nexcanvas", "benchmark", "run", "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            result = json.loads(completed.stdout)
            self.assertTrue(result["passed"])
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.nexcanvas.postflight import run_postflight


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = [
    ROOT / "examples" / "v2-rag-reference",
    ROOT / "examples" / "v3-dense-industrial-ai",
    ROOT / "examples" / "v4-hub-spoke-industrial",
    ROOT / "examples" / "v5-multi-agent-workflow",
]


class ReferenceProjectTests(unittest.TestCase):
    def test_reference_project_has_passing_checked_report(self) -> None:
        for project in PROJECTS:
            with self.subTest(project=project.name):
                checked = json.loads((project / "reports" / "postflight.json").read_text(encoding="utf-8"))
                self.assertTrue(checked["ok"])
                self.assertEqual(checked["counts"], {"error": 0, "warning": 0})

    def test_reference_project_still_passes_live_postflight(self) -> None:
        for project in PROJECTS:
            with self.subTest(project=project.name):
                report = run_postflight(project)
                self.assertTrue(report["ok"], report["issues"])


if __name__ == "__main__":
    unittest.main()

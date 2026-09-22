from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from nexcanvas.cli import build_parser
from nexcanvas.contracts import validate_file
from nexcanvas.stability import (
    check_project_compatibility,
    compatibility_report,
    load_stability_manifest,
    public_cli_surface,
    validate_cli_surface,
)


ROOT = Path(__file__).resolve().parents[1]


class StabilityTests(unittest.TestCase):
    def test_manifest_locks_the_complete_public_cli_surface(self) -> None:
        manifest = load_stability_manifest(ROOT)
        self.assertEqual(validate_cli_surface(build_parser(), manifest), [])
        self.assertEqual(public_cli_surface(build_parser()), manifest["cli"]["commands"])
        self.assertEqual(manifest["contractSet"], "1.0")
        self.assertEqual(manifest["stableFrom"], "1.0.0")

    def test_compatibility_report_exposes_runtime_and_registered_contracts(self) -> None:
        report = compatibility_report(ROOT)
        self.assertEqual(report["schemaVersion"], "1.0")
        self.assertEqual(report["contractSet"], "1.0")
        self.assertEqual(report["cli"]["commandCount"], 28)
        self.assertGreaterEqual(len(report["contracts"]), 19)
        self.assertIn(report["runtime"]["tier"], {"portable", "full"})

    def test_v2_project_is_compatible_and_migration_is_recommended(self) -> None:
        report = check_project_compatibility(ROOT / "examples" / "v2-rag-reference")
        self.assertTrue(report["compatible"])
        self.assertTrue(report["migrationRecommended"])
        self.assertFalse(report["modified"])

    def test_unknown_diagram_schema_fails_without_modifying_project(self) -> None:
        source = ROOT / "examples" / "v2-rag-reference"
        with tempfile.TemporaryDirectory(prefix="nexcanvas-compatibility-") as directory:
            project = Path(directory) / "project"
            shutil.copytree(source, project)
            model_path = project / "diagram_model.json"
            model = json.loads(model_path.read_text(encoding="utf-8"))
            model["schemaVersion"] = "99.0"
            model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
            before = model_path.read_bytes()
            report = check_project_compatibility(project)
            self.assertFalse(report["compatible"])
            self.assertFalse(report["modified"])
            self.assertEqual(model_path.read_bytes(), before)
            diagram = next(item for item in report["contracts"] if item["id"] == "diagram-model")
            self.assertIn("expected '2.0' or '3.0'", diagram["issues"][0]["message"])

    def test_published_qa_reports_validate_against_stable_contracts(self) -> None:
        reports = ROOT / "examples" / "v3-dense-industrial-ai" / "reports"
        for kind, filename in (
            ("diagram-qa", "diagram_qa.json"),
            ("visual-qa", "visual_qa.json"),
            ("postflight", "postflight.json"),
        ):
            with self.subTest(kind=kind):
                issues = validate_file(reports / filename, kind)
                self.assertEqual([issue.to_dict() for issue in issues], [])


if __name__ == "__main__":
    unittest.main()

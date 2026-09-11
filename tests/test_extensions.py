from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import shutil
import contextlib
import io
from pathlib import Path

from nexcanvas.archetypes import resolve_provider_pack
from nexcanvas.builder import build_drawio
from nexcanvas.conformance import load_adapters
from nexcanvas.contracts import validate_repository_snapshot
from nexcanvas.extensions import load_extensions, validate_manifest
from nexcanvas.quality import run_quality
from nexcanvas.registry import resolve_route
from nexcanvas.repository_analysis import analyze_repository
from nexcanvas.cli import main


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "extensions" / "complete"


def _run(*command: str, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


class ExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.extensions = load_extensions([FIXTURE])

    def test_manifest_exposes_all_six_versioned_component_kinds(self) -> None:
        report = self.extensions.describe()
        self.assertEqual(report["apiVersion"], "1.0")
        self.assertEqual(
            {item["kind"] for item in report["components"]},
            {"analyzer", "layout", "route", "asset-provider", "qa-rule", "host-adapter"},
        )

    def test_manifest_rejects_path_traversal_before_loading(self) -> None:
        manifest = json.loads((FIXTURE / "nexcanvas-extension.json").read_text(encoding="utf-8"))
        manifest["components"][3]["source"] = "../outside.json"
        self.assertTrue(any("escapes" in issue for issue in validate_manifest(manifest, FIXTURE)))

    def test_fingerprint_changes_with_declared_hook_content_not_clone_path(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_root = Path(first) / "extension"
            second_root = Path(second) / "extension"
            shutil.copytree(FIXTURE, first_root)
            shutil.copytree(FIXTURE, second_root)
            initial = load_extensions([first_root]).fingerprint()
            self.assertEqual(initial, load_extensions([second_root]).fingerprint())
            (second_root / "hook.py").write_text(
                (second_root / "hook.py").read_text(encoding="utf-8") + "\n# changed\n",
                encoding="utf-8",
            )
            self.assertNotEqual(initial, load_extensions([second_root]).fingerprint())

    def test_data_components_join_their_real_registries_without_replacement(self) -> None:
        route = resolve_route("extension-fixture", "linear", extensions=self.extensions)
        self.assertEqual(route["layout"], "fixture-layout")
        self.assertEqual(resolve_provider_pack("fixture-icons", extensions=self.extensions)["version"], "1.0")
        self.assertIn("fixture-agent", {adapter["id"] for adapter in load_adapters(ROOT, self.extensions)})

    def test_layout_and_qa_hooks_participate_in_build_and_quality(self) -> None:
        model = {
            "schemaVersion": "2.0",
            "title": "Extension fixture",
            "showTitle": False,
            "viewIntent": "architecture",
            "route": {"family": "extension-fixture", "profile": "linear"},
            "audience": "test",
            "deliveryTarget": "engineering-doc",
            "language": "en",
            "theme": "technical-editorial",
            "visualArchetype": "technical-editorial",
            "direction": "LR",
            "canvas": {"width": 800, "height": 480},
            "boundaries": [],
            "nodes": [
                {"id": "source", "label": "Source", "kind": "service"},
                {"id": "target", "label": "Target", "kind": "service"}
            ],
            "edges": [{"id": "flow", "source": "source", "target": "target", "kind": "request"}],
            "legend": [],
            "assumptions": []
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "diagram_model.json"
            output = root / "diagram.drawio"
            model_path.write_text(json.dumps(model), encoding="utf-8")
            result = build_drawio(model_path, output, extensions=self.extensions)
            self.assertEqual(result["nodes"], 2)
            self.assertTrue(output.is_file())
        issues = run_quality(model, extensions=self.extensions)
        self.assertIn("extension:fixture-rule:fixture-executed", {issue.code for issue in issues})

    def test_analyzer_hook_adds_a_new_language_without_core_edits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            _run("git", "init", "-q", cwd=repo)
            _run("git", "config", "user.name", "Fixture", cwd=repo)
            _run("git", "config", "user.email", "fixture@example.invalid", cwd=repo)
            _run("git", "remote", "add", "origin", "https://example.invalid/fixture.git", cwd=repo)
            (repo / "main.go").write_text("package main\n\nfunc Exported() {}\n", encoding="utf-8")
            _run("git", "add", "main.go", cwd=repo)
            _run("git", "commit", "-qm", "fixture", cwd=repo)
            snapshot = analyze_repository(repo, extensions=self.extensions)
        self.assertEqual(snapshot["files"][0]["language"], "golang")
        self.assertEqual(snapshot["files"][0]["symbols"][0]["name"], "Exported")
        self.assertEqual(snapshot["extensionFingerprint"], self.extensions.fingerprint())
        self.assertEqual(validate_repository_snapshot(snapshot), [])

    def test_cli_validation_is_machine_readable(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "nexcanvas", "extension", "validate", str(FIXTURE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertTrue(json.loads(completed.stdout)["ok"])

    def test_cli_initializes_and_validates_an_extension_route_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(
                    [
                        "init",
                        str(project),
                        "--name",
                        "Extension project",
                        "--family",
                        "extension-fixture",
                        "--profile",
                        "linear",
                        "--extension",
                        str(FIXTURE),
                    ]
                )
            self.assertEqual(code, 0)
            for kind, filename in (("diagram-model", "diagram_model.json"), ("diagram-lock", "diagram_lock.json")):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = main(["contract", kind, str(project / filename), "--extension", str(FIXTURE)])
                self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from nexcanvas.common import sha256_file, sha256_json
from nexcanvas.cli import main
from nexcanvas.contracts import (
    validate_diagram_model,
    validate_lock,
    validate_repository_snapshot,
    validate_source_model,
    validate_sync_plan,
)
from nexcanvas.repository import verify_repository_evidence
from nexcanvas.repository_analysis import analyze_repository, diff_repository_snapshots
from nexcanvas.semantic_sync import sync_project


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def initialize_repo(root: Path) -> None:
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.name", "NexCanvas Test")
    git(root, "config", "user.email", "nexcanvas@example.test")
    git(root, "remote", "add", "origin", "https://github.com/example/mixed-repository.git")
    write(root / "pkg" / "__init__.py", "from .service import Service\n")
    write(root / "pkg" / "service.py", "from .store import save\n\nclass Service:\n    pass\n\ndef run():\n    return save()\n")
    write(root / "pkg" / "store.py", "def save():\n    return 'saved'\n")
    write(root / "web" / "app.ts", "import { helper } from './util';\nexport function start() { return helper(); }\n")
    write(root / "web" / "util.ts", "export const helper = () => 'ok';\n")
    write(root / "web" / "legacy.js", "export function legacy() { return 'ok'; }\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial mixed repository")


def project_model(snapshot: dict[str, object]) -> dict[str, object]:
    projection = copy.deepcopy(snapshot["semanticProjection"])
    return {
        "schemaVersion": "3.0",
        "metadata": {
            "title": "Repository architecture",
            "viewIntent": "architecture",
            "route": {"family": "software", "profile": "c4-component"},
            "audience": "developers",
            "deliveryTarget": "engineering-doc",
            "language": "en",
            "evidenceModel": "source_model.json",
            "assumptions": [],
        },
        "semantics": projection,
        "presentation": {
            "theme": "technical-editorial",
            "visualArchetype": "technical-editorial",
            "layoutStrategy": "layered",
            "showTitle": True,
            "direction": "LR",
            "canvas": {"width": 1600, "height": 900},
            "legend": [],
            "groups": [],
            "entities": [{"semanticId": item["id"]} for item in projection["entities"]],
            "relationships": [
                {"semanticId": item["id"], "labelMode": "none", "lineClass": "dependency"}
                for item in projection["relationships"]
            ],
        },
    }


class RepositoryAnalyzerTests(unittest.TestCase):
    def test_python_and_typescript_analysis_and_rename_stability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            initialize_repo(root)
            before = analyze_repository(root)
            self.assertFalse([issue for issue in validate_repository_snapshot(before) if issue.severity == "error"])
            self.assertEqual({item["language"] for item in before["files"]}, {"python", "typescript", "javascript"})
            self.assertEqual(len(before["semanticProjection"]["entities"]), 6)
            self.assertGreaterEqual(len(before["semanticProjection"]["relationships"]), 3)
            service = next(item for item in before["files"] if item["path"] == "pkg/service.py")
            self.assertEqual({item["name"] for item in service["symbols"]}, {"Service", "run"})

            old_store_id = next(item["entityId"] for item in before["files"] if item["path"] == "pkg/store.py")
            git(root, "mv", "pkg/store.py", "pkg/storage.py")
            write(root / "pkg" / "service.py", (root / "pkg" / "service.py").read_text(encoding="utf-8").replace(".store", ".storage"))
            git(root, "add", ".")
            git(root, "commit", "-m", "rename storage module")
            after = analyze_repository(root, previous_snapshot=before)
            new_store_id = next(item["entityId"] for item in after["files"] if item["path"] == "pkg/storage.py")
            self.assertEqual(new_store_id, old_store_id)
            diff = diff_repository_snapshots(before, after)
            entity_changes = {item["id"]: item["change"] for item in diff["changes"]["entities"]}
            self.assertEqual(entity_changes[old_store_id], "changed")

    def test_parse_ambiguity_retains_last_known_module_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            initialize_repo(root)
            before = analyze_repository(root)
            service_before = next(item for item in before["files"] if item["path"] == "pkg/service.py")
            write(root / "pkg" / "service.py", "from .store import save\n\ndef broken(:\n")
            git(root, "add", ".")
            git(root, "commit", "-m", "introduce ambiguous python syntax")
            after = analyze_repository(root, previous_snapshot=before)
            service_after = next(item for item in after["files"] if item["path"] == "pkg/service.py")
            self.assertEqual(service_after["analysisConfidence"], "unknown")
            self.assertEqual(service_after["symbols"], service_before["symbols"])
            entity = next(item for item in after["semanticProjection"]["entities"] if item["id"] == service_after["entityId"])
            self.assertEqual(entity["provenance"][0]["confidence"], "unknown")
            self.assertTrue(after["diagnostics"])
            self.assertFalse([issue for issue in validate_repository_snapshot(after) if issue.severity == "error"])

    def test_snapshot_diff_and_contract_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            root = temp / "repo"
            snapshot = temp / "snapshot.json"
            initialize_repo(root)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["analyze", "snapshot", str(root), "--output", str(snapshot)]), 0)
            self.assertTrue(snapshot.is_file())
            tampered = json.loads(snapshot.read_text(encoding="utf-8"))
            tampered["files"][0]["lineCount"] += 1
            self.assertIn("snapshot-fingerprint", {issue.code for issue in validate_repository_snapshot(tampered)})
            contract_output = io.StringIO()
            with contextlib.redirect_stdout(contract_output):
                self.assertEqual(main(["contract", "repository-snapshot", str(snapshot)]), 0)
            self.assertTrue(json.loads(contract_output.getvalue())["ok"])
            diff_output = io.StringIO()
            with contextlib.redirect_stdout(diff_output):
                self.assertEqual(main(["analyze", "diff", str(snapshot), str(snapshot)]), 0)
            summary = json.loads(diff_output.getvalue())["summary"]
            self.assertTrue(all(all(count == 0 for count in values.values()) for values in summary.values()))


class SemanticSyncTests(unittest.TestCase):
    def test_sync_rejects_v2_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            repo = temp / "repo"
            project = temp / "project"
            initialize_repo(repo)
            project.mkdir()
            (project / "diagram_model.json").write_text(json.dumps({"schemaVersion": "2.0"}), encoding="utf-8")
            (project / "source_model.json").write_text(json.dumps({}), encoding="utf-8")
            (project / "diagram_lock.json").write_text(json.dumps({}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "requires Diagram Model schemaVersion '3.0'"):
                sync_project(project, repo, dry_run=True)

    def test_dry_run_three_way_merge_and_confirmed_removal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            repo = temp / "repo"
            project = temp / "project"
            initialize_repo(repo)
            baseline = analyze_repository(repo)
            model = project_model(baseline)
            service_id = next(item["entityId"] for item in baseline["files"] if item["path"] == "pkg/service.py")
            util_id = next(item["entityId"] for item in baseline["files"] if item["path"] == "web/util.ts")
            service_record = next(item for item in model["semantics"]["entities"] if item["id"] == service_id)
            service_record["description"] = "Manual service description"
            service_view = next(item for item in model["presentation"]["entities"] if item["semanticId"] == service_id)
            service_view["layout"] = {"x": 320, "y": 180, "width": 240, "height": 120}
            first_edge = model["semantics"]["relationships"][0]
            first_edge["annotation"] = "Manual architecture note"
            first_edge_view = model["presentation"]["relationships"][0]
            first_edge_view["laneId"] = "manual-lane"
            source_model = {
                "schemaVersion": "2.0",
                "status": "confirmed",
                "sources": [baseline["source"]],
                "facts": baseline["facts"],
                "assumptions": [],
                "exclusions": [],
            }
            lock = {
                "schemaVersion": "2.0",
                "status": "confirmed",
                "viewIntent": "architecture",
                "route": {"family": "software", "profile": "c4-component"},
                "theme": "technical-editorial",
                "visualArchetype": "technical-editorial",
                "layoutStrategy": "layered",
                "sourceHash": sha256_json(source_model),
                "decisions": {
                    "audience": "developers",
                    "deliveryTarget": "engineering-doc",
                    "notation": "C4 component",
                    "layout": "layered",
                    "assetPolicy": "generic",
                },
            }
            project.mkdir()
            for name, value in (
                ("repository_snapshot.json", baseline),
                ("diagram_model.json", model),
                ("source_model.json", source_model),
                ("diagram_lock.json", lock),
            ):
                (project / name).write_text(json.dumps(value, indent=2), encoding="utf-8")

            write(repo / "pkg" / "service.py", (repo / "pkg" / "service.py").read_text(encoding="utf-8") + "\ndef health():\n    return True\n")
            write(repo / "pkg" / "new_worker.py", "def work():\n    return True\n")
            git(repo, "rm", "web/util.ts")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "evolve repository")

            tracked = [project / name for name in ("repository_snapshot.json", "diagram_model.json", "source_model.json", "diagram_lock.json")]
            before_hashes = {path.name: sha256_file(path) for path in tracked}
            dry_output = io.StringIO()
            with contextlib.redirect_stdout(dry_output):
                self.assertEqual(main(["sync", str(project), "--repo-root", str(repo), "--dry-run"]), 0)
            dry = json.loads(dry_output.getvalue())
            self.assertFalse(dry["projectModified"])
            self.assertEqual(before_hashes, {path.name: sha256_file(path) for path in tracked})
            self.assertGreater(dry["summary"]["conflicts"], 0)
            self.assertGreater(dry["summary"]["pendingRemovals"], 0)
            self.assertFalse([issue for issue in validate_sync_plan(dry) if issue.severity == "error"])

            applied = sync_project(project, repo, dry_run=False)
            self.assertTrue(applied["projectModified"])
            self.assertFalse(applied["complete"])
            merged = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
            merged_service = next(item for item in merged["semantics"]["entities"] if item["id"] == service_id)
            self.assertEqual(merged_service["description"], "Manual service description")
            self.assertEqual(
                next(item for item in merged["presentation"]["entities"] if item["semanticId"] == service_id)["layout"],
                {"x": 320, "y": 180, "width": 240, "height": 120},
            )
            self.assertEqual(merged["semantics"]["relationships"][0]["annotation"], "Manual architecture note")
            self.assertEqual(merged["presentation"]["relationships"][0]["laneId"], "manual-lane")
            self.assertIn(util_id, {item["id"] for item in merged["semantics"]["entities"]})
            self.assertTrue((project / "reports" / "repository_snapshot.candidate.json").is_file())

            candidate = json.loads((project / "reports" / "repository_snapshot.candidate.json").read_text(encoding="utf-8"))
            incoming_service = next(item for item in candidate["semanticProjection"]["entities"] if item["id"] == service_id)
            merged_service["description"] = incoming_service["description"]
            (project / "diagram_model.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
            pending_ids = {item["id"] for item in applied["pendingRemovals"]}
            final = sync_project(project, repo, dry_run=False, confirmed_removals=pending_ids)
            self.assertTrue(final["complete"])
            self.assertFalse((project / "reports" / "repository_snapshot.candidate.json").exists())
            final_model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
            self.assertNotIn(util_id, {item["id"] for item in final_model["semantics"]["entities"]})
            self.assertEqual(json.loads((project / "repository_snapshot.json").read_text(encoding="utf-8"))["fingerprint"], candidate["fingerprint"])
            final_source = json.loads((project / "source_model.json").read_text(encoding="utf-8"))
            final_lock = json.loads((project / "diagram_lock.json").read_text(encoding="utf-8"))
            self.assertFalse([issue for issue in validate_diagram_model(final_model) if issue.severity == "error"])
            self.assertFalse([issue for issue in validate_source_model(final_source) if issue.severity == "error"])
            self.assertFalse([issue for issue in validate_lock(final_lock) if issue.severity == "error"])
            self.assertFalse([issue for issue in verify_repository_evidence(final_source, repo) if issue.severity == "error"])
            self.assertEqual(final_lock["sourceHash"], sha256_json(final_source))


if __name__ == "__main__":
    unittest.main()

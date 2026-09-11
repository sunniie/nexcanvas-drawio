from __future__ import annotations

import contextlib
import io
import json
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from nexcanvas.builder import build_drawio as real_build_drawio
from nexcanvas.common import sha256_file
from nexcanvas.contracts import validate_project_state
from nexcanvas.cli import main
from nexcanvas.pipeline import STAGES, run_generate
from nexcanvas.model_v3 import migrate_v2_model
from nexcanvas.extensions import load_extensions


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "examples" / "v5-multi-agent-workflow"
EXTENSION_FIXTURE = ROOT / "tests" / "fixtures" / "extensions" / "complete"


def _png(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, data: bytes) -> bytes:
        checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)

    rows = b"".join(b"\x00" + b"\xff\xff\xff\xff" * width for _ in range(height))
    return (
        signature
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def _fake_render(source: Path, output: Path, fmt: str, scale: float, **_: object) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_png(2000, 1200))
    return {
        "schemaVersion": "2.0",
        "source": "artifacts/diagram.drawio",
        "output": "artifacts/diagram.drawio.png",
        "format": fmt,
        "scale": scale,
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "dimensions": {"width": 2000, "height": 1200},
        "renderer": "test-renderer",
        "command": ["test-renderer"],
    }


class PipelineTests(unittest.TestCase):
    def _project(self, directory: str) -> Path:
        project = Path(directory) / "project"
        shutil.copytree(REFERENCE, project)
        state = project / "project_state.json"
        if state.exists():
            state.unlink()
        return project

    def test_generate_stops_at_visual_review_then_completes_and_reuses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            with patch("nexcanvas.pipeline.render_drawio", side_effect=_fake_render):
                pending = run_generate(project)
                self.assertEqual(pending["outcome"], "awaiting-review")
                self.assertEqual(pending["exitCode"], 3)
                state = json.loads((project / "project_state.json").read_text(encoding="utf-8"))
                self.assertEqual(state["status"], "awaiting-review")
                self.assertEqual(state["stages"]["visual-qa"]["status"], "awaiting-review")
                self.assertEqual(state["stages"]["postflight"]["status"], "pending")

                complete = run_generate(
                    project,
                    approve_visual=True,
                    reviewer="pipeline-test",
                    notes="Inspected at target size and connector terminals at 200%.",
                )
                self.assertEqual(complete["outcome"], "complete")
                self.assertEqual(complete["exitCode"], 0)
                self.assertTrue(all(event["action"] == "reused" for event in complete["events"][:4]))
                self.assertFalse(any(event["action"] == "invalidated" for event in complete["events"]))

                before = json.loads((project / "project_state.json").read_text(encoding="utf-8"))
                reused = run_generate(project)
                after = json.loads((project / "project_state.json").read_text(encoding="utf-8"))
                self.assertEqual(reused["outcome"], "complete")
                self.assertTrue(all(event["action"] == "reused" for event in reused["events"]))
                self.assertEqual(
                    {name: before["stages"][name]["attempts"] for name in STAGES},
                    {name: after["stages"][name]["attempts"] for name in STAGES},
                )
                self.assertEqual(validate_project_state(after), [])

    def test_v3_model_runs_through_the_same_resumable_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            model_path = project / "diagram_model.json"
            source = json.loads((project / "source_model.json").read_text(encoding="utf-8"))
            legacy = json.loads(model_path.read_text(encoding="utf-8"))
            model_path.write_text(
                json.dumps(migrate_v2_model(legacy, source), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with patch("nexcanvas.pipeline.render_drawio", side_effect=_fake_render):
                pending = run_generate(project)
                complete = run_generate(
                    project,
                    approve_visual=True,
                    reviewer="pipeline-test",
                    notes="Inspected the V3 render at target size and connector terminals at 200%.",
                )
            self.assertEqual(pending["outcome"], "awaiting-review")
            self.assertEqual(complete["outcome"], "complete")
            drawio = (project / "artifacts" / "diagram.drawio").read_text(encoding="utf-8")
            self.assertIn('nc-model-schema-version="3.0"', drawio)
            self.assertIn("nc-semantic-hash=", drawio)

    def test_model_change_invalidates_every_downstream_delivery_stage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            with patch("nexcanvas.pipeline.render_drawio", side_effect=_fake_render):
                run_generate(project)
                run_generate(
                    project,
                    approve_visual=True,
                    reviewer="pipeline-test",
                    notes="Approved the current render after enlarged connector inspection.",
                )
                model_path = project / "diagram_model.json"
                model = json.loads(model_path.read_text(encoding="utf-8"))
                model["title"] = "Changed model title"
                model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")

                changed = run_generate(project)
                self.assertEqual(changed["outcome"], "awaiting-review")
                actions = {event["stage"]: event["action"] for event in changed["events"]}
                self.assertEqual(actions["plan"], "ran")
                self.assertEqual(actions["build"], "ran")
                self.assertEqual(actions["diagram-qa"], "ran")
                self.assertEqual(actions["render"], "ran")
                state = json.loads((project / "project_state.json").read_text(encoding="utf-8"))
                self.assertNotEqual(state["status"], "complete")
                self.assertNotEqual(state["stages"]["postflight"]["status"], "complete")

    def test_failed_stage_is_persisted_and_safe_to_resume(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            with patch("nexcanvas.pipeline.build_drawio", side_effect=RuntimeError("synthetic build failure")):
                failed = run_generate(project)
            self.assertEqual(failed["outcome"], "error")
            state = json.loads((project / "project_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stages"]["plan"]["status"], "complete")
            self.assertEqual(state["stages"]["build"]["status"], "failed")
            self.assertEqual(state["stages"]["build"]["attempts"], 1)

            with (
                patch("nexcanvas.pipeline.build_drawio", side_effect=real_build_drawio),
                patch("nexcanvas.pipeline.render_drawio", side_effect=_fake_render),
            ):
                resumed = run_generate(project)
            self.assertEqual(resumed["outcome"], "awaiting-review")
            self.assertEqual(resumed["events"][0], {"stage": "plan", "action": "reused", "status": "complete"})
            state = json.loads((project / "project_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stages"]["build"]["attempts"], 2)

    def test_tampered_preview_invalidates_render_approval_and_postflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            with patch("nexcanvas.pipeline.render_drawio", side_effect=_fake_render):
                run_generate(project)
                run_generate(
                    project,
                    approve_visual=True,
                    reviewer="pipeline-test",
                    notes="Approved after inspecting target size and enlarged connector terminals.",
                )
                preview = project / "artifacts" / "diagram.drawio.png"
                preview.write_bytes(preview.read_bytes() + b"tampered")
                result = run_generate(project)

            self.assertEqual(result["outcome"], "awaiting-review")
            invalidated = [event["stage"] for event in result["events"] if event["action"] == "invalidated"]
            self.assertIn("render", invalidated)
            state = json.loads((project / "project_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stages"]["visual-qa"]["status"], "awaiting-review")
            self.assertNotEqual(state["stages"]["postflight"]["status"], "complete")

    def test_complete_state_cannot_claim_pending_visual_stage(self) -> None:
        state = {
            "schemaVersion": "1.0",
            "pipelineVersion": "0.3.0",
            "projectRoot": ".",
            "status": "complete",
            "stages": {name: {"status": "pending", "attempts": 0} for name in STAGES},
        }
        issues = validate_project_state(state)
        self.assertIn("pipeline-false-complete", {issue.code for issue in issues})

    def test_generate_cli_emits_machine_readable_review_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            output = io.StringIO()
            with (
                patch("nexcanvas.pipeline.render_drawio", side_effect=_fake_render),
                contextlib.redirect_stdout(output),
            ):
                code = main(["generate", str(project)])
            result = json.loads(output.getvalue())
            self.assertEqual(code, 3)
            self.assertEqual(result["exitCode"], 3)
            self.assertEqual(result["outcome"], "awaiting-review")
            self.assertFalse(result["complete"])

    def test_extension_content_change_invalidates_build_and_downstream_stages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            extension_root = Path(directory) / "extension"
            shutil.copytree(EXTENSION_FIXTURE, extension_root)
            extensions = load_extensions([extension_root])
            with patch("nexcanvas.pipeline.render_drawio", side_effect=_fake_render):
                run_generate(project, extensions=extensions)
                run_generate(
                    project,
                    approve_visual=True,
                    reviewer="pipeline-test",
                    notes="Approved extension-backed render after enlarged inspection.",
                    extensions=extensions,
                )
                hook = extension_root / "hook.py"
                hook.write_text(hook.read_text(encoding="utf-8") + "\n# extension revision\n", encoding="utf-8")
                changed = run_generate(project, extensions=load_extensions([extension_root]))
            self.assertIn({"stage": "plan", "action": "reused", "status": "complete"}, changed["events"])
            self.assertTrue(
                any(event["stage"] == "build" and event["action"] == "invalidated" for event in changed["events"])
            )
            self.assertEqual(changed["outcome"], "awaiting-review")


if __name__ == "__main__":
    unittest.main()

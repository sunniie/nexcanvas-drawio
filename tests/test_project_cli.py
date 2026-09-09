from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexcanvas.project import init_project


def init_args(*, project_root: Path | None, output_root: Path, name: str = "My Architecture", brief: str = "", family: str | None = "software", profile: str | None = "c4-context") -> argparse.Namespace:
    return argparse.Namespace(
        project_root=project_root,
        output_root=output_root,
        name=name,
        family=family,
        profile=profile,
        brief=brief,
        view_intent="auto",
        theme="technical-editorial",
        visual_archetype="technical-editorial",
        audience="engineering stakeholders",
        delivery_target="engineering-doc",
        language="en",
        direction="LR",
        width=1600,
        height=900,
        force=False,
    )


class ProjectInitializationTests(unittest.TestCase):
    def test_omitted_project_root_uses_standard_output_folder_and_slug(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory) / "nexcanvas-output"
            result = init_project(init_args(project_root=None, output_root=output_root))

            expected = (output_root / "my-architecture").resolve()
            self.assertEqual(Path(result["projectRoot"]), expected)
            self.assertTrue(result["usedDefaultOutput"])
            self.assertTrue((expected / "diagram_model.json").is_file())
            self.assertTrue((expected / "artifacts").is_dir())
            self.assertTrue((expected / "reports" / "runtime.json").is_file())
            model = json.loads((expected / "diagram_model.json").read_text(encoding="utf-8"))
            self.assertFalse(model["showTitle"])
            self.assertNotIn("subtitle", model)
            self.assertFalse((expected / "assets" / "icons").exists())

    def test_brief_first_initialization_infers_lifecycle_and_route(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory) / "nexcanvas-output"
            result = init_project(
                init_args(
                    project_root=None,
                    output_root=output_root,
                    name="Order run",
                    brief="Vẽ vòng đời trạng thái order, retry và cancelled",
                    family=None,
                    profile=None,
                )
            )
            project = Path(result["projectRoot"])
            model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
            lock = json.loads((project / "diagram_lock.json").read_text(encoding="utf-8"))
            source = json.loads((project / "source_model.json").read_text(encoding="utf-8"))
            self.assertEqual(model["viewIntent"], "lifecycle")
            self.assertEqual(model["route"], {"family": "behavior", "profile": "state-machine"})
            self.assertEqual(lock["viewIntent"], "lifecycle")
            self.assertEqual(source["facts"][0]["id"], "fact-brief")

    def test_explicit_project_root_takes_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            explicit = base / "chosen-project"
            result = init_project(
                init_args(project_root=explicit, output_root=base / "ignored-output-root")
            )

            self.assertEqual(Path(result["projectRoot"]), explicit.resolve())
            self.assertFalse(result["usedDefaultOutput"])
            self.assertFalse((base / "ignored-output-root").exists())


if __name__ == "__main__":
    unittest.main()

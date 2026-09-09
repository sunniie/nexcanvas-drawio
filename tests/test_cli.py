from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexcanvas.cli import build_parser, main


class UnifiedCliTests(unittest.TestCase):
    def test_required_public_commands_are_registered(self) -> None:
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        )
        self.assertTrue(
            {"doctor", "init", "analyze", "plan", "build", "render", "qa", "postflight", "generate"}.issubset(
                subparsers.choices
            )
        )

    def test_init_uses_callers_working_directory(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                outside = Path(directory)
                os.chdir(outside)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = main(
                        [
                            "init",
                            "--name",
                            "Outside repo",
                            "--brief",
                            "Show the deployment architecture",
                            "--language",
                            "en",
                        ]
                    )
                result = json.loads(output.getvalue())
                self.assertEqual(code, 0)
                self.assertEqual(
                    Path(result["projectRoot"]),
                    (outside / "nexcanvas-output" / "outside-repo").resolve(),
                )
            finally:
                os.chdir(previous)

    def test_doctor_resolves_distribution_data_without_using_cwd(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = main(["doctor"])
                report = json.loads(output.getvalue())
                self.assertEqual(code, 0)
                self.assertTrue(Path(report["skillRoot"]).is_absolute())
                self.assertNotEqual(Path(report["skillRoot"]), Path(directory).resolve())
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()

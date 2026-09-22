#!/usr/bin/env python3
"""Build and smoke-test the wheel from a working directory outside the repo."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        rendered = " ".join(command)
        raise RuntimeError(
            f"Command failed with exit {result.returncode}: {rendered}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _venv_command(root: Path) -> Path:
    return root / ("Scripts/nexcanvas.exe" if os.name == "nt" else "bin/nexcanvas")


def _assert_cli(environment: Path, outside: Path) -> tuple[str, dict[str, object]]:
    python = _venv_python(environment)
    command = _venv_command(environment)
    version = _run([str(command), "--version"], outside).stdout.strip()
    module_version = _run([str(python), "-m", "nexcanvas", "--version"], outside).stdout.strip()
    if version != module_version:
        raise RuntimeError("Console entry point and python -m nexcanvas resolve differently.")
    doctor = json.loads(_run([str(command), "doctor"], outside).stdout)
    catalog = json.loads(
        _run([str(command), "asset", "search", "postgresql", "--limit", "1"], outside).stdout
    )
    _run([str(command), "generate", "--help"], outside)
    _run([str(command), "analyze", "snapshot", "--help"], outside)
    _run([str(command), "analyze", "diff", "--help"], outside)
    _run([str(command), "sync", "--help"], outside)
    conformance = json.loads(_run([str(command), "conformance", "doctor"], outside).stdout)
    _run([str(command), "conformance", "prepare", "--help"], outside)
    _run([str(command), "conformance", "evaluate", "--help"], outside)
    _run([str(command), "conformance", "report", "--no-discovery"], outside)
    benchmark = json.loads(_run([str(command), "benchmark", "validate"], outside).stdout)
    _run([str(command), "extension", "validate", "--help"], outside)
    compatibility = json.loads(_run([str(command), "compatibility", "report"], outside).stdout)
    if not doctor["capabilities"]["authorNativeDrawio"] or catalog["count"] != 1:
        raise RuntimeError("Installed runtime data or core capability checks failed.")
    if len(conformance.get("hosts", [])) < 4:
        raise RuntimeError("Installed runtime is missing conformance host adapters.")
    if benchmark.get("cases") != 7:
        raise RuntimeError("Installed runtime is missing the seven-class visual benchmark suite.")
    if compatibility.get("contractSet") != "1.0" or compatibility.get("cli", {}).get("commandCount") != 28:
        raise RuntimeError("Installed runtime is missing the stable 1.0 contract set.")
    return version, doctor


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nexcanvas-package-") as directory:
        temp = Path(directory)
        wheelhouse = temp / "wheelhouse"
        wheelhouse.mkdir()
        _run(
            [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--wheel-dir", str(wheelhouse)],
            ROOT,
        )
        wheels = list(wheelhouse.glob("nexcanvas_drawio-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"Expected one NexCanvas wheel, found: {wheels}")

        outside = temp / "outside-repository"
        outside.mkdir()

        editable_environment = temp / "editable-venv"
        venv.EnvBuilder(with_pip=True).create(editable_environment)
        editable_python = _venv_python(editable_environment)
        _run([str(editable_python), "-m", "pip", "install", "--no-deps", "-e", str(ROOT)], temp)
        editable_version, editable_doctor = _assert_cli(editable_environment, outside)

        environment = temp / "wheel-venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = _venv_python(environment)
        _run([str(python), "-m", "pip", "install", "--no-deps", str(wheels[0])], temp)
        version, doctor = _assert_cli(environment, outside)
        initialized = json.loads(
            _run(
                [
                    str(python),
                    "-m",
                    "nexcanvas",
                    "init",
                    "--name",
                    "Packaged smoke",
                    "--brief",
                    "Trace one API request through a service",
                    "--language",
                    "en",
                ],
                outside,
            ).stdout
        )
        project = Path(initialized["projectRoot"])
        required = [
            project / "source_model.json",
            project / "diagram_model.json",
            project / "diagram_lock.json",
            project / "project_state.json",
            project / "assets" / "asset_manifest.json",
            project / "reports" / "runtime.json",
        ]
        if not all(path.is_file() for path in required):
            raise RuntimeError("Packaged CLI did not create the standard project contract set.")
        initialized_model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        if initialized_model.get("schemaVersion") != "3.0":
            raise RuntimeError("Packaged CLI did not initialize the canonical diagram model V3 contract.")
        provenance = [{"factId": "fact-brief", "confidence": "confirmed"}]
        initialized_model["semantics"]["entities"].append(
            {"id": "worker", "label": "Worker", "kind": "service", "provenance": provenance}
        )
        initialized_model["semantics"]["relationships"].append(
            {
                "id": "request",
                "source": "system",
                "target": "worker",
                "kind": "request",
                "label": "Dispatch request",
                "provenance": provenance,
            }
        )
        initialized_model["presentation"]["entities"].append(
            {"semanticId": "worker", "presentation": "service-icon", "importance": "secondary"}
        )
        initialized_model["presentation"]["relationships"].append(
            {
                "semanticId": "request",
                "labelMode": "offset",
                "lineClass": "control",
                "importance": "primary",
                "step": 1,
                "layout": {"order": 1},
            }
        )
        (project / "diagram_model.json").write_text(
            json.dumps(initialized_model, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        model_contract = json.loads(
            _run(
                [str(_venv_command(environment)), "contract", "diagram-model", str(project / "diagram_model.json")],
                outside,
            ).stdout
        )
        if not model_contract["ok"]:
            raise RuntimeError("Packaged CLI created an invalid canonical diagram model V3 contract.")
        _run([str(_venv_command(environment)), "migrate", "v2-to-v3", "--help"], outside)
        state_contract = json.loads(
            _run(
                [str(_venv_command(environment)), "contract", "project-state", str(project / "project_state.json")],
                outside,
            ).stdout
        )
        if not state_contract["ok"]:
            raise RuntimeError("Packaged CLI created an invalid project pipeline state contract.")
        command = _venv_command(environment)
        layout_report = project / "reports" / "layout-brainstorm.json"
        drawio = project / "artifacts" / "diagram.drawio"
        build_report = project / "reports" / "build.json"
        qa_report = project / "reports" / "diagram_qa.json"
        _run([str(command), "plan", str(project / "diagram_model.json"), "--output", str(layout_report)], outside)
        _run(
            [
                str(command),
                "build",
                str(project / "diagram_model.json"),
                "--output",
                str(drawio),
                "--project-root",
                str(project),
                "--proof",
                str(build_report),
            ],
            outside,
        )
        _run(
            [
                str(command),
                "qa",
                "diagram",
                str(project / "diagram_model.json"),
                "--source-model",
                str(project / "source_model.json"),
                "--drawio",
                str(drawio),
                "--project-root",
                str(project),
                "--output",
                str(qa_report),
            ],
            outside,
        )
        compatibility = json.loads(
            _run([str(command), "compatibility", "check", str(project)], outside).stdout
        )
        if not compatibility.get("compatible") or compatibility.get("modified") is not False:
            raise RuntimeError("Packaged project compatibility check failed or modified the project.")
        for output in (layout_report, drawio, build_report, qa_report):
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"Fresh-install structural E2E did not create {output.name}.")
        for schema in (
            "repository-snapshot.schema.json",
            "semantic-sync-plan.schema.json",
            "conformance-suite.schema.json",
            "host-adapter.schema.json",
            "conformance-execution.schema.json",
            "conformance-result.schema.json",
            "extension-manifest.schema.json",
            "visual-benchmark-suite.schema.json",
            "visual-benchmark-result.schema.json",
            "diagram-qa.schema.json",
            "visual-qa.schema.json",
            "postflight.schema.json",
            "stability-manifest.schema.json",
        ):
            if not (Path(doctor["skillRoot"]) / "schemas" / schema).is_file():
                raise RuntimeError(f"Packaged runtime is missing {schema}.")
        print(
            json.dumps(
                {
                    "ok": True,
                    "version": version,
                    "editableVersion": editable_version,
                    "wheel": wheels[0].name,
                    "workingDirectoryIndependent": True,
                    "resourceRoot": doctor["skillRoot"],
                    "editableResourceRoot": editable_doctor["skillRoot"],
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

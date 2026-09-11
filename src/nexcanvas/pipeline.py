from __future__ import annotations

import subprocess
import traceback
from pathlib import Path
from typing import Any

from . import __version__
from .assets import load_manifest
from .builder import build_drawio
from .common import load_json, safe_project_path, sha256_file, sha256_json, utc_now, write_json
from .contracts import validate_project_state
from .extensions import ExtensionSet
from .geometry import run_checks as run_geometry_checks
from .model_v3 import normalize_diagram_model
from .planning import brainstorm_layout
from .postflight import run_postflight
from .quality import run_quality, summarize
from .registry import resolve_route
from .rendering import render_drawio
from .visual import create_visual_report


STATE_SCHEMA_VERSION = "1.0"
STAGES = ("plan", "build", "diagram-qa", "render", "visual-qa", "postflight")
DEPENDENCIES = {
    "plan": (),
    "build": ("plan",),
    "diagram-qa": ("build",),
    "render": ("diagram-qa",),
    "visual-qa": ("render",),
    "postflight": ("visual-qa",),
}


def _new_stage() -> dict[str, Any]:
    return {"status": "pending", "attempts": 0}


def new_project_state() -> dict[str, Any]:
    return {
        "schemaVersion": STATE_SCHEMA_VERSION,
        "pipelineVersion": __version__,
        "projectRoot": ".",
        "status": "pending",
        "currentStage": None,
        "updatedAt": utc_now(),
        "stages": {name: _new_stage() for name in STAGES},
    }


def initialize_project_state(project_root: Path, *, replace: bool = False) -> dict[str, Any]:
    path = project_root.resolve() / "project_state.json"
    if path.is_file() and not replace:
        return load_project_state(project_root)
    state = new_project_state()
    write_json(path, state)
    return state


def load_project_state(project_root: Path) -> dict[str, Any]:
    path = project_root.resolve() / "project_state.json"
    if not path.is_file():
        return initialize_project_state(project_root)
    state = load_json(path)
    if not isinstance(state, dict):
        raise ValueError("project_state.json must contain a JSON object")
    if state.get("schemaVersion") != STATE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported project_state schemaVersion {state.get('schemaVersion')!r}; "
            f"expected {STATE_SCHEMA_VERSION!r}."
        )
    stages = state.setdefault("stages", {})
    if not isinstance(stages, dict):
        raise ValueError("project_state.stages must be an object")
    for name in STAGES:
        record = stages.setdefault(name, _new_stage())
        if not isinstance(record, dict):
            raise ValueError(f"project_state.stages.{name} must be an object")
        record.setdefault("status", "pending")
        record.setdefault("attempts", 0)
    state["pipelineVersion"] = __version__
    state["projectRoot"] = "."
    issues = validate_project_state(state)
    if issues:
        details = "; ".join(f"{issue.location}: {issue.message}" for issue in issues)
        raise ValueError(f"Invalid project_state.json: {details}")
    return state


def _save_state(project_root: Path, state: dict[str, Any]) -> None:
    state["updatedAt"] = utc_now()
    write_json(project_root / "project_state.json", state)


def _effective_asset_input(project_root: Path) -> dict[str, Any]:
    manifest_path = project_root / "assets" / "asset_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Required pipeline input is missing: assets/asset_manifest.json")
    manifest = load_manifest(project_root)
    assets: list[dict[str, Any]] = []
    for item in manifest.get("assets", []):
        if not isinstance(item, dict):
            continue
        local_path = str(item.get("localPath", ""))
        actual_hash: str | None = None
        if local_path:
            try:
                asset_path = safe_project_path(project_root, local_path)
                actual_hash = sha256_file(asset_path) if asset_path.is_file() else "missing"
            except ValueError:
                actual_hash = "outside-project"
        assets.append(
            {
                "key": item.get("key"),
                "provider": item.get("provider"),
                "version": item.get("version"),
                "sourceUrl": item.get("sourceUrl"),
                "localPath": local_path,
                "declaredSha256": item.get("sha256"),
                "actualSha256": actual_hash,
                "needsManual": item.get("state") == "NeedsManual",
            }
        )
    return {"catalogVersion": manifest.get("catalogVersion"), "assets": assets}


def _required_hash(project_root: Path, relative: str) -> str:
    path = safe_project_path(project_root, relative)
    if not path.is_file():
        raise FileNotFoundError(f"Required pipeline input is missing: {relative}")
    return sha256_file(path)


def _repository_context_hash(project_root: Path, repo_root: Path | None) -> str | None:
    source_model = load_json(project_root / "source_model.json")
    revisions = sorted(
        str(source.get("repository", {}).get("revision", ""))
        for source in source_model.get("sources", [])
        if isinstance(source, dict) and source.get("type") == "repository"
    )
    if not revisions:
        return None
    if repo_root is None:
        return sha256_json({"available": False, "reason": "repo-root-not-supplied", "revisions": revisions})

    def git(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repo_root.resolve()), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            raise ValueError(completed.stderr.strip() or completed.stdout.strip() or "git command failed")
        return completed.stdout.strip()

    try:
        origin = git("remote", "get-url", "origin").replace("\\", "/").removesuffix(".git").rstrip("/").lower()
        resolved = {revision: git("rev-parse", f"{revision}^{{commit}}") for revision in revisions}
        return sha256_json({"available": True, "origin": origin, "revisions": resolved})
    except (OSError, ValueError) as exc:
        return sha256_json(
            {"available": False, "reason": type(exc).__name__, "message": str(exc), "revisions": revisions}
        )


def _input_descriptor(
    stage: str,
    project_root: Path,
    state: dict[str, Any],
    options: dict[str, Any],
) -> tuple[str, dict[str, str], dict[str, str]]:
    file_inputs: dict[str, str] = {}
    virtual_inputs: dict[str, str] = {
        "pipelineVersion": sha256_json(__version__),
    }
    extensions: ExtensionSet = options["extensions"]
    if stage != "plan":
        virtual_inputs["extensions"] = extensions.fingerprint()
    required: tuple[str, ...]
    if stage == "plan":
        required = ("diagram_model.json",)
    elif stage == "build":
        required = ("diagram_model.json",)
        virtual_inputs["effectiveAssets"] = sha256_json(_effective_asset_input(project_root))
    elif stage == "diagram-qa":
        required = (
            "source_model.json",
            "diagram_lock.json",
            "diagram_model.json",
            "artifacts/diagram.drawio",
        )
        virtual_inputs["effectiveAssets"] = sha256_json(_effective_asset_input(project_root))
        virtual_inputs["qaOptions"] = sha256_json(
            {
                "padding": options["padding"],
                "failOnWarning": options["failOnWarning"],
                "repositoryContext": _repository_context_hash(project_root, options.get("repoRoot")),
            }
        )
    elif stage == "render":
        required = ("artifacts/diagram.drawio",)
        virtual_inputs["renderOptions"] = sha256_json(
            {"format": options["renderFormat"], "scale": options["scale"]}
        )
    elif stage == "visual-qa":
        required = (options["previewRelative"],)
        virtual_inputs["visualTarget"] = sha256_json(
            {
                "expectedWidth": options["expectedWidth"],
                "expectedHeight": options["expectedHeight"],
            }
        )
    elif stage == "postflight":
        required = (
            "source_model.json",
            "diagram_lock.json",
            "diagram_model.json",
            "artifacts/diagram.drawio",
            "reports/diagram_qa.json",
            "reports/visual_qa.json",
        )
        virtual_inputs["effectiveAssets"] = sha256_json(_effective_asset_input(project_root))
        virtual_inputs["repositoryContext"] = sha256_json(
            _repository_context_hash(project_root, options.get("repoRoot"))
        )
    else:
        raise ValueError(f"Unknown pipeline stage: {stage}")

    for relative in required:
        file_inputs[relative] = _required_hash(project_root, relative)
    inputs = {**file_inputs, **{f"@{key}": value for key, value in virtual_inputs.items()}}
    dependency_hashes: dict[str, str] = {}
    for dependency in DEPENDENCIES[stage]:
        record = state["stages"][dependency]
        output_hash = record.get("outputHash")
        if record.get("status") != "complete" or not isinstance(output_hash, str):
            raise RuntimeError(f"Pipeline dependency {dependency!r} is not complete for {stage!r}.")
        dependency_hashes[dependency] = output_hash
    fingerprint = sha256_json(
        {"stage": stage, "inputs": inputs, "dependencies": dependency_hashes}
    )
    return fingerprint, inputs, dependency_hashes


def _output_relatives(stage: str, options: dict[str, Any]) -> tuple[str, ...]:
    return {
        "plan": ("reports/layout_brainstorm.json",),
        "build": ("artifacts/diagram.drawio", "reports/build.json"),
        "diagram-qa": ("reports/diagram_qa.json",),
        "render": (options["previewRelative"], "reports/render.json"),
        "visual-qa": ("reports/visual_qa.json",),
        "postflight": ("reports/postflight.json",),
    }[stage]


def _collect_outputs(stage: str, project_root: Path, options: dict[str, Any]) -> dict[str, dict[str, Any]]:
    outputs: dict[str, dict[str, Any]] = {}
    for relative in _output_relatives(stage, options):
        path = safe_project_path(project_root, relative)
        if path.is_file():
            outputs[relative] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    return outputs


def _outputs_match(
    record: dict[str, Any],
    project_root: Path,
    stage: str,
    options: dict[str, Any],
) -> bool:
    outputs = record.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        return False
    if set(outputs) != set(_output_relatives(stage, options)):
        return False
    for relative, metadata in outputs.items():
        if not isinstance(relative, str) or not isinstance(metadata, dict):
            return False
        try:
            path = safe_project_path(project_root, relative)
        except ValueError:
            return False
        if not path.is_file() or metadata.get("sha256") != sha256_file(path):
            return False
    return True


def _invalidate_from(state: dict[str, Any], stage_index: int, reason: str) -> None:
    for name in STAGES[stage_index:]:
        record = state["stages"][name]
        if record.get("status") != "pending" or name == STAGES[stage_index]:
            record["status"] = "stale"
            record["invalidatedAt"] = utc_now()
            record["invalidationReason"] = reason
        for key in (
            "inputHash",
            "inputs",
            "dependencies",
            "outputs",
            "outputHash",
            "result",
            "error",
            "startedAt",
            "completedAt",
        ):
            record.pop(key, None)


def _run_stage(
    stage: str,
    project_root: Path,
    options: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    model_path = project_root / "diagram_model.json"
    if stage == "plan":
        report = brainstorm_layout(load_json(model_path))
        write_json(project_root / "reports" / "layout_brainstorm.json", report)
        return "complete", {"ok": True, "winner": report.get("winner")}

    if stage == "build":
        result = build_drawio(
            model_path,
            project_root / "artifacts" / "diagram.drawio",
            project_root=project_root,
            extensions=options["extensions"],
        )
        write_json(project_root / "reports" / "build.json", result)
        return "complete", {"ok": True, "nodes": result["nodes"], "edges": result["edges"]}

    if stage == "diagram-qa":
        canonical_model = load_json(model_path)
        model = normalize_diagram_model(canonical_model)
        drawio = project_root / "artifacts" / "diagram.drawio"
        issues = run_quality(
            canonical_model,
            load_json(project_root / "source_model.json"),
            project_root,
            drawio,
            repo_root=options.get("repoRoot"),
            extensions=options["extensions"],
        )
        report = summarize(issues)
        report["schemaVersion"] = "2.0"
        report["checkedAt"] = utc_now()
        route = resolve_route(
            model["route"]["family"], model["route"]["profile"], extensions=options["extensions"]
        )
        errors, warnings = run_geometry_checks(drawio, options["padding"], str(route["geometryQa"]))
        report["geometry"] = {"profile": route["geometryQa"], "errors": errors, "warnings": warnings}
        report["counts"]["error"] += len(errors)
        report["counts"]["warning"] += len(warnings)
        report["ok"] = report["counts"]["error"] == 0
        write_json(project_root / "reports" / "diagram_qa.json", report)
        gate_ok = report["ok"] and not (
            options["failOnWarning"] and report["counts"]["warning"] > 0
        )
        return ("complete" if gate_ok else "failed"), {
            "ok": gate_ok,
            "counts": report["counts"],
            "failOnWarning": options["failOnWarning"],
        }

    if stage == "render":
        result = render_drawio(
            project_root / "artifacts" / "diagram.drawio",
            project_root / options["previewRelative"],
            options["renderFormat"],
            options["scale"],
            report_root=project_root,
        )
        write_json(project_root / "reports" / "render.json", result)
        return "complete", {"ok": True, "artifact": result["output"], "sha256": result["sha256"]}

    if stage == "visual-qa":
        report = create_visual_report(
            project_root / options["previewRelative"],
            options["expectedWidth"],
            options["expectedHeight"],
            options["approveVisual"],
            options["reviewer"],
            options["notes"],
            project_root,
        )
        write_json(project_root / "reports" / "visual_qa.json", report)
        if not options["approveVisual"]:
            return "awaiting-review", {
                "ok": False,
                "artifact": report["artifact"],
                "manualReview": "pending-review",
            }
        return ("complete" if report["ok"] else "failed"), {
            "ok": report["ok"],
            "artifact": report["artifact"],
            "manualReview": report["manualReview"]["status"],
        }

    if stage == "postflight":
        report = run_postflight(
            project_root, repo_root=options.get("repoRoot"), extensions=options["extensions"]
        )
        write_json(project_root / "reports" / "postflight.json", report)
        return ("complete" if report["ok"] else "failed"), {
            "ok": report["ok"],
            "counts": report["counts"],
        }

    raise ValueError(f"Unknown pipeline stage: {stage}")


def _result(
    project_root: Path,
    state: dict[str, Any],
    events: list[dict[str, Any]],
    *,
    outcome: str,
    exit_code: int,
    next_action: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schemaVersion": STATE_SCHEMA_VERSION,
        "ok": outcome == "complete",
        "complete": outcome == "complete",
        "outcome": outcome,
        "exitCode": exit_code,
        "projectRoot": str(project_root),
        "state": "project_state.json",
        "currentStage": state.get("currentStage"),
        "events": events,
    }
    if next_action:
        value["nextAction"] = next_action
    return value


def run_generate(
    project_root: Path,
    *,
    repo_root: Path | None = None,
    render_format: str = "png",
    scale: float = 1.0,
    expected_width: int | None = None,
    expected_height: int | None = None,
    approve_visual: bool = False,
    reviewer: str = "",
    notes: str = "",
    padding: float = 10.0,
    fail_on_warning: bool = True,
    restart: bool = False,
    extensions: ExtensionSet | None = None,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    if render_format not in {"png", "svg", "pdf"}:
        raise ValueError(f"Unsupported render format: {render_format}")
    if approve_visual and (not reviewer.strip() or not notes.strip()):
        raise ValueError("--approve-visual requires non-empty --reviewer and --notes values.")
    if scale <= 0:
        raise ValueError("--scale must be greater than zero.")
    if padding < 0:
        raise ValueError("--padding must be zero or greater.")
    if bool(expected_width) != bool(expected_height):
        raise ValueError("--expected-width and --expected-height must be supplied together.")
    if expected_width is not None and (expected_width <= 0 or expected_height is None or expected_height <= 0):
        raise ValueError("Expected visual dimensions must be greater than zero.")
    model = normalize_diagram_model(load_json(project_root / "diagram_model.json"))
    canvas = model.get("canvas") if isinstance(model, dict) else {}
    width = expected_width or int(canvas.get("width", 0) or 0) or None
    height = expected_height or int(canvas.get("height", 0) or 0) or None
    preview_relative = f"artifacts/diagram.drawio.{render_format}"
    options: dict[str, Any] = {
        "repoRoot": repo_root.resolve() if repo_root else None,
        "renderFormat": render_format,
        "scale": scale,
        "expectedWidth": width,
        "expectedHeight": height,
        "approveVisual": approve_visual,
        "reviewer": reviewer,
        "notes": notes,
        "padding": padding,
        "failOnWarning": fail_on_warning,
        "previewRelative": preview_relative,
        "extensions": extensions or ExtensionSet.empty(),
    }
    state = load_project_state(project_root)
    events: list[dict[str, Any]] = []
    if restart:
        _invalidate_from(state, 0, "Explicit pipeline restart requested.")
        state["status"] = "pending"
        state["currentStage"] = None
        _save_state(project_root, state)
        events.append({"stage": "pipeline", "action": "restarted", "status": "pending"})

    for index, stage in enumerate(STAGES):
        state["currentStage"] = stage
        record = state["stages"][stage]
        try:
            input_hash, inputs, dependencies = _input_descriptor(stage, project_root, state, options)
        except Exception as exc:
            record["status"] = "failed"
            record["attempts"] = int(record.get("attempts", 0)) + 1
            record["error"] = {"type": type(exc).__name__, "message": str(exc)}
            record["completedAt"] = utc_now()
            state["status"] = "failed"
            _save_state(project_root, state)
            events.append({"stage": stage, "action": "failed", "status": "failed"})
            return _result(project_root, state, events, outcome="error", exit_code=2)

        current = (
            record.get("status") in {"complete", "awaiting-review"}
            and record.get("inputHash") == input_hash
            and _outputs_match(record, project_root, stage, options)
        )
        promote_review = stage == "visual-qa" and record.get("status") == "awaiting-review" and approve_visual
        if current and not promote_review:
            events.append({"stage": stage, "action": "reused", "status": record["status"]})
            if record["status"] == "awaiting-review":
                state["status"] = "awaiting-review"
                _save_state(project_root, state)
                return _result(
                    project_root,
                    state,
                    events,
                    outcome="awaiting-review",
                    exit_code=3,
                    next_action=(
                        f"Inspect {preview_relative}, then rerun generate with --approve-visual, "
                        "--reviewer, and --notes."
                    ),
                )
            continue

        if record.get("status") in {"complete", "awaiting-review"} and not promote_review:
            reason = (
                "Stage inputs or dependencies changed."
                if record.get("inputHash") != input_hash
                else "A generated output is missing or its hash changed."
            )
            _invalidate_from(state, index, reason)
            record = state["stages"][stage]
            events.append({"stage": stage, "action": "invalidated", "status": "stale", "reason": reason})

        record["status"] = "running"
        record["attempts"] = int(record.get("attempts", 0)) + 1
        record["inputHash"] = input_hash
        record["inputs"] = inputs
        record["dependencies"] = dependencies
        record["startedAt"] = utc_now()
        record.pop("error", None)
        state["status"] = "running"
        _save_state(project_root, state)
        try:
            stage_status, summary = _run_stage(stage, project_root, options)
            # Asset lifecycle states may advance during build or postflight. The
            # effective asset fingerprint intentionally ignores those equivalent
            # transitions, but recomputing here records the exact final inputs.
            final_input_hash, final_inputs, final_dependencies = _input_descriptor(
                stage, project_root, state, options
            )
            outputs = _collect_outputs(stage, project_root, options)
            record["inputHash"] = final_input_hash
            record["inputs"] = final_inputs
            record["dependencies"] = final_dependencies
            record["outputs"] = outputs
            record["outputHash"] = sha256_json(outputs)
            record["result"] = summary
            record["status"] = stage_status
            record["completedAt"] = utc_now()
            record.pop("invalidationReason", None)
            record.pop("invalidatedAt", None)
            events.append({"stage": stage, "action": "ran", "status": stage_status})
            if stage_status == "awaiting-review":
                state["status"] = "awaiting-review"
                _save_state(project_root, state)
                return _result(
                    project_root,
                    state,
                    events,
                    outcome="awaiting-review",
                    exit_code=3,
                    next_action=(
                        f"Inspect {preview_relative}, then rerun generate with --approve-visual, "
                        "--reviewer, and --notes."
                    ),
                )
            if stage_status == "failed":
                state["status"] = "failed"
                _invalidate_from(state, index + 1, f"Upstream stage {stage!r} failed.")
                state["stages"][stage]["status"] = "failed"
                _save_state(project_root, state)
                return _result(project_root, state, events, outcome="failed-gate", exit_code=1)
            _save_state(project_root, state)
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "detail": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
            }
            record["outputs"] = _collect_outputs(stage, project_root, options)
            record["completedAt"] = utc_now()
            state["status"] = "failed"
            _invalidate_from(state, index + 1, f"Upstream stage {stage!r} raised an error.")
            _save_state(project_root, state)
            events.append({"stage": stage, "action": "failed", "status": "failed"})
            return _result(project_root, state, events, outcome="error", exit_code=2)

    state["status"] = "complete"
    state["currentStage"] = None
    state["completedAt"] = utc_now()
    _save_state(project_root, state)
    return _result(project_root, state, events, outcome="complete", exit_code=0)

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .assets import load_manifest, mark_assets
from .common import load_json, portable_path, sha256_file, sha256_json, utc_now
from .contracts import Issue, validate_lock, validate_manifest, validate_source_model
from .intents import resolve_view_intent
from .quality import validate_drawio_metadata
from .repository import verify_repository_evidence


def run_postflight(project_root: Path, root: Path | None = None, repo_root: Path | None = None) -> dict[str, Any]:
    paths = {
        "source": project_root / "source_model.json",
        "lock": project_root / "diagram_lock.json",
        "model": project_root / "diagram_model.json",
        "drawio": project_root / "artifacts" / "diagram.drawio",
        "qa": project_root / "reports" / "diagram_qa.json",
        "visual": project_root / "reports" / "visual_qa.json",
        "manifest": project_root / "assets" / "asset_manifest.json",
    }
    issues: list[Issue] = []
    for name, path in paths.items():
        if not path.is_file():
            issues.append(Issue("error", "artifact-missing", f"Required {name} artifact is missing: {path.name}.", str(path)))
    if issues:
        return _report(project_root, issues, {})

    source = load_json(paths["source"])
    lock = load_json(paths["lock"])
    model = load_json(paths["model"])
    qa = load_json(paths["qa"])
    visual = load_json(paths["visual"])
    manifest = load_manifest(project_root, root)
    issues.extend(validate_source_model(source))
    issues.extend(verify_repository_evidence(source, repo_root))
    issues.extend(validate_lock(lock, root))
    issues.extend(validate_manifest(manifest, project_root))
    if source.get("status") != "confirmed":
        issues.append(Issue("error", "source-unconfirmed", "source_model.status must be confirmed before delivery.", "source_model.status"))
    if lock.get("status") != "confirmed":
        issues.append(Issue("error", "lock-unconfirmed", "diagram_lock.status must be confirmed before delivery.", "diagram_lock.status"))
    if lock.get("sourceHash") != sha256_json(source):
        issues.append(Issue("error", "source-lock-drift", "diagram_lock sourceHash does not match source_model.", "diagram_lock.sourceHash"))
    if resolve_view_intent(model) != resolve_view_intent({"route": lock.get("route", {}), "viewIntent": lock.get("viewIntent", "")}):
        issues.append(Issue("error", "view-intent-lock-drift", "diagram_model and diagram_lock resolve to different semantic view intents.", "diagram_lock.viewIntent"))
    issues.extend(validate_drawio_metadata(paths["drawio"], model))
    drawio_root = ET.parse(paths["drawio"]).getroot()
    if drawio_root.get("nc-model-hash") != sha256_json(model):
        issues.append(Issue("error", "model-build-drift", "The .drawio file was not built from the current diagram_model.", "mxfile@nc-model-hash"))
    if not qa.get("ok"):
        issues.append(Issue("error", "qa-failed", "diagram_qa.json is not passing.", "reports/diagram_qa.json"))
    if not visual.get("ok") or visual.get("manualReview", {}).get("status") != "approved":
        issues.append(Issue("error", "visual-unapproved", "Rendered visual QA has not been approved.", "reports/visual_qa.json"))
    visual_artifact = Path(str(visual.get("artifact", "")))
    if not visual_artifact.is_absolute():
        visual_artifact = project_root / visual_artifact
    if not visual_artifact.is_file() or sha256_file(visual_artifact) != visual.get("sha256"):
        issues.append(Issue("error", "visual-drift", "Approved visual artifact is missing or has changed.", "reports/visual_qa.json"))
    unresolved = [item.get("key") for item in manifest.get("assets", []) if item.get("state") == "NeedsManual"]
    if unresolved:
        issues.append(Issue("error", "asset-unresolved", f"Assets still need manual resolution: {', '.join(map(str, unresolved))}.", "assets"))

    if not any(issue.severity == "error" for issue in issues):
        embedded = {str(node.get("assetRef")) for node in model.get("nodes", []) if node.get("assetRef")}
        if embedded:
            mark_assets(project_root, embedded, "RenderVerified")
    artifacts = {
        name: {"path": portable_path(path, project_root), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for name, path in paths.items()
        if path.is_file()
    }
    return _report(project_root, issues, artifacts)


def _report(project_root: Path, issues: list[Issue], artifacts: dict[str, Any]) -> dict[str, Any]:
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    return {
        "schemaVersion": "2.0",
        "checkedAt": utc_now(),
        "projectRoot": ".",
        "ok": errors == 0,
        "counts": {"error": errors, "warning": warnings},
        "issues": [issue.to_dict() for issue in issues],
        "artifacts": artifacts,
    }

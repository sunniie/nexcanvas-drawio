from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import portable_path, sha256_file, utc_now
from .rendering import image_dimensions


def create_visual_report(
    artifact: Path,
    expected_width: int | None = None,
    expected_height: int | None = None,
    approved: bool = False,
    reviewer: str = "",
    notes: str = "",
    report_root: Path | None = None,
) -> dict[str, Any]:
    if not artifact.is_file() or artifact.stat().st_size == 0:
        raise ValueError(f"Visual artifact is missing or empty: {artifact}")
    dimensions = image_dimensions(artifact)
    checks: list[dict[str, Any]] = []
    checks.append({"name": "non-empty-artifact", "ok": artifact.stat().st_size > 1024, "detail": f"{artifact.stat().st_size} bytes"})
    if dimensions:
        width, height = dimensions
        checks.append({"name": "minimum-readable-size", "ok": width >= 640 and height >= 360, "detail": f"{width}x{height}"})
        if expected_width and expected_height:
            expected_ratio = expected_width / expected_height
            actual_ratio = width / height
            checks.append({"name": "aspect-ratio", "ok": abs(actual_ratio - expected_ratio) <= 0.02, "detail": f"actual={actual_ratio:.3f}, expected={expected_ratio:.3f}"})
    else:
        checks.append({"name": "dimensions", "ok": artifact.suffix.lower() == ".pdf", "detail": "Dimensions are not available for this format."})
    automated_ok = all(check["ok"] for check in checks)
    status = "approved" if approved and automated_ok else ("rejected" if approved else "pending-review")
    return {
        "schemaVersion": "2.0",
        "reviewedAt": utc_now(),
        "artifact": portable_path(artifact, report_root),
        "sha256": sha256_file(artifact),
        "dimensions": {"width": dimensions[0], "height": dimensions[1]} if dimensions else None,
        "automatedChecks": checks,
        "manualReview": {
            "status": status,
            "reviewer": reviewer,
            "notes": notes,
            "requiredCriteria": [
                "No clipped, overlapping, or unreadable text",
                "Connector direction and labels match the intended meaning",
                "Parallel connectors use independent lanes or one documented semantic bus",
                "Callouts mask only their own long rail and labels remain clear of badges",
                "Hierarchy, grouping, and visual balance are clear at target size",
                "Technology marks are exact, visible, and not misleading",
                "The composition looks intentional rather than template-filled",
            ],
        },
        "ok": automated_ok and status == "approved",
    }

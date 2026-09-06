#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from drawio_qa import run_checks as run_geometry_checks
from nexcanvas.common import load_json, utc_now, write_json
from nexcanvas.quality import run_quality, summarize
from nexcanvas.registry import resolve_route


def main() -> int:
    parser = argparse.ArgumentParser(description="Run contract, semantic, asset, and geometry QA for a NexCanvas diagram.")
    parser.add_argument("model", type=Path)
    parser.add_argument("--drawio", type=Path)
    parser.add_argument("--source-model", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--repo-root", type=Path, help="Local Git repository used to verify repository-backed evidence.")
    parser.add_argument("--padding", type=float, default=10.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()
    model = load_json(args.model.resolve())
    source = load_json(args.source_model.resolve()) if args.source_model else None
    drawio = args.drawio.resolve() if args.drawio else None
    issues = run_quality(
        model,
        source,
        args.project_root.resolve() if args.project_root else None,
        drawio,
        repo_root=args.repo_root.resolve() if args.repo_root else None,
    )
    report = summarize(issues)
    report["schemaVersion"] = "2.0"
    report["checkedAt"] = utc_now()
    if drawio and drawio.is_file():
        route = resolve_route(model["route"]["family"], model["route"]["profile"])
        geometry_errors, geometry_warnings = run_geometry_checks(drawio, args.padding, str(route["geometryQa"]))
        report["geometry"] = {"profile": route["geometryQa"], "errors": geometry_errors, "warnings": geometry_warnings}
        report["counts"]["error"] += len(geometry_errors)
        report["counts"]["warning"] += len(geometry_warnings)
        report["ok"] = report["counts"]["error"] == 0
    if args.output:
        write_json(args.output.resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    failed = not report["ok"] or (args.fail_on_warning and report["counts"]["warning"] > 0)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

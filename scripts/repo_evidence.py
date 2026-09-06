#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.common import load_json, write_json
from nexcanvas.repository import inspect_repository, verify_repository_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture or verify revision-pinned repository evidence for NexCanvas.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture = subparsers.add_parser("capture", help="Inspect a Git repository and emit a source entry.")
    capture.add_argument("repo_root", type=Path)
    capture.add_argument("--source-id", default="repository-1")
    capture.add_argument("--source-model", type=Path, help="Insert or replace the repository source in this source_model.json.")
    capture.add_argument("--output", type=Path, help="Write the captured source entry as JSON instead of stdout only.")
    verify = subparsers.add_parser("verify", help="Verify repository origin, revision, blobs, and line ranges.")
    verify.add_argument("source_model", type=Path)
    verify.add_argument("--repo-root", type=Path, required=True)
    verify.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.command == "capture":
        source_model_path = args.source_model.resolve() if args.source_model else None
        relative_to = source_model_path.parent if source_model_path else None
        entry = inspect_repository(args.repo_root.resolve(), args.source_id, relative_to)
        if source_model_path:
            model = load_json(source_model_path)
            sources = [source for source in model.get("sources", []) if isinstance(source, dict) and source.get("id") != args.source_id]
            sources.append(entry)
            model["sources"] = sources
            write_json(source_model_path, model)
        if args.output:
            write_json(args.output.resolve(), entry)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return 0

    model = load_json(args.source_model.resolve())
    issues = verify_repository_evidence(model, args.repo_root.resolve())
    report = {"ok": not any(issue.severity == "error" for issue in issues), "issues": [issue.to_dict() for issue in issues]}
    if args.output:
        write_json(args.output.resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

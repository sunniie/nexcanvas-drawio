#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.contracts import validate_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a NexCanvas v2 JSON contract.")
    parser.add_argument("kind", choices=["source-model", "diagram-lock", "diagram-model", "asset-manifest"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--project-root", type=Path)
    args = parser.parse_args()
    issues = validate_file(args.path.resolve(), args.kind, project_root=args.project_root.resolve() if args.project_root else None)
    report = {"ok": not any(issue.severity == "error" for issue in issues), "issues": [issue.to_dict() for issue in issues]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

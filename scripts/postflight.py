#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.common import write_json
from nexcanvas.postflight import run_postflight


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify NexCanvas delivery provenance and all quality gates.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--repo-root", type=Path, help="Local Git repository used to reverify repository-backed evidence.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_postflight(args.project_root.resolve(), repo_root=args.repo_root.resolve() if args.repo_root else None)
    if args.output:
        write_json(args.output.resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

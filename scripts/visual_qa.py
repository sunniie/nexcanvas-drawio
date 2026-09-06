#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.common import write_json
from nexcanvas.visual import create_visual_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Record automated visual checks and explicit rendered-image approval.")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    parser.add_argument("--approve", action="store_true", help="Use only after inspecting the rendered image at target size.")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    inferred_root = output.parent.parent if output.parent.name == "reports" else None
    try:
        report = create_visual_report(args.artifact.resolve(), args.expected_width, args.expected_height, args.approve, args.reviewer, args.notes, inferred_root)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    write_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

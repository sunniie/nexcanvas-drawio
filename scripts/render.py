#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.common import write_json
from nexcanvas.rendering import render_drawio


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a .drawio artifact with embedded editable XML.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument("--format", choices=["png", "svg", "pdf"])
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    inferred_root = source.parent.parent if source.parent.name == "artifacts" else None
    try:
        result = render_drawio(source, output, args.format, args.scale, report_root=inferred_root)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    if args.report:
        write_json(args.report.resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

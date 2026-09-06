#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.builder import build_drawio
from nexcanvas.common import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Build native editable Draw.io XML from a NexCanvas diagram model.")
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--proof", type=Path, help="Optional JSON build proof path.")
    args = parser.parse_args()
    try:
        result = build_drawio(
            args.model.resolve(),
            args.output.resolve(),
            project_root=args.project_root.resolve() if args.project_root else None,
        )
    except (OSError, KeyError, ValueError) as exc:
        parser.error(str(exc))
    if args.proof:
        write_json(args.proof.resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

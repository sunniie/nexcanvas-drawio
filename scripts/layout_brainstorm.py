#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.common import load_json, write_json
from nexcanvas.planning import brainstorm_layout


def main() -> int:
    parser = argparse.ArgumentParser(description="Score NexCanvas layout candidates before generating geometry.")
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = brainstorm_layout(load_json(args.model.resolve()))
    if args.output:
        write_json(args.output.resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

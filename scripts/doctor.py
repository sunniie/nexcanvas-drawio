#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.common import write_json
from nexcanvas.runtime import inspect_runtime


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect NexCanvas Draw.io runtime capabilities.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    args = parser.parse_args()
    report = inspect_runtime()
    if args.output:
        write_json(args.output.resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["capabilities"]["authorNativeDrawio"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

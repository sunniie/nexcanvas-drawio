#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from nexcanvas.assets import load_catalog, search_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the pinned NexCanvas technology-icon catalog.")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    results = search_catalog(args.query, limit=args.limit) if args.query else load_catalog().get("entries", [])[: args.limit]
    print(json.dumps({"count": len(results), "results": results}, ensure_ascii=False, indent=2))
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())

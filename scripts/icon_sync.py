#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.assets import sync_catalog_asset, sync_provider_asset, sync_user_asset


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve and sync a verified diagram asset into a project.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("query", help="Catalog query or manifest key for --user-svg.")
    parser.add_argument("--user-svg", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--provider", help="Official provider pack key, such as microsoft-azure-official.")
    parser.add_argument("--source-archive", type=Path, help="Official provider ZIP or extracted icon directory.")
    parser.add_argument("--accept-terms", action="store_true", help="Confirm that the provider icon terms were reviewed and accepted.")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--generic-fallback", action="store_true")
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    try:
        if args.user_svg:
            result = sync_user_asset(project_root, args.query, args.user_svg.resolve(), args.title)
        elif args.provider:
            result = sync_provider_asset(
                project_root,
                args.provider,
                args.query,
                source_archive=args.source_archive.resolve() if args.source_archive else None,
                accept_terms=args.accept_terms,
            )
        else:
            result = sync_catalog_asset(project_root, args.query, offline=args.offline, generic_fallback=args.generic_fallback)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("state") != "NeedsManual" else 2


if __name__ == "__main__":
    raise SystemExit(main())

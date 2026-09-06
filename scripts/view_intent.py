#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from nexcanvas.intents import DEFAULT_ROUTES, classify_brief


def main() -> int:
    parser = argparse.ArgumentParser(description="Infer NexCanvas semantic view intent from a user brief.")
    parser.add_argument("brief")
    args = parser.parse_args()
    result = classify_brief(args.brief)
    family, profile = DEFAULT_ROUTES[result["viewIntent"]]
    result["defaultRoute"] = {"family": family, "profile": profile}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the Phase 6 corpus, adapters, fixtures, and reporting invariants."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexcanvas.conformance import build_matrix, evaluate_run, load_adapters, load_suite, matrix_markdown, prepare_run


def main() -> int:
    suite = load_suite(ROOT)
    adapters = load_adapters(ROOT)
    failures: list[str] = []
    baselines = [case for case in suite["cases"] if case.get("baselineProject")]
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        for case in baselines:
            pack = temp / case["id"]
            prepare_run(case["id"], "codex", pack, ROOT)
            result = evaluate_run(
                pack / "request.json",
                ROOT / case["baselineProject"],
                mode="fixture",
                root=ROOT,
            )
            if not result["passed"] or result["status"] != "fixture":
                failures.append(f"fixture failed: {case['id']}")
        matrix = build_matrix([], detect=False, root=ROOT)
        if any(host["state"] != "not-run" for host in matrix["hosts"]):
            failures.append("empty observed result set must leave every host not-run")
        if "fixtures never change host status" not in matrix_markdown(matrix):
            failures.append("matrix disclosure is missing")
    if failures:
        print("NexCanvas conformance validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        f"NexCanvas conformance validation passed: {len(suite['cases'])} cases, "
        f"{len(adapters)} adapters, {len(baselines)} fixture baselines."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


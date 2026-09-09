#!/usr/bin/env python3
"""Deprecated v0.1 wrapper; use ``nexcanvas qa diagram``."""

from nexcanvas.geometry import main, run_checks

__all__ = ["main", "run_checks"]


if __name__ == "__main__":
    raise SystemExit(main())

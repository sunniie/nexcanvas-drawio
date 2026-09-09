#!/usr/bin/env python3
"""Deprecated v0.1 wrapper; use ``nexcanvas init``."""

from nexcanvas.project import init_project, main

__all__ = ["init_project", "main"]


if __name__ == "__main__":
    raise SystemExit(main())

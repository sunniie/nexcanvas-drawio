"""Compatibility loader for v0.1 script entry points.

The supported package lives in ``src/nexcanvas``. This shim lets existing
``python scripts/<command>.py`` invocations continue to resolve it from a clone.
"""

from pathlib import Path


_SOURCE_PACKAGE = Path(__file__).resolve().parents[2] / "src" / "nexcanvas"
if not _SOURCE_PACKAGE.is_dir():
    raise ImportError(f"NexCanvas source package not found: {_SOURCE_PACKAGE}")

__path__ = [str(_SOURCE_PACKAGE)]
exec(
    compile(
        (_SOURCE_PACKAGE / "__init__.py").read_text(encoding="utf-8"),
        str(_SOURCE_PACKAGE / "__init__.py"),
        "exec",
    )
)


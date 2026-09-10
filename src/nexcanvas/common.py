from __future__ import annotations

import hashlib
import json
import os
import re
import sysconfig
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _has_runtime_data(path: Path) -> bool:
    return all(
        (path / relative).is_file()
        for relative in (
            "config/route-registry.json",
            "config/styles.json",
            "assets/catalog/technology-icons.json",
            "schemas/diagram-model.schema.json",
            "schemas/diagram-model-v3.schema.json",
        )
    )


def resource_root() -> Path:
    """Resolve immutable runtime data without depending on the process CWD."""

    configured = os.environ.get("NEXCANVAS_HOME")
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())

    package_file = Path(__file__).resolve()
    candidates.extend(
        [
            package_file.parents[2],
            Path(sysconfig.get_path("data")) / "share" / "nexcanvas",
        ]
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if _has_runtime_data(resolved):
            return resolved
    checked = ", ".join(str(path) for path in candidates)
    raise RuntimeError(
        "NexCanvas runtime data was not found. Reinstall the package or set "
        f"NEXCANVAS_HOME to a valid distribution root. Checked: {checked}"
    )


def skill_root() -> Path:
    """Backward-compatible name for the resolved distribution resource root."""

    return resource_root()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "diagram"


def safe_project_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ValueError(f"Path escapes project root: {relative}")
    return candidate


def portable_path(path: Path, base: Path | None = None) -> str:
    resolved = path.resolve()
    if base is not None:
        try:
            return resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            pass
    return str(resolved)

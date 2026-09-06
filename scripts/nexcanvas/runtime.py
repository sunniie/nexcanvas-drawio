from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .common import skill_root, utc_now


def _command_version(command: str, args: list[str] | None = None) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    try:
        completed = subprocess.run(
            [executable, *(args or ["--version"])],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else "available"


def is_wsl() -> bool:
    if os.name != "posix":
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def find_drawio() -> Path | None:
    for command in ("drawio", "draw.io"):
        found = shutil.which(command)
        if found:
            return Path(found).resolve()

    candidates: list[Path] = []
    system = platform.system().lower()
    if system == "windows":
        candidates.extend(
            [
                Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "draw.io" / "draw.io.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "draw.io" / "draw.io.exe",
            ]
        )
    elif system == "darwin":
        candidates.append(Path("/Applications/draw.io.app/Contents/MacOS/draw.io"))
    elif is_wsl():
        candidates.extend(
            [
                Path("/mnt/c/Program Files/draw.io/draw.io.exe"),
                Path("/mnt/c/Program Files (x86)/draw.io/draw.io.exe"),
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def inspect_runtime(root: Path | None = None) -> dict[str, Any]:
    resolved_root = (root or skill_root()).resolve()
    drawio = find_drawio()
    python_version = platform.python_version()
    node_version = _command_version("node")
    has_browser_launcher = any(shutil.which(name) for name in ("xdg-open", "open", "start", "cmd.exe")) or os.name == "nt"
    tier = "full" if drawio else "portable"
    capabilities = {
        "authorNativeDrawio": True,
        "validateContracts": True,
        "structuralQa": True,
        "layoutBuiltIn": True,
        "layoutElk": node_version is not None,
        "renderCli": drawio is not None,
        "openBrowser": has_browser_launcher,
        "imageGeneration": False,
    }
    return {
        "schemaVersion": "2.0",
        "checkedAt": utc_now(),
        "tier": tier,
        "platform": platform.platform(),
        "python": python_version,
        "node": node_version,
        "drawio": str(drawio) if drawio else None,
        "skillRoot": str(resolved_root),
        "capabilities": capabilities,
        "limitations": [] if drawio else ["Draw.io Desktop CLI not found; rendered visual QA cannot be completed."],
    }

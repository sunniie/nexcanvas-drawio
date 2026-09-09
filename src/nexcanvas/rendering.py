from __future__ import annotations

import os
import struct
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .common import portable_path, sha256_file, utc_now
from .runtime import find_drawio


FORMATS = {"png", "svg", "pdf"}


def image_dimensions(path: Path) -> tuple[int, int] | None:
    suffix = path.suffix.lower()
    if suffix == ".png":
        with path.open("rb") as handle:
            header = handle.read(24)
        if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", header[16:24])
    if suffix == ".svg":
        root = ET.parse(path).getroot()
        width = str(root.get("width", "")).replace("px", "")
        height = str(root.get("height", "")).replace("px", "")
        try:
            return int(round(float(width))), int(round(float(height)))
        except ValueError:
            view_box = str(root.get("viewBox", "")).split()
            if len(view_box) == 4:
                return int(round(float(view_box[2]))), int(round(float(view_box[3])))
    return None


def render_drawio(
    source: Path,
    output: Path,
    fmt: str | None = None,
    scale: float = 1.0,
    timeout: int = 120,
    executable: Path | None = None,
    report_root: Path | None = None,
) -> dict[str, Any]:
    output_format = (fmt or output.suffix.lstrip(".")).lower()
    if output_format not in FORMATS:
        raise ValueError(f"Unsupported export format: {output_format}")
    cli = executable or find_drawio()
    if cli is None:
        raise RuntimeError("Draw.io Desktop CLI was not found. Run 'nexcanvas doctor' for capability details.")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(cli),
        "--export",
        "--format",
        output_format,
        "--embed-diagram",
        "--scale",
        str(scale),
        "--border",
        "0",
        "--output",
        str(output),
        str(source),
    ]
    environment = os.environ.copy()
    environment["ELECTRON_DISABLE_SECURITY_WARNINGS"] = "true"
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False, env=environment)
    if completed.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
        diagnostic = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
        raise RuntimeError(f"Draw.io export failed with exit code {completed.returncode}: {diagnostic}")
    dimensions = image_dimensions(output)
    return {
        "schemaVersion": "2.0",
        "renderedAt": utc_now(),
        "source": portable_path(source, report_root),
        "output": portable_path(output, report_root),
        "format": output_format,
        "scale": scale,
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "dimensions": {"width": dimensions[0], "height": dimensions[1]} if dimensions else None,
        "renderer": cli.name,
        "command": [cli.name, *command[1:-2], portable_path(output, report_root), portable_path(source, report_root)],
    }

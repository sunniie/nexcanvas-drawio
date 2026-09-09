from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import load_json, skill_root


def archetype_registry(root: Path | None = None) -> dict[str, Any]:
    return load_json((root or skill_root()) / "config" / "visual-archetypes.json")


def resolve_archetype(name: str | None, root: Path | None = None) -> dict[str, Any]:
    registry = archetype_registry(root)
    selected = name or registry.get("default", "technical-editorial")
    value = registry.get("archetypes", {}).get(selected)
    if not isinstance(value, dict):
        raise KeyError(f"Unknown visual archetype: {selected}")
    return {"key": selected, **value}


def provider_pack_registry(root: Path | None = None) -> dict[str, Any]:
    return load_json((root or skill_root()) / "config" / "provider-icon-packs.json")


def resolve_provider_pack(name: str, root: Path | None = None) -> dict[str, Any]:
    value = provider_pack_registry(root).get("packs", {}).get(name)
    if not isinstance(value, dict):
        raise KeyError(f"Unknown provider icon pack: {name}")
    return {"key": name, **value}

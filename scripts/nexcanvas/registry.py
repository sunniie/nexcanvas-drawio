from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import load_json, skill_root


SUPPORTED_LAYOUTS = {
    "erd",
    "grid",
    "layered",
    "matrix",
    "nested",
    "radial",
    "rag",
    "reference",
    "sequence",
    "swimlane",
    "tree",
}


def route_registry(root: Path | None = None) -> dict[str, Any]:
    base = root or skill_root()
    return load_json(base / "config" / "route-registry.json")


def style_registry(root: Path | None = None) -> dict[str, Any]:
    base = root or skill_root()
    return load_json(base / "config" / "styles.json")


def resolve_route(family: str, profile: str, root: Path | None = None) -> dict[str, Any]:
    registry = route_registry(root)
    family_entry = registry.get("families", {}).get(family)
    if not family_entry:
        raise KeyError(f"Unknown route family: {family}")
    profile_entry = family_entry.get("profiles", {}).get(profile)
    if not profile_entry:
        raise KeyError(f"Unknown route profile: {family}/{profile}")
    return {"family": family, "profile": profile, **profile_entry}


def resolve_theme(theme: str, root: Path | None = None) -> dict[str, Any]:
    registry = style_registry(root)
    entry = registry.get("themes", {}).get(theme)
    if not entry:
        raise KeyError(f"Unknown visual theme: {theme}")
    return {"id": theme, **entry}


def all_profiles(root: Path | None = None) -> list[tuple[str, str, dict[str, Any]]]:
    result: list[tuple[str, str, dict[str, Any]]] = []
    for family, family_entry in route_registry(root).get("families", {}).items():
        for profile, profile_entry in family_entry.get("profiles", {}).items():
            result.append((family, profile, profile_entry))
    return result

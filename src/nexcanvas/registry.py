from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .common import load_json, skill_root

if TYPE_CHECKING:
    from .extensions import ExtensionSet


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


def route_registry(root: Path | None = None, extensions: "ExtensionSet | None" = None) -> dict[str, Any]:
    base = root or skill_root()
    registry = load_json(base / "config" / "route-registry.json")
    if extensions is None:
        return registry
    for component in extensions.components("route"):
        value = extensions.data("route", component.component_id)
        family = value.get("family") if isinstance(value, dict) else None
        profile = value.get("profile") if isinstance(value, dict) else None
        definition = value.get("definition") if isinstance(value, dict) else None
        if not isinstance(family, str) or not family or not isinstance(profile, str) or not profile:
            raise ValueError(f"Extension route {component.component_id} requires family and profile.")
        if not isinstance(definition, dict):
            raise ValueError(f"Extension route {component.component_id} requires a definition object.")
        families = registry.setdefault("families", {})
        family_entry = families.setdefault(family, {"description": "Extension route family", "profiles": {}})
        profiles = family_entry.setdefault("profiles", {})
        if profile in profiles:
            raise ValueError(f"Extension route cannot replace existing route: {family}/{profile}.")
        profiles[profile] = definition
    return registry


def style_registry(root: Path | None = None) -> dict[str, Any]:
    base = root or skill_root()
    return load_json(base / "config" / "styles.json")


def resolve_route(
    family: str,
    profile: str,
    root: Path | None = None,
    extensions: "ExtensionSet | None" = None,
) -> dict[str, Any]:
    registry = route_registry(root, extensions)
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


def all_profiles(root: Path | None = None, extensions: "ExtensionSet | None" = None) -> list[tuple[str, str, dict[str, Any]]]:
    result: list[tuple[str, str, dict[str, Any]]] = []
    for family, family_entry in route_registry(root, extensions).get("families", {}).items():
        for profile, profile_entry in family_entry.get("profiles", {}).items():
            result.append((family, profile, profile_entry))
    return result

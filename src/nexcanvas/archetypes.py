from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .common import load_json, skill_root

if TYPE_CHECKING:
    from .extensions import ExtensionSet


def archetype_registry(root: Path | None = None) -> dict[str, Any]:
    return load_json((root or skill_root()) / "config" / "visual-archetypes.json")


def resolve_archetype(name: str | None, root: Path | None = None) -> dict[str, Any]:
    registry = archetype_registry(root)
    selected = name or registry.get("default", "technical-editorial")
    value = registry.get("archetypes", {}).get(selected)
    if not isinstance(value, dict):
        raise KeyError(f"Unknown visual archetype: {selected}")
    return {"key": selected, **value}


def provider_pack_registry(root: Path | None = None, extensions: "ExtensionSet | None" = None) -> dict[str, Any]:
    registry = load_json((root or skill_root()) / "config" / "provider-icon-packs.json")
    if extensions is None:
        return registry
    packs = registry.setdefault("packs", {})
    for component in extensions.components("asset-provider"):
        value = extensions.data("asset-provider", component.component_id)
        if not isinstance(value, dict):
            raise ValueError(f"Asset provider {component.component_id} must contain an object.")
        key = str(value.get("key", component.component_id))
        definition = value.get("definition", value)
        if key in packs:
            raise ValueError(f"Extension asset provider cannot replace existing provider pack: {key}.")
        if not isinstance(definition, dict):
            raise ValueError(f"Asset provider {component.component_id} requires a definition object.")
        packs[key] = {field: entry for field, entry in definition.items() if field != "key"}
    return registry


def resolve_provider_pack(
    name: str,
    root: Path | None = None,
    extensions: "ExtensionSet | None" = None,
) -> dict[str, Any]:
    value = provider_pack_registry(root, extensions).get("packs", {}).get(name)
    if not isinstance(value, dict):
        raise KeyError(f"Unknown provider icon pack: {name}")
    return {"key": name, **value}

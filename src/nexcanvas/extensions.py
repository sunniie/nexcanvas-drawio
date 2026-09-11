from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import __version__
from .common import load_json, sha256_file, sha256_json


EXTENSION_SCHEMA_VERSION = "1.0"
EXTENSION_API_VERSION = "1.0"
EXTENSION_PROTOCOL_VERSION = "1.0"
COMPONENT_KINDS = {
    "analyzer",
    "layout",
    "route",
    "asset-provider",
    "qa-rule",
    "host-adapter",
}
HOOK_KINDS = {"analyzer", "layout", "qa-rule"}
DATA_KINDS = {"route", "asset-provider", "host-adapter"}
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid semantic version: {value!r}")
    return tuple(int(match.group(index)) for index in (1, 2, 3))


def _supports_product(requirement: str, product_version: str) -> bool:
    current = _version_tuple(product_version)
    for token in (item.strip() for item in requirement.split(",")):
        match = re.fullmatch(r"(>=|<=|>|<|==)\s*(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)", token)
        if not match:
            raise ValueError(f"Unsupported requiresNexCanvas constraint: {token!r}")
        expected = _version_tuple(match.group(2))
        operator = match.group(1)
        if operator == ">=" and not current >= expected:
            return False
        if operator == "<=" and not current <= expected:
            return False
        if operator == ">" and not current > expected:
            return False
        if operator == "<" and not current < expected:
            return False
        if operator == "==" and not current == expected:
            return False
    return True


def _inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Extension resource escapes its root: {relative}")
    return candidate


def validate_manifest(value: Any, root: Path | None = None) -> list[str]:
    if not isinstance(value, dict):
        return ["Extension manifest must be an object."]
    issues: list[str] = []
    if value.get("schemaVersion") != EXTENSION_SCHEMA_VERSION:
        issues.append(f"schemaVersion must be {EXTENSION_SCHEMA_VERSION!r}.")
    if value.get("apiVersion") != EXTENSION_API_VERSION:
        issues.append(f"apiVersion must be {EXTENSION_API_VERSION!r}.")
    for field in ("id", "name"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            issues.append(f"{field} must be a non-empty string.")
    if isinstance(value.get("id"), str) and not ID_RE.fullmatch(value["id"]):
        issues.append("id must be a lowercase dot, dash, or underscore separated identifier.")
    try:
        _version_tuple(str(value.get("version", "")))
    except ValueError as exc:
        issues.append(str(exc))
    requirement = value.get("requiresNexCanvas")
    if not isinstance(requirement, str) or not requirement.strip():
        issues.append("requiresNexCanvas must be a non-empty compatibility range.")
    else:
        try:
            if not _supports_product(requirement, __version__):
                issues.append(f"requiresNexCanvas {requirement!r} does not include installed version {__version__}.")
        except ValueError as exc:
            issues.append(str(exc))

    components = value.get("components")
    if not isinstance(components, list) or not components:
        return issues + ["components must be a non-empty array."]
    seen: set[tuple[str, str]] = set()
    for index, component in enumerate(components):
        location = f"components[{index}]"
        if not isinstance(component, dict):
            issues.append(f"{location} must be an object.")
            continue
        kind = component.get("kind")
        component_id = component.get("id")
        if kind not in COMPONENT_KINDS:
            issues.append(f"{location}.kind is unsupported: {kind!r}.")
        if not isinstance(component_id, str) or not ID_RE.fullmatch(component_id):
            issues.append(f"{location}.id must be a valid lowercase identifier.")
        elif isinstance(kind, str) and (kind, component_id) in seen:
            issues.append(f"Duplicate component: {kind}/{component_id}.")
        elif isinstance(kind, str):
            seen.add((kind, component_id))
        if kind in HOOK_KINDS:
            if component.get("protocolVersion") != EXTENSION_PROTOCOL_VERSION:
                issues.append(f"{location}.protocolVersion must be {EXTENSION_PROTOCOL_VERSION!r}.")
            command = component.get("command")
            if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
                issues.append(f"{location}.command must be a non-empty string array.")
            timeout = component.get("timeoutSeconds", 15)
            if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 120:
                issues.append(f"{location}.timeoutSeconds must be an integer from 1 to 120.")
            if isinstance(command, list) and root is not None:
                for command_index, item in enumerate(command):
                    if not isinstance(item, str) or item == "{python}" or os.path.isabs(item):
                        continue
                    if item.endswith((".py", ".exe")) or "/" in item or "\\" in item:
                        try:
                            command_path = _inside(root.resolve(), item)
                            if not command_path.is_file():
                                issues.append(f"{location}.command[{command_index}] does not exist: {item}.")
                        except ValueError as exc:
                            issues.append(f"{location}.command[{command_index}]: {exc}")
            if kind == "analyzer":
                suffixes = component.get("fileSuffixes")
                if not isinstance(suffixes, list) or not suffixes or not all(
                    isinstance(item, str) and re.fullmatch(r"\.[a-z0-9]+", item) for item in suffixes
                ):
                    issues.append(f"{location}.fileSuffixes must contain lowercase file extensions such as '.go'.")
        if kind in DATA_KINDS:
            source = component.get("source")
            if not isinstance(source, str) or not source:
                issues.append(f"{location}.source must be a non-empty relative JSON path.")
            elif root is not None:
                try:
                    path = _inside(root.resolve(), source)
                    if not path.is_file():
                        issues.append(f"{location}.source does not exist: {source}.")
                    elif path.suffix.lower() != ".json":
                        issues.append(f"{location}.source must be a JSON file.")
                except ValueError as exc:
                    issues.append(f"{location}.source: {exc}")
    return issues


@dataclass(frozen=True)
class ExtensionComponent:
    extension_id: str
    extension_version: str
    root: Path
    definition: dict[str, Any]

    @property
    def kind(self) -> str:
        return str(self.definition["kind"])

    @property
    def component_id(self) -> str:
        return str(self.definition["id"])

    @property
    def key(self) -> str:
        return f"{self.kind}/{self.component_id}"


class ExtensionSet:
    def __init__(self, manifests: Iterable[tuple[Path, dict[str, Any]]]) -> None:
        self.manifests: list[dict[str, Any]] = []
        self._components: dict[tuple[str, str], ExtensionComponent] = {}
        for root, manifest in manifests:
            manifest_root = root.resolve()
            declared_files: dict[str, str] = {}
            for definition in manifest["components"]:
                source = definition.get("source")
                if isinstance(source, str):
                    declared_files[source] = sha256_file(_inside(manifest_root, source))
                for item in definition.get("command", []):
                    if (
                        isinstance(item, str)
                        and not os.path.isabs(item)
                        and item.endswith((".py", ".exe"))
                    ):
                        command_file = _inside(manifest_root, item)
                        if command_file.is_file():
                            declared_files[item] = sha256_file(command_file)
            manifest_sha = sha256_file(manifest_root / "nexcanvas-extension.json")
            self.manifests.append(
                {
                    "id": manifest["id"],
                    "name": manifest["name"],
                    "version": manifest["version"],
                    "root": str(manifest_root),
                    "manifestSha256": manifest_sha,
                    "declaredFiles": dict(sorted(declared_files.items())),
                    "contentSha256": sha256_json(
                        {"manifestSha256": manifest_sha, "declaredFiles": dict(sorted(declared_files.items()))}
                    ),
                }
            )
            for definition in manifest["components"]:
                component = ExtensionComponent(
                    str(manifest["id"]), str(manifest["version"]), manifest_root, dict(definition)
                )
                key = (component.kind, component.component_id)
                if key in self._components:
                    other = self._components[key]
                    raise ValueError(
                        f"Duplicate extension component {component.key}: "
                        f"{other.extension_id} and {component.extension_id}."
                    )
                self._components[key] = component

    @classmethod
    def empty(cls) -> "ExtensionSet":
        return cls([])

    def components(self, kind: str) -> list[ExtensionComponent]:
        return sorted(
            (component for (component_kind, _), component in self._components.items() if component_kind == kind),
            key=lambda component: component.component_id,
        )

    def get(self, kind: str, component_id: str) -> ExtensionComponent | None:
        return self._components.get((kind, component_id))

    def data(self, kind: str, component_id: str) -> dict[str, Any] | None:
        component = self.get(kind, component_id)
        if component is None:
            return None
        source = _inside(component.root, str(component.definition["source"]))
        value = load_json(source)
        if not isinstance(value, dict):
            raise ValueError(f"Extension data {component.key} must contain one JSON object.")
        return value

    def run_hook(self, kind: str, component_id: str, request: dict[str, Any]) -> dict[str, Any]:
        component = self.get(kind, component_id)
        if component is None or kind not in HOOK_KINDS:
            raise KeyError(f"Unknown executable extension component: {kind}/{component_id}")
        command = [sys.executable if item == "{python}" else item for item in component.definition["command"]]
        command = [
            str(_inside(component.root, item))
            if item != sys.executable and not os.path.isabs(item) and item.endswith((".py", ".exe"))
            else item
            for item in command
        ]
        envelope = {
            "protocolVersion": EXTENSION_PROTOCOL_VERSION,
            "kind": kind,
            "componentId": component_id,
            "request": request,
        }
        completed = subprocess.run(
            command,
            cwd=component.root,
            input=json.dumps(envelope, ensure_ascii=False),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            timeout=int(component.definition.get("timeoutSeconds", 15)),
            check=False,
            shell=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "no diagnostic"
            raise RuntimeError(f"Extension {component.key} exited with {completed.returncode}: {detail}")
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Extension {component.key} returned invalid JSON: {exc}") from exc
        if not isinstance(response, dict) or response.get("protocolVersion") != EXTENSION_PROTOCOL_VERSION:
            raise ValueError(f"Extension {component.key} response must use protocolVersion {EXTENSION_PROTOCOL_VERSION}.")
        if response.get("ok") is not True or not isinstance(response.get("result"), dict):
            raise ValueError(f"Extension {component.key} returned an unsuccessful or malformed response.")
        return response["result"]

    def describe(self) -> dict[str, Any]:
        return {
            "schemaVersion": EXTENSION_SCHEMA_VERSION,
            "apiVersion": EXTENSION_API_VERSION,
            "manifests": self.manifests,
            "components": [
                {
                    "kind": component.kind,
                    "id": component.component_id,
                    "extensionId": component.extension_id,
                    "extensionVersion": component.extension_version,
                    "mode": "hook" if component.kind in HOOK_KINDS else "data",
                }
                for component in sorted(self._components.values(), key=lambda item: item.key)
            ],
        }

    def fingerprint(self) -> str:
        """Return a clone-path-independent digest of every loaded extension input."""
        return sha256_json(
            [
                {
                    "id": manifest["id"],
                    "version": manifest["version"],
                    "contentSha256": manifest["contentSha256"],
                }
                for manifest in sorted(self.manifests, key=lambda item: str(item["id"]))
            ]
        )


def load_extensions(paths: Iterable[Path] | None) -> ExtensionSet:
    manifests: list[tuple[Path, dict[str, Any]]] = []
    seen_roots: set[Path] = set()
    for supplied in paths or []:
        path = supplied.resolve()
        root = path if path.is_dir() else path.parent
        manifest_path = root / "nexcanvas-extension.json" if path.is_dir() else path
        if root in seen_roots:
            continue
        seen_roots.add(root)
        if manifest_path.name != "nexcanvas-extension.json" or not manifest_path.is_file():
            raise ValueError(f"Extension path must be a directory containing nexcanvas-extension.json: {supplied}")
        manifest = load_json(manifest_path)
        issues = validate_manifest(manifest, root)
        if issues:
            raise ValueError(f"Invalid extension {manifest_path}: {issues[0]}")
        manifests.append((root, manifest))
    return ExtensionSet(manifests)

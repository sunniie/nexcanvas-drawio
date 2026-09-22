from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Iterable

from . import __version__
from .common import load_json, resource_root, sha256_file
from .contracts import validate_file
from .runtime import inspect_runtime


MANIFEST_PATH = "config/stability-manifest.json"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")

PROJECT_CONTRACTS: tuple[tuple[str, str, str, bool], ...] = (
    ("source-model", "source_model.json", "source-model", True),
    ("diagram-lock", "diagram_lock.json", "diagram-lock", True),
    ("diagram-model", "diagram_model.json", "diagram-model", True),
    ("asset-manifest", "assets/asset_manifest.json", "asset-manifest", True),
    ("project-state", "project_state.json", "project-state", False),
    ("repository-snapshot", "repository_snapshot.json", "repository-snapshot", False),
    ("semantic-sync-plan", "reports/semantic_sync.json", "sync-plan", False),
    ("diagram-qa", "reports/diagram_qa.json", "diagram-qa", False),
    ("visual-qa", "reports/visual_qa.json", "visual-qa", False),
    ("postflight", "reports/postflight.json", "postflight", False),
)


def load_stability_manifest(root: Path | None = None) -> dict[str, Any]:
    distribution = (root or resource_root()).resolve()
    value = load_json(distribution / MANIFEST_PATH)
    if not isinstance(value, dict):
        raise ValueError("The NexCanvas stability manifest must be a JSON object.")
    issues = validate_stability_manifest(value, distribution)
    if issues:
        raise ValueError(f"Invalid NexCanvas stability manifest: {issues[0]}")
    return value


def validate_stability_manifest(value: dict[str, Any], root: Path) -> list[str]:
    issues: list[str] = []
    if value.get("schemaVersion") != "1.0":
        issues.append("schemaVersion must be '1.0'.")
    if value.get("contractSet") != "1.0":
        issues.append("contractSet must be '1.0'.")
    if value.get("stableFrom") != "1.0.0":
        issues.append("stableFrom must be '1.0.0'.")
    if value.get("supportLine") != "1.x":
        issues.append("supportLine must be '1.x'.")

    platforms = value.get("platforms")
    if not isinstance(platforms, dict):
        issues.append("platforms must be an object.")
    else:
        python = platforms.get("python") if isinstance(platforms.get("python"), dict) else {}
        supported = python.get("supported")
        if not isinstance(supported, list) or not supported or not all(isinstance(item, str) for item in supported):
            issues.append("platforms.python.supported must be a non-empty string array.")
        if python.get("reference") not in (supported or []):
            issues.append("platforms.python.reference must be one of the supported versions.")

    cli = value.get("cli")
    if not isinstance(cli, dict):
        issues.append("cli must be an object.")
    else:
        if cli.get("command") != "nexcanvas":
            issues.append("cli.command must be 'nexcanvas'.")
        exit_codes = cli.get("exitCodes")
        if not isinstance(exit_codes, dict) or set(exit_codes) != {"0", "1", "2", "3"}:
            issues.append("cli.exitCodes must define exactly 0, 1, 2, and 3.")
        commands = cli.get("commands")
        if not isinstance(commands, list) or not commands:
            issues.append("cli.commands must be a non-empty array.")
        else:
            paths: list[str] = []
            for index, command in enumerate(commands):
                if not isinstance(command, dict):
                    issues.append(f"cli.commands[{index}] must be an object.")
                    continue
                path = command.get("path")
                if not isinstance(path, str) or not path:
                    issues.append(f"cli.commands[{index}].path must be a non-empty string.")
                else:
                    paths.append(path)
                for field in ("positionals", "options"):
                    items = command.get(field)
                    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                        issues.append(f"cli.commands[{index}].{field} must be a string array.")
                    elif len(items) != len(set(items)):
                        issues.append(f"cli.commands[{index}].{field} contains duplicates.")
                options = command.get("options")
                if isinstance(options, list) and options != sorted(options):
                    issues.append(f"cli.commands[{index}].options must be sorted.")
            if len(paths) != len(set(paths)):
                issues.append("cli.commands paths must be unique.")

    contracts = value.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        issues.append("contracts must be a non-empty array.")
    else:
        ids: list[str] = []
        for index, contract in enumerate(contracts):
            if not isinstance(contract, dict):
                issues.append(f"contracts[{index}] must be an object.")
                continue
            contract_id = contract.get("id")
            if not isinstance(contract_id, str) or not contract_id:
                issues.append(f"contracts[{index}].id must be a non-empty string.")
            else:
                ids.append(contract_id)
            version = contract.get("version")
            if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+", version):
                issues.append(f"contracts[{index}].version must be major.minor.")
            if contract.get("status") not in {"stable", "compatibility"}:
                issues.append(f"contracts[{index}].status is invalid.")
            schema = contract.get("schema")
            if not isinstance(schema, str) or not schema.startswith("schemas/"):
                issues.append(f"contracts[{index}].schema must be a schemas/ path.")
            else:
                schema_path = root / schema
                if not schema_path.is_file():
                    issues.append(f"contracts[{index}] schema is missing: {schema}.")
                else:
                    schema_value = load_json(schema_path)
                    declared = (
                        schema_value.get("properties", {}).get("schemaVersion", {}).get("const")
                        if isinstance(schema_value, dict)
                        else None
                    )
                    if declared != version:
                        issues.append(
                            f"contracts[{index}] version {version!r} does not match "
                            f"{schema} schemaVersion const {declared!r}."
                        )
        if len(ids) != len(set(ids)):
            issues.append("contract IDs must be unique.")

    policies = value.get("policies")
    if not isinstance(policies, dict):
        issues.append("policies must be an object.")
    else:
        for name, relative in policies.items():
            if not isinstance(relative, str) or not (root / relative).is_file():
                issues.append(f"policy {name!r} points to a missing file: {relative!r}.")
    return issues


def public_cli_surface(parser: argparse.ArgumentParser) -> list[dict[str, Any]]:
    def walk(current: argparse.ArgumentParser, prefix: tuple[str, ...]) -> Iterable[dict[str, Any]]:
        subparsers = next(
            (action for action in current._actions if isinstance(action, argparse._SubParsersAction)),
            None,
        )
        if subparsers is not None:
            for name, child in subparsers.choices.items():
                yield from walk(child, (*prefix, name))
            return
        if not prefix:
            return
        positionals: list[str] = []
        options: list[str] = []
        for action in current._actions:
            if action.dest == "help":
                continue
            if action.option_strings:
                options.extend(action.option_strings)
            else:
                positionals.append(action.dest)
        yield {
            "path": " ".join(prefix),
            "positionals": positionals,
            "options": sorted(options),
        }

    return list(walk(parser, ()))


def validate_cli_surface(parser: argparse.ArgumentParser, manifest: dict[str, Any]) -> list[str]:
    expected = manifest.get("cli", {}).get("commands", [])
    actual = public_cli_surface(parser)
    if actual == expected:
        return []
    expected_by_path = {item.get("path"): item for item in expected if isinstance(item, dict)}
    actual_by_path = {item.get("path"): item for item in actual}
    issues: list[str] = []
    for path in sorted(set(expected_by_path) - set(actual_by_path)):
        issues.append(f"stable CLI command is missing: {path}")
    for path in sorted(set(actual_by_path) - set(expected_by_path)):
        issues.append(f"unregistered CLI command was added: {path}")
    for path in sorted(set(expected_by_path) & set(actual_by_path)):
        if expected_by_path[path] != actual_by_path[path]:
            issues.append(f"stable CLI surface changed for: {path}")
    return issues or ["stable CLI command order changed"]


def compatibility_report(root: Path | None = None) -> dict[str, Any]:
    distribution = (root or resource_root()).resolve()
    manifest_path = distribution / MANIFEST_PATH
    manifest = load_stability_manifest(distribution)
    version_match = SEMVER_RE.fullmatch(__version__)
    major = int(version_match.group(1)) if version_match else -1
    return {
        "schemaVersion": "1.0",
        "productVersion": __version__,
        "contractSet": manifest["contractSet"],
        "supportLine": manifest["supportLine"],
        "stability": "stable" if major == 1 else "pre-stable-build",
        "manifestSha256": sha256_file(manifest_path),
        "platforms": manifest["platforms"],
        "cli": {
            "command": manifest["cli"]["command"],
            "outputEncoding": manifest["cli"]["outputEncoding"],
            "machineOutput": manifest["cli"]["machineOutput"],
            "exitCodes": manifest["cli"]["exitCodes"],
            "commandCount": len(manifest["cli"]["commands"]),
        },
        "contracts": manifest["contracts"],
        "policies": manifest["policies"],
        "runtime": inspect_runtime(),
    }


def check_project_compatibility(project_root: Path) -> dict[str, Any]:
    project = project_root.resolve()
    results: list[dict[str, Any]] = []
    errors = 0
    missing_required = 0
    diagram_version: str | None = None
    for contract_id, relative, kind, required in PROJECT_CONTRACTS:
        path = project / relative
        if not path.is_file():
            if required:
                missing_required += 1
                errors += 1
            results.append(
                {
                    "id": contract_id,
                    "path": relative,
                    "present": False,
                    "required": required,
                    "ok": not required,
                    "issues": ["required contract is missing"] if required else [],
                }
            )
            continue
        value = load_json(path)
        if contract_id == "diagram-model" and isinstance(value, dict):
            diagram_version = str(value.get("schemaVersion", ""))
        validation = validate_file(path, kind, project_root=project)
        contract_errors = [issue.to_dict() for issue in validation if issue.severity == "error"]
        errors += len(contract_errors)
        results.append(
            {
                "id": contract_id,
                "path": relative,
                "present": True,
                "required": required,
                "schemaVersion": value.get("schemaVersion") if isinstance(value, dict) else None,
                "ok": not contract_errors,
                "issues": contract_errors,
            }
        )
    migration_recommended = diagram_version == "2.0"
    actions: list[str] = []
    if migration_recommended:
        actions.append(
            "Create a separate V3 candidate with: nexcanvas migrate v2-to-v3 "
            "<project>/diagram_model.json --output <project>/diagram_model.v3.json"
        )
    if errors:
        actions.append("Resolve reported contract errors before generating or synchronizing this project.")
    return {
        "schemaVersion": "1.0",
        "productVersion": __version__,
        "contractSet": "1.0",
        "projectRoot": str(project),
        "compatible": errors == 0,
        "migrationRecommended": migration_recommended,
        "missingRequired": missing_required,
        "contracts": results,
        "actions": actions,
        "modified": False,
    }

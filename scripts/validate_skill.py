#!/usr/bin/env python3
"""Validate the portable NexCanvas skill package without host-specific tooling."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")
VERSION_RE = re.compile(
    r'^__version__\s*=\s*["\']([^"\']+)["\'](?:\s*#.*)?$',
    re.MULTILINE,
)
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def _local_link_issues(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = unquote(target.split("#", 1)[0])
        if not (path.parent / target).resolve().exists():
            issues.append(f"{path.relative_to(ROOT)}: missing local link target {target!r}")
    return issues


def validate() -> list[str]:
    issues: list[str] = []
    required = [
        "SKILL.md",
        "README.md",
        "ROADMAP.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "SECURITY.md",
        "SUPPORT.md",
        "CODE_OF_CONDUCT.md",
        "agents/openai.yaml",
        "pyproject.toml",
        "src/nexcanvas/cli.py",
        "src/nexcanvas/pipeline.py",
        "src/nexcanvas/model_v3.py",
        "src/nexcanvas/repository_analysis.py",
        "src/nexcanvas/semantic_sync.py",
        "src/nexcanvas/__main__.py",
        "schemas/project-state.schema.json",
        "schemas/diagram-model-v3.schema.json",
        "schemas/repository-snapshot.schema.json",
        "schemas/semantic-sync-plan.schema.json",
        "schemas/conformance-suite.schema.json",
        "schemas/host-adapter.schema.json",
        "schemas/conformance-execution.schema.json",
        "schemas/conformance-result.schema.json",
        "conformance/suite.json",
        "conformance/hosts/codex.json",
        "conformance/hosts/github-copilot.json",
        "conformance/hosts/claude-code.json",
        "docs/conformance.md",
        "docs/host-capability-matrix.md",
        "docs/pipeline-state.md",
        "references/semantic-model-v3.md",
        "workflows/conformance.md",
        "workflows/sync-repository.md",
        "version.txt",
        "release-please-config.json",
        ".release-please-manifest.json",
        ".github/workflows/release-please.yml",
    ]
    for relative in required:
        if not (ROOT / relative).is_file():
            issues.append(f"missing required file: {relative}")

    skill_path = ROOT / "SKILL.md"
    if skill_path.is_file():
        metadata = _frontmatter(skill_path.read_text(encoding="utf-8"))
        if metadata.get("name") != "nexcanvas-drawio":
            issues.append("SKILL.md: frontmatter name must be nexcanvas-drawio")
        if len(metadata.get("description", "")) < 40:
            issues.append("SKILL.md: description must identify the skill's useful scope")

    version_path = ROOT / "version.txt"
    init_path = ROOT / "src/nexcanvas/__init__.py"
    manifest_path = ROOT / ".release-please-manifest.json"
    if version_path.is_file() and init_path.is_file() and manifest_path.is_file():
        product_version = version_path.read_text(encoding="utf-8").strip()
        if not SEMVER_RE.fullmatch(product_version):
            issues.append(f"version.txt: invalid semantic version {product_version!r}")
        match = VERSION_RE.search(init_path.read_text(encoding="utf-8"))
        python_version = match.group(1) if match else None
        try:
            release_version = json.loads(manifest_path.read_text(encoding="utf-8")).get(".")
        except (json.JSONDecodeError, AttributeError) as exc:
            release_version = None
            issues.append(f".release-please-manifest.json: invalid manifest ({exc})")
        versions = {
            "version.txt": product_version,
            "src/nexcanvas/__init__.py": python_version,
            ".release-please-manifest.json": release_version,
        }
        if len(set(versions.values())) != 1:
            issues.append(f"product versions do not match: {versions}")

    release_workflow_path = ROOT / ".github" / "workflows" / "release-please.yml"
    if release_workflow_path.is_file():
        release_workflow = release_workflow_path.read_text(encoding="utf-8")
        title_command = 'gh release edit "$RELEASE_TAG" --title "NexCanvas $RELEASE_TAG"'
        if title_command not in release_workflow:
            issues.append(
                ".github/workflows/release-please.yml: missing canonical "
                "NexCanvas release-title normalization"
            )

    for relative in [
        "SKILL.md",
        "README.md",
        "ROADMAP.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "SUPPORT.md",
        "docs/cli.md",
        "docs/conformance.md",
        "docs/host-capability-matrix.md",
        "workflows/conformance.md",
    ]:
        path = ROOT / relative
        if path.is_file():
            issues.extend(_local_link_issues(path))

    legacy_core = [path for path in (ROOT / "scripts" / "nexcanvas").glob("*.py") if path.name != "__init__.py"]
    if legacy_core:
        issues.append(f"legacy implementation modules remain under scripts/nexcanvas: {legacy_core}")

    sys.path.insert(0, str(ROOT / "src"))
    try:
        from nexcanvas.conformance import load_adapters, load_suite

        load_suite(ROOT)
        load_adapters(ROOT)
    except (OSError, ValueError) as exc:
        issues.append(f"conformance contracts are invalid: {exc}")

    return issues


def main() -> int:
    issues = validate()
    if issues:
        print("NexCanvas skill validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("NexCanvas skill validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

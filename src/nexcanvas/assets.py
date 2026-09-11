from __future__ import annotations

import re
import shutil
import urllib.error
import urllib.request
import zipfile
from io import BytesIO
from urllib.parse import quote
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .common import load_json, safe_project_path, sha256_file, skill_root, utc_now, write_json
from .archetypes import resolve_provider_pack

if TYPE_CHECKING:
    from .extensions import ExtensionSet


def catalog_path(root: Path | None = None) -> Path:
    return (root or skill_root()) / "assets" / "catalog" / "technology-icons.json"


def load_catalog(root: Path | None = None) -> dict[str, Any]:
    return load_json(catalog_path(root))


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def search_catalog(query: str, root: Path | None = None, limit: int = 10) -> list[dict[str, Any]]:
    needle = normalize(query)
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in load_catalog(root).get("entries", []):
        candidates = [entry.get("key", ""), entry.get("title", ""), entry.get("slug", ""), *entry.get("aliases", [])]
        normalized = [normalize(str(value)) for value in candidates]
        if needle in normalized:
            score = 0
        elif any(value.startswith(needle) or needle.startswith(value) for value in normalized if value):
            score = 1
        elif any(needle in value or value in needle for value in normalized if value):
            score = 2
        else:
            continue
        scored.append((score, entry))
    return [entry for _, entry in sorted(scored, key=lambda item: (item[0], str(item[1].get("title", ""))))[:limit]]


def resolve_catalog_entry(query: str, root: Path | None = None) -> dict[str, Any] | None:
    matches = search_catalog(query, root, limit=10)
    if not matches:
        return None
    needle = normalize(query)
    for entry in matches:
        exact = [entry.get("key", ""), entry.get("title", ""), entry.get("slug", ""), *entry.get("aliases", [])]
        if needle in {normalize(str(value)) for value in exact}:
            return entry
    return matches[0]


def _svg_is_safe(data: bytes) -> tuple[bool, str]:
    if len(data) > 2_000_000:
        return False, "SVG exceeds the 2 MB asset limit."
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        return False, f"Invalid SVG XML: {exc}"
    if root.tag.rsplit("}", 1)[-1].lower() != "svg":
        return False, "Asset root element is not <svg>."
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1].lower()
        if local_name in {"script", "foreignobject"}:
            return False, f"Unsafe SVG element: {local_name}."
        for key, value in element.attrib.items():
            key_name = key.rsplit("}", 1)[-1].lower()
            if key_name.startswith("on"):
                return False, f"Unsafe SVG event attribute: {key_name}."
            if key_name in {"href", "src"} and re.match(r"(?i)https?://", value.strip()):
                return False, "Remote references are not allowed inside synced SVG assets."
    return True, "ok"


def _download(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "nexcanvas-drawio/2.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(2_000_001)


def _download_archive(url: str, timeout: int = 60, maximum: int = 100_000_000) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "nexcanvas-drawio/2.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError(f"Provider archive exceeds the {maximum // 1_000_000} MB safety limit.")
    return data


def _provider_entry(pack: dict[str, Any], query: str) -> tuple[str, dict[str, Any]] | None:
    needle = normalize(query)
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for key, entry in pack.get("entries", {}).items():
        candidates = [key, entry.get("title", ""), *entry.get("aliases", [])]
        values = [normalize(str(value)) for value in candidates]
        if needle in values:
            score = 0
        elif any(value.startswith(needle) or needle.startswith(value) for value in values if value):
            score = 1
        elif any(needle in value or value in needle for value in values if value):
            score = 2
        else:
            continue
        ranked.append((score, str(key), entry))
    if not ranked:
        return None
    _, key, entry = sorted(ranked, key=lambda item: (item[0], item[1]))[0]
    return key, entry


def _dynamic_provider_entry(provider: str, query: str, source_archive: Path) -> tuple[str, dict[str, Any]] | None:
    needle = normalize(query)
    if not needle:
        return None
    if source_archive.is_dir():
        names = [path.name for path in source_archive.rglob("*.svg")]
    else:
        with zipfile.ZipFile(source_archive) as archive:
            names = [Path(name).name for name in archive.namelist() if name.lower().endswith(".svg")]
    scored: list[tuple[int, int, str]] = []
    for name in sorted(set(names)):
        value = normalize(Path(name).stem)
        if value == needle:
            score = 0
        elif value.endswith(needle) or value.startswith(needle):
            score = 1
        elif needle in value:
            score = 2
        else:
            continue
        scored.append((score, len(value), name))
    if not scored:
        return None
    filename = sorted(scored)[0][2]
    provider_prefix = normalize(provider).replace("official", "") or "provider"
    key = f"{provider_prefix}-{needle}"
    return key, {"title": query, "aliases": [query], "filename": filename}


def _provider_svg_bytes(pack: dict[str, Any], entry: dict[str, Any], source_archive: Path | None) -> tuple[bytes, str]:
    filename = str(entry["filename"])
    if source_archive and source_archive.is_dir():
        matches = sorted(path for path in source_archive.rglob("*.svg") if path.name.lower() == filename.lower())
        if not matches:
            raise FileNotFoundError(f"{filename} was not found in {source_archive}.")
        return matches[0].read_bytes(), matches[0].name

    if source_archive:
        archive_data = source_archive.read_bytes()
    else:
        download_url = str(pack.get("downloadUrl", ""))
        if not download_url:
            raise ValueError("This provider pack requires --source-archive with the official downloaded ZIP or icon directory.")
        archive_data = _download_archive(download_url)

    with zipfile.ZipFile(BytesIO(archive_data)) as archive:
        matches = sorted(
            name for name in archive.namelist()
            if not name.endswith("/") and Path(name).name.lower() == filename.lower()
        )
        if not matches:
            raise FileNotFoundError(f"{filename} was not found in the provider archive.")
        info = archive.getinfo(matches[0])
        if info.file_size > 2_000_000:
            raise ValueError("Provider SVG exceeds the 2 MB asset limit.")
        return archive.read(info), matches[0]


def sync_provider_asset(
    project_root: Path,
    provider: str,
    query: str,
    root: Path | None = None,
    source_archive: Path | None = None,
    accept_terms: bool = False,
    extensions: "ExtensionSet | None" = None,
) -> dict[str, Any]:
    resolved_root = root or skill_root()
    pack = resolve_provider_pack(provider, resolved_root, extensions)
    manifest = load_manifest(project_root, resolved_root)
    matched = _provider_entry(pack, query)
    if matched is None and source_archive:
        matched = _dynamic_provider_entry(provider, query, source_archive)
    if matched is None:
        result = {
            "key": query,
            "requested": query,
            "state": "NeedsManual",
            "provider": provider,
            "message": f"No exact entry exists in the {pack['label']} mapping.",
            "updatedAt": utc_now(),
        }
        _upsert(manifest, result)
        manifest["updatedAt"] = utc_now()
        write_json(manifest_file(project_root), manifest)
        return result
    if not accept_terms:
        raise ValueError(f"Review {pack.get('termsUrl', 'the provider terms')} and rerun with --accept-terms.")

    key, entry = matched
    relative = f"{pack['destination']}/{key}.svg"
    target = safe_project_path(project_root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    source = ""
    if not target.is_file():
        data, source = _provider_svg_bytes(pack, entry, source_archive)
        safe, reason = _svg_is_safe(data)
        if not safe:
            raise ValueError(reason)
        target.write_bytes(data)
    result = {
        "key": key,
        "requested": query,
        "title": entry.get("title", key),
        "state": "Synced",
        "provider": provider,
        "version": pack.get("version", ""),
        "sourceUrl": (
            f"{pack.get('downloadUrl')}#{source}" if pack.get("downloadUrl") and source
            else str(pack.get("downloadUrl") or pack.get("termsUrl", ""))
        ),
        "termsUrl": pack.get("termsUrl", ""),
        "localPath": relative,
        "sha256": sha256_file(target),
        "license": pack.get("license", ""),
        "trademarkNotice": "Keep the official icon unmodified and place the represented product name close to it.",
        "message": "",
        "updatedAt": utc_now(),
    }
    _upsert(manifest, result)
    manifest["updatedAt"] = utc_now()
    write_json(manifest_file(project_root), manifest)
    return result


def manifest_file(project_root: Path) -> Path:
    return project_root / "assets" / "asset_manifest.json"


def load_manifest(project_root: Path, root: Path | None = None) -> dict[str, Any]:
    path = manifest_file(project_root)
    if path.is_file():
        return load_json(path)
    catalog = load_catalog(root)
    return {
        "schemaVersion": "2.0",
        "catalogVersion": catalog.get("catalogVersion", "unknown"),
        "updatedAt": utc_now(),
        "assets": [],
    }


def _upsert(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    assets = manifest.setdefault("assets", [])
    for index, existing in enumerate(assets):
        if existing.get("key") == entry.get("key"):
            assets[index] = entry
            return
    assets.append(entry)


def sync_catalog_asset(
    project_root: Path,
    query: str,
    root: Path | None = None,
    offline: bool = False,
    generic_fallback: bool = False,
) -> dict[str, Any]:
    resolved_root = root or skill_root()
    catalog = load_catalog(resolved_root)
    entry = resolve_catalog_entry(query, resolved_root)
    manifest = load_manifest(project_root, resolved_root)
    if entry is None:
        result = {
            "key": query,
            "requested": query,
            "state": "Resolved" if generic_fallback else "NeedsManual",
            "provider": "generic",
            "message": "No verified catalog match; use a clearly labeled generic glyph." if generic_fallback else "No verified catalog match.",
            "updatedAt": utc_now(),
        }
        _upsert(manifest, result)
        manifest["updatedAt"] = utc_now()
        write_json(manifest_file(project_root), manifest)
        return result

    key = str(entry["key"])
    provider = str(entry["provider"])
    if provider == "drawio-native":
        result = {
            "key": key,
            "requested": query,
            "state": "Resolved",
            "provider": provider,
            "nativeStyle": entry.get("nativeStyle", ""),
            "license": catalog.get("license", {}).get(provider, ""),
            "updatedAt": utc_now(),
        }
        _upsert(manifest, result)
        manifest["updatedAt"] = utc_now()
        write_json(manifest_file(project_root), manifest)
        return result

    slug = str(entry["slug"])
    version = str(entry.get("version") or catalog.get("simpleIconsVersion", ""))
    relative = f"assets/icons/simple-icons/{slug}.svg"
    target = safe_project_path(project_root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    url = str(catalog["simpleIconsBaseUrl"]).format(slug=slug, version=version)
    state = "Synced"
    message = ""
    if not target.is_file():
        if offline:
            state = "NeedsManual"
            message = "Offline mode: icon was not already present in the project."
        else:
            try:
                data = _download(url)
                safe, reason = _svg_is_safe(data)
                if not safe:
                    raise ValueError(reason)
                target.write_bytes(data)
            except (OSError, ValueError, urllib.error.URLError) as exc:
                state = "NeedsManual"
                message = f"Unable to sync verified icon: {exc}"
    result = {
        "key": key,
        "requested": query,
        "state": state,
        "provider": provider,
        "version": version,
        "sourceUrl": url,
        "localPath": relative if target.is_file() else "",
        "sha256": sha256_file(target) if target.is_file() else "",
        "license": catalog.get("license", {}).get(provider, ""),
        "trademarkNotice": "Use the mark only for the product it represents; do not redraw, distort, or substitute a neighboring brand.",
        "message": message,
        "updatedAt": utc_now(),
    }
    _upsert(manifest, result)
    manifest["updatedAt"] = utc_now()
    write_json(manifest_file(project_root), manifest)
    return result


def sync_user_asset(project_root: Path, key: str, source: Path, title: str | None = None) -> dict[str, Any]:
    data = source.read_bytes()
    safe, reason = _svg_is_safe(data)
    if not safe:
        raise ValueError(reason)
    filename = f"{normalize(key) or 'custom'}.svg"
    relative = f"assets/icons/custom/{filename}"
    target = safe_project_path(project_root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    manifest = load_manifest(project_root)
    result = {
        "key": key,
        "requested": title or key,
        "state": "Synced",
        "provider": "user",
        "sourceUrl": "",
        "localPath": relative,
        "sha256": sha256_file(target),
        "license": "User supplied; usage rights must be confirmed by the user.",
        "message": "",
        "updatedAt": utc_now(),
    }
    _upsert(manifest, result)
    manifest["updatedAt"] = utc_now()
    write_json(manifest_file(project_root), manifest)
    return result


def svg_data_uri(path: Path) -> str:
    data = path.read_bytes()
    safe, reason = _svg_is_safe(data)
    if not safe:
        raise ValueError(reason)
    return "data:image/svg+xml," + quote(data.decode("utf-8"), safe="")


def mark_assets(project_root: Path, keys: set[str], state: str) -> None:
    if state not in {"Embedded", "RenderVerified"}:
        raise ValueError(f"Unsupported asset transition target: {state}")
    manifest = load_manifest(project_root)
    changed = False
    for asset in manifest.get("assets", []):
        if asset.get("key") in keys and asset.get("state") in {"Synced", "Embedded", "RenderVerified"} and asset.get("state") != state:
            asset["state"] = state
            asset["updatedAt"] = utc_now()
            changed = True
    if changed:
        manifest["updatedAt"] = utc_now()
        write_json(manifest_file(project_root), manifest)

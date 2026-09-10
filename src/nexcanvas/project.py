#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexcanvas.assets import load_manifest, manifest_file
from nexcanvas.common import sha256_json, slugify, utc_now, write_json
from nexcanvas.intents import DEFAULT_ROUTES, VIEW_INTENTS, classify_brief, compatible_view_intents, default_view_intent
from nexcanvas.model_v3 import migrate_v2_model
from nexcanvas.registry import resolve_route, resolve_theme
from nexcanvas.archetypes import resolve_archetype
from nexcanvas.runtime import inspect_runtime
from nexcanvas.pipeline import initialize_project_state


def init_project(args: argparse.Namespace) -> dict[str, object]:
    slug = slugify(args.name)
    explicit_root = getattr(args, "project_root", None)
    output_root = getattr(args, "output_root", Path("nexcanvas-output"))
    project_root = (explicit_root if explicit_root is not None else output_root / slug).resolve()
    protected = ["source_model.json", "diagram_lock.json", "diagram_model.json", "project_state.json"]
    existing = [name for name in protected if (project_root / name).exists()]
    if existing and not args.force:
        raise FileExistsError(f"Project already contains NexCanvas contracts: {', '.join(existing)}. Use --force to replace only these generated contracts.")
    family_arg = getattr(args, "family", None)
    profile_arg = getattr(args, "profile", None)
    if bool(family_arg) != bool(profile_arg):
        raise ValueError("--family and --profile must be supplied together, or both omitted for brief-first routing.")
    requested_intent = str(getattr(args, "view_intent", "auto") or "auto")
    brief = str(getattr(args, "brief", "") or "").strip()
    if family_arg and profile_arg:
        family, profile = str(family_arg), str(profile_arg)
        view_intent = default_view_intent(family, profile) if requested_intent == "auto" else requested_intent
    else:
        view_intent = classify_brief(brief)["viewIntent"] if requested_intent == "auto" and brief else ("architecture" if requested_intent == "auto" else requested_intent)
        family, profile = DEFAULT_ROUTES[view_intent]
    if view_intent not in compatible_view_intents(family, profile):
        supported = ", ".join(sorted(compatible_view_intents(family, profile)))
        raise ValueError(f"view intent {view_intent!r} is incompatible with {family}/{profile}; supported: {supported}")
    route = resolve_route(family, profile)
    resolve_theme(args.theme)
    archetype = resolve_archetype(args.visual_archetype)
    for relative in ("assets", "artifacts", "reports"):
        (project_root / relative).mkdir(parents=True, exist_ok=True)

    facts = []
    if brief:
        facts.append({"id": "fact-brief", "claim": brief, "evidence": ["conversation-1"], "confidence": "confirmed"})
    source = {
        "schemaVersion": "2.0",
        "status": "draft",
        "sources": [{"id": "conversation-1", "type": "conversation", "location": "Current user request", "snapshot": utc_now()}],
        "facts": facts,
        "assumptions": [],
        "exclusions": [],
    }
    legacy_model = {
        "schemaVersion": "2.0",
        "title": args.name,
        "showTitle": False,
        "viewIntent": view_intent,
        "route": {"family": family, "profile": profile},
        "audience": args.audience,
        "deliveryTarget": args.delivery_target,
        "language": args.language,
        "theme": args.theme,
        "visualArchetype": archetype["key"],
        "direction": args.direction,
        "canvas": {"width": args.width, "height": args.height},
        "boundaries": [],
        "nodes": [{"id": "system", "label": args.name, "kind": "system", "importance": "primary", "evidence": ["fact-brief"] if brief else []}],
        "edges": [],
        "legend": [],
        "sourceSnapshot": "source_model.json",
        "assumptions": [],
    }
    model = migrate_v2_model(legacy_model, source)
    lock = {
        "schemaVersion": "2.0",
        "status": "draft",
        "viewIntent": view_intent,
        "route": legacy_model["route"],
        "theme": args.theme,
        "visualArchetype": archetype["key"],
        "canvas": legacy_model["canvas"],
        "sourceHash": sha256_json(source),
        "decisions": {
            "audience": args.audience,
            "viewIntent": view_intent,
            "deliveryTarget": args.delivery_target,
            "notation": route["notation"],
            "layout": route["layout"],
            "visualArchetype": archetype["key"],
            "assetPolicy": "verified-exact-or-generic",
        },
    }
    write_json(project_root / "source_model.json", source)
    write_json(project_root / "diagram_model.json", model)
    write_json(project_root / "diagram_lock.json", lock)
    write_json(manifest_file(project_root), load_manifest(project_root))
    write_json(project_root / "reports" / "runtime.json", inspect_runtime())
    initialize_project_state(project_root, replace=True)
    return {
        "projectRoot": str(project_root),
        "slug": slug,
        "usedDefaultOutput": explicit_root is None,
        "viewIntent": view_intent,
        "route": legacy_model["route"],
        "created": protected + ["assets/asset_manifest.json", "reports/runtime.json"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a contract-first NexCanvas diagram project.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="Initialize a project directory.")
    init.add_argument(
        "project_root",
        type=Path,
        nargs="?",
        help="Project directory. Defaults to <output-root>/<slug>.",
    )
    init.add_argument(
        "--output-root",
        type=Path,
        default=Path("nexcanvas-output"),
        help="Parent directory used when project_root is omitted (default: ./nexcanvas-output).",
    )
    init.add_argument("--name", required=True)
    init.add_argument("--brief", help="Plain-language diagram brief used for automatic semantic intent routing.")
    init.add_argument("--view-intent", choices=["auto", *sorted(VIEW_INTENTS)], default="auto")
    init.add_argument("--family", help="Optional advanced route family; supply together with --profile.")
    init.add_argument("--profile", help="Optional advanced route profile; supply together with --family.")
    init.add_argument("--theme", default="technical-editorial")
    init.add_argument("--visual-archetype", default="technical-editorial")
    init.add_argument("--audience", default="engineering stakeholders")
    init.add_argument("--delivery-target", choices=["readme", "engineering-doc", "slide", "poster", "print", "interactive"], default="engineering-doc")
    init.add_argument("--language", default="en")
    init.add_argument("--direction", choices=["LR", "RL", "TB", "BT"], default="LR")
    init.add_argument("--width", type=int, default=1600)
    init.add_argument("--height", type=int, default=900)
    init.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        result = init_project(args)
    except (FileExistsError, KeyError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

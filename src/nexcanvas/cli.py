from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from . import __version__
from .assets import load_catalog, search_catalog, sync_catalog_asset, sync_provider_asset, sync_user_asset
from .builder import build_drawio
from .common import load_json, utc_now, write_json
from .contracts import validate_file, validate_repository_snapshot
from .geometry import run_checks as run_geometry_checks
from .intents import DEFAULT_ROUTES, VIEW_INTENTS, classify_brief
from .model_v3 import migrate_file
from .planning import brainstorm_layout
from .pipeline import run_generate
from .postflight import run_postflight
from .project import init_project
from .quality import run_quality, summarize
from .registry import resolve_route
from .rendering import render_drawio
from .repository import inspect_repository, verify_repository_evidence
from .repository_analysis import analyze_repository, diff_repository_snapshots
from .runtime import inspect_runtime
from .semantic_sync import sync_project
from .visual import create_visual_report


Handler = Callable[[argparse.Namespace], int]


def _emit(value: dict[str, Any], output: Path | None = None) -> None:
    if output:
        write_json(output.resolve(), value)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _doctor(args: argparse.Namespace) -> int:
    report = inspect_runtime()
    _emit(report, args.output)
    return 0 if report["capabilities"]["authorNativeDrawio"] else 1


def _init(args: argparse.Namespace) -> int:
    _emit(init_project(args))
    return 0


def _analyze_capture(args: argparse.Namespace) -> int:
    source_model_path = args.source_model.resolve() if args.source_model else None
    entry = inspect_repository(
        args.repo_root.resolve(), args.source_id, source_model_path.parent if source_model_path else None
    )
    if source_model_path:
        model = load_json(source_model_path)
        sources = [
            source
            for source in model.get("sources", [])
            if isinstance(source, dict) and source.get("id") != args.source_id
        ]
        sources.append(entry)
        model["sources"] = sources
        write_json(source_model_path, model)
    _emit(entry, args.output)
    return 0


def _analyze_verify(args: argparse.Namespace) -> int:
    model = load_json(args.source_model.resolve())
    issues = verify_repository_evidence(model, args.repo_root.resolve())
    report = {
        "ok": not any(issue.severity == "error" for issue in issues),
        "issues": [issue.to_dict() for issue in issues],
    }
    _emit(report, args.output)
    return 0 if report["ok"] else 1


def _analyze_snapshot(args: argparse.Namespace) -> int:
    previous = load_json(args.previous.resolve()) if args.previous else None
    if previous is not None:
        errors = [issue for issue in validate_repository_snapshot(previous) if issue.severity == "error"]
        if errors:
            raise ValueError(f"Previous repository snapshot is invalid: {errors[0].code}: {errors[0].message}")
    snapshot = analyze_repository(
        args.repo_root.resolve(),
        source_id=args.source_id,
        previous_snapshot=previous,
        include=args.include,
        exclude=args.exclude,
        max_files=args.max_files,
    )
    _emit(snapshot, args.output)
    return 0


def _analyze_diff(args: argparse.Namespace) -> int:
    before = load_json(args.before.resolve())
    after = load_json(args.after.resolve())
    for label, value in (("before", before), ("after", after)):
        errors = [issue for issue in validate_repository_snapshot(value) if issue.severity == "error"]
        if errors:
            raise ValueError(f"{label} repository snapshot is invalid: {errors[0].code}: {errors[0].message}")
    _emit(diff_repository_snapshots(before, after), args.output)
    return 0


def _plan(args: argparse.Namespace) -> int:
    report = brainstorm_layout(load_json(args.model.resolve()))
    _emit(report, args.output)
    return 0


def _build(args: argparse.Namespace) -> int:
    result = build_drawio(
        args.model.resolve(),
        args.output.resolve(),
        project_root=args.project_root.resolve() if args.project_root else None,
    )
    if args.proof:
        write_json(args.proof.resolve(), result)
    _emit(result)
    return 0


def _render(args: argparse.Namespace) -> int:
    source = args.source.resolve()
    output = args.output.resolve()
    inferred_root = source.parent.parent if source.parent.name == "artifacts" else None
    result = render_drawio(source, output, args.format, args.scale, report_root=inferred_root)
    _emit(result, args.report)
    return 0


def _qa_diagram(args: argparse.Namespace) -> int:
    model = load_json(args.model.resolve())
    source = load_json(args.source_model.resolve()) if args.source_model else None
    drawio = args.drawio.resolve() if args.drawio else None
    issues = run_quality(
        model,
        source,
        args.project_root.resolve() if args.project_root else None,
        drawio,
        repo_root=args.repo_root.resolve() if args.repo_root else None,
    )
    report = summarize(issues)
    report["schemaVersion"] = "2.0"
    report["checkedAt"] = utc_now()
    if drawio and drawio.is_file():
        route = resolve_route(model["route"]["family"], model["route"]["profile"])
        errors, warnings = run_geometry_checks(drawio, args.padding, str(route["geometryQa"]))
        report["geometry"] = {"profile": route["geometryQa"], "errors": errors, "warnings": warnings}
        report["counts"]["error"] += len(errors)
        report["counts"]["warning"] += len(warnings)
        report["ok"] = report["counts"]["error"] == 0
    _emit(report, args.output)
    failed = not report["ok"] or (args.fail_on_warning and report["counts"]["warning"] > 0)
    return 1 if failed else 0


def _qa_visual(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    inferred_root = output.parent.parent if output.parent.name == "reports" else None
    report = create_visual_report(
        args.artifact.resolve(),
        args.expected_width,
        args.expected_height,
        args.approve,
        args.reviewer,
        args.notes,
        inferred_root,
    )
    _emit(report, output)
    return 0 if report["ok"] else 1


def _postflight(args: argparse.Namespace) -> int:
    report = run_postflight(
        args.project_root.resolve(), repo_root=args.repo_root.resolve() if args.repo_root else None
    )
    _emit(report, args.output)
    return 0 if report["ok"] else 1


def _generate(args: argparse.Namespace) -> int:
    result = run_generate(
        args.project_root,
        repo_root=args.repo_root,
        render_format=args.render_format,
        scale=args.scale,
        expected_width=args.expected_width,
        expected_height=args.expected_height,
        approve_visual=args.approve_visual,
        reviewer=args.reviewer,
        notes=args.notes,
        padding=args.padding,
        fail_on_warning=not args.allow_warnings,
        restart=args.restart,
    )
    _emit(result)
    return int(result["exitCode"])


def _sync(args: argparse.Namespace) -> int:
    result = sync_project(
        args.project_root,
        args.repo_root,
        dry_run=args.dry_run,
        source_id=args.source_id,
        include=args.include,
        exclude=args.exclude,
        max_files=args.max_files,
        confirmed_removals=set(args.confirm_removal or []),
        output=args.output,
    )
    _emit(result)
    return 0 if args.dry_run or result["complete"] else 1


def _intent(args: argparse.Namespace) -> int:
    result = classify_brief(args.brief)
    family, profile = DEFAULT_ROUTES[result["viewIntent"]]
    result["defaultRoute"] = {"family": family, "profile": profile}
    _emit(result)
    return 0


def _migrate_v2_to_v3(args: argparse.Namespace) -> int:
    input_model = load_json(args.model.resolve())
    if not isinstance(input_model, dict) or input_model.get("schemaVersion") != "2.0":
        raise ValueError("v2-to-v3 requires an input diagram model with schemaVersion '2.0'.")
    result = migrate_file(
        args.model,
        args.output,
        source_path=args.source_model,
        force=args.force,
    )
    _emit(result)
    return 0


def _contract(args: argparse.Namespace) -> int:
    issues = validate_file(
        args.path.resolve(),
        args.kind,
        project_root=args.project_root.resolve() if args.project_root else None,
    )
    report = {
        "ok": not any(issue.severity == "error" for issue in issues),
        "issues": [issue.to_dict() for issue in issues],
    }
    _emit(report)
    return 0 if report["ok"] else 1


def _asset_search(args: argparse.Namespace) -> int:
    results = search_catalog(args.query, limit=args.limit) if args.query else load_catalog().get("entries", [])[: args.limit]
    _emit({"count": len(results), "results": results})
    return 0 if results else 1


def _asset_sync(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    if args.user_svg:
        result = sync_user_asset(project_root, args.query, args.user_svg.resolve(), args.title)
    elif args.provider:
        result = sync_provider_asset(
            project_root,
            args.provider,
            args.query,
            source_archive=args.source_archive.resolve() if args.source_archive else None,
            accept_terms=args.accept_terms,
        )
    else:
        result = sync_catalog_asset(
            project_root, args.query, offline=args.offline, generic_fallback=args.generic_fallback
        )
    _emit(result)
    return 2 if result.get("state") == "NeedsManual" else 0


def _set_handler(parser: argparse.ArgumentParser, handler: Handler) -> None:
    parser.set_defaults(handler=handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexcanvas",
        description="Build and verify editable, evidence-grounded Draw.io diagrams.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="Inspect runtime capabilities.")
    doctor.add_argument("--output", type=Path)
    _set_handler(doctor, _doctor)

    init = commands.add_parser("init", help="Initialize a contract-first diagram project.")
    init.add_argument("project_root", type=Path, nargs="?")
    init.add_argument("--output-root", type=Path, default=Path("nexcanvas-output"))
    init.add_argument("--name", required=True)
    init.add_argument("--brief", default="")
    init.add_argument("--view-intent", choices=["auto", *sorted(VIEW_INTENTS)], default="auto")
    init.add_argument("--family")
    init.add_argument("--profile")
    init.add_argument("--theme", default="technical-editorial")
    init.add_argument("--visual-archetype", default="technical-editorial")
    init.add_argument("--audience", default="engineering stakeholders")
    init.add_argument(
        "--delivery-target",
        choices=["readme", "engineering-doc", "slide", "poster", "print", "interactive"],
        default="engineering-doc",
    )
    init.add_argument("--language", default="en")
    init.add_argument("--direction", choices=["LR", "RL", "TB", "BT"], default="LR")
    init.add_argument("--width", type=int, default=1600)
    init.add_argument("--height", type=int, default=900)
    init.add_argument("--force", action="store_true")
    _set_handler(init, _init)

    analyze = commands.add_parser("analyze", help="Capture or verify revision-pinned repository evidence.")
    analyze_commands = analyze.add_subparsers(dest="analyze_command", required=True)
    capture = analyze_commands.add_parser("capture", help="Capture a Git repository evidence source.")
    capture.add_argument("repo_root", type=Path)
    capture.add_argument("--source-id", default="repository-1")
    capture.add_argument("--source-model", type=Path)
    capture.add_argument("--output", type=Path)
    _set_handler(capture, _analyze_capture)
    verify = analyze_commands.add_parser("verify", help="Verify pinned repository evidence.")
    verify.add_argument("source_model", type=Path)
    verify.add_argument("--repo-root", type=Path, required=True)
    verify.add_argument("--output", type=Path)
    _set_handler(verify, _analyze_verify)
    snapshot = analyze_commands.add_parser("snapshot", help="Analyze tracked Python and TypeScript/JavaScript modules at HEAD.")
    snapshot.add_argument("repo_root", type=Path)
    snapshot.add_argument("--source-id", default="repository-sync")
    snapshot.add_argument("--previous", type=Path, help="Previous snapshot used for rename-aware stable IDs.")
    snapshot.add_argument("--include", action="append", help="Git-style path pattern; repeat to add scopes.")
    snapshot.add_argument("--exclude", action="append", help="Git-style path pattern; repeat to add exclusions.")
    snapshot.add_argument("--max-files", type=int, default=500)
    snapshot.add_argument("--output", "-o", type=Path)
    _set_handler(snapshot, _analyze_snapshot)
    diff = analyze_commands.add_parser("diff", help="Compare two repository snapshots by stable semantic ID.")
    diff.add_argument("before", type=Path)
    diff.add_argument("after", type=Path)
    diff.add_argument("--output", "-o", type=Path)
    _set_handler(diff, _analyze_diff)

    plan = commands.add_parser("plan", help="Score layout candidates before geometry generation.")
    plan.add_argument("model", type=Path)
    plan.add_argument("--output", type=Path)
    _set_handler(plan, _plan)

    build = commands.add_parser("build", help="Build native editable Draw.io XML.")
    build.add_argument("model", type=Path)
    build.add_argument("--output", "-o", type=Path, required=True)
    build.add_argument("--project-root", type=Path)
    build.add_argument("--proof", type=Path)
    _set_handler(build, _build)

    render = commands.add_parser("render", help="Render a Draw.io artifact to PNG, SVG, or PDF.")
    render.add_argument("source", type=Path)
    render.add_argument("--output", "-o", type=Path, required=True)
    render.add_argument("--format", choices=["png", "svg", "pdf"])
    render.add_argument("--scale", type=float, default=1.0)
    render.add_argument("--report", type=Path)
    _set_handler(render, _render)

    qa = commands.add_parser("qa", help="Run diagram or rendered-image quality gates.")
    qa_commands = qa.add_subparsers(dest="qa_command", required=True)
    diagram = qa_commands.add_parser("diagram", help="Run contract, semantic, asset, and geometry QA.")
    diagram.add_argument("model", type=Path)
    diagram.add_argument("--drawio", type=Path)
    diagram.add_argument("--source-model", type=Path)
    diagram.add_argument("--project-root", type=Path)
    diagram.add_argument("--repo-root", type=Path)
    diagram.add_argument("--padding", type=float, default=10.0)
    diagram.add_argument("--output", type=Path)
    diagram.add_argument("--fail-on-warning", action="store_true")
    _set_handler(diagram, _qa_diagram)
    visual = qa_commands.add_parser("visual", help="Record rendered-image checks and explicit approval.")
    visual.add_argument("artifact", type=Path)
    visual.add_argument("--expected-width", type=int)
    visual.add_argument("--expected-height", type=int)
    visual.add_argument("--approve", action="store_true")
    visual.add_argument("--reviewer", default="")
    visual.add_argument("--notes", default="")
    visual.add_argument("--output", type=Path, required=True)
    _set_handler(visual, _qa_visual)

    postflight = commands.add_parser("postflight", help="Verify provenance and every delivery gate.")
    postflight.add_argument("project_root", type=Path)
    postflight.add_argument("--repo-root", type=Path)
    postflight.add_argument("--output", type=Path)
    _set_handler(postflight, _postflight)

    generate = commands.add_parser("generate", help="Run or safely resume the hash-bound delivery pipeline.")
    generate.add_argument("project_root", type=Path)
    generate.add_argument("--repo-root", type=Path)
    generate.add_argument("--render-format", choices=["png", "svg", "pdf"], default="png")
    generate.add_argument("--scale", type=float, default=1.0)
    generate.add_argument("--expected-width", type=int)
    generate.add_argument("--expected-height", type=int)
    generate.add_argument("--approve-visual", action="store_true")
    generate.add_argument("--reviewer", default="")
    generate.add_argument("--notes", default="")
    generate.add_argument("--padding", type=float, default=10.0)
    generate.add_argument("--allow-warnings", action="store_true")
    generate.add_argument("--restart", action="store_true")
    _set_handler(generate, _generate)

    sync = commands.add_parser("sync", help="Three-way reconcile repository semantics with a Diagram Model V3 project.")
    sync.add_argument("project_root", type=Path)
    sync.add_argument("--repo-root", type=Path, required=True)
    mode = sync.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print the sync plan without modifying project files.")
    mode.add_argument("--apply", action="store_true", help="Apply safe changes and preserve reported conflicts.")
    sync.add_argument("--source-id", default="repository-sync")
    sync.add_argument("--include", action="append", help="Path pattern; repeat to add scopes.")
    sync.add_argument("--exclude", action="append", help="Path pattern; repeat to add exclusions.")
    sync.add_argument("--max-files", type=int)
    sync.add_argument("--confirm-removal", action="append", default=[], help="Stable semantic ID approved for removal; repeat per ID.")
    sync.add_argument("--output", type=Path, help="Optional plan/report path.")
    _set_handler(sync, _sync)

    migrate = commands.add_parser("migrate", help="Migrate persisted NexCanvas contracts without rewriting the source.")
    migrate_commands = migrate.add_subparsers(dest="migrate_command", required=True)
    v2_to_v3 = migrate_commands.add_parser("v2-to-v3", help="Create a canonical diagram model V3 from a diagram model V2.")
    v2_to_v3.add_argument("model", type=Path)
    v2_to_v3.add_argument("--output", "-o", type=Path, required=True)
    v2_to_v3.add_argument("--source-model", type=Path)
    v2_to_v3.add_argument("--force", action="store_true", help="Replace only the requested output file if it already exists.")
    _set_handler(v2_to_v3, _migrate_v2_to_v3)

    intent = commands.add_parser("intent", help="Infer semantic view intent from a brief.")
    intent.add_argument("brief")
    _set_handler(intent, _intent)

    contract = commands.add_parser("contract", help="Validate one persisted NexCanvas contract.")
    contract.add_argument(
        "kind", choices=["source-model", "diagram-lock", "diagram-model", "asset-manifest", "project-state", "repository-snapshot", "sync-plan"]
    )
    contract.add_argument("path", type=Path)
    contract.add_argument("--project-root", type=Path)
    _set_handler(contract, _contract)

    asset = commands.add_parser("asset", help="Search or sync verified diagram assets.")
    asset_commands = asset.add_subparsers(dest="asset_command", required=True)
    search = asset_commands.add_parser("search", help="Search the pinned technology icon catalog.")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--limit", type=int, default=10)
    _set_handler(search, _asset_search)
    sync = asset_commands.add_parser("sync", help="Sync a verified asset into a project.")
    sync.add_argument("project_root", type=Path)
    sync.add_argument("query")
    sync.add_argument("--user-svg", type=Path)
    sync.add_argument("--title")
    sync.add_argument("--provider")
    sync.add_argument("--source-archive", type=Path)
    sync.add_argument("--accept-terms", action="store_true")
    sync.add_argument("--offline", action="store_true")
    sync.add_argument("--generic-fallback", action="store_true")
    _set_handler(sync, _asset_sync)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileExistsError, KeyError, OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

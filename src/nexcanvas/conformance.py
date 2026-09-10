from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .common import load_json, portable_path, resource_root, sha256_file, sha256_json, utc_now, write_json
from .contracts import validate_diagram_model, validate_lock, validate_manifest, validate_source_model
from .model_v3 import normalize_diagram_model
from .postflight import run_postflight


DIMENSIONS = ("semantics", "evidence", "assets", "routing", "gates")
PASS_THRESHOLD = 1.0
HOST_STATES = {"verified", "not-run", "unavailable", "failed"}
HASH_KEYS = {"skillSha256", "adapterSha256", "caseSha256", "requestSha256", "projectArtifactsSha256"}


def _data_root(root: Path | None = None) -> Path:
    return (root or resource_root()) / "conformance"


def load_suite(root: Path | None = None) -> dict[str, Any]:
    suite = load_json(_data_root(root) / "suite.json")
    errors = validate_suite(suite)
    if errors:
        raise ValueError(f"Invalid conformance suite: {errors[0]}")
    return suite


def load_adapters(root: Path | None = None) -> list[dict[str, Any]]:
    adapters: list[dict[str, Any]] = []
    for path in sorted((_data_root(root) / "hosts").glob("*.json")):
        adapter = load_json(path)
        errors = validate_adapter(adapter)
        if errors:
            raise ValueError(f"Invalid host adapter {path.name}: {errors[0]}")
        adapter["_path"] = path
        adapters.append(adapter)
    return adapters


def validate_suite(suite: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(suite, dict) or suite.get("schemaVersion") != "1.0":
        return ["schemaVersion must be '1.0'."]
    if not isinstance(suite.get("suiteId"), str) or not suite["suiteId"].strip():
        issues.append("suiteId must be a non-empty string.")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        return issues + ["cases must be a non-empty array."]
    ids: set[str] = set()
    intents: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            issues.append(f"cases[{index}] must be an object.")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            issues.append(f"cases[{index}].id must be a non-empty string.")
        elif case_id in ids:
            issues.append(f"Duplicate case id: {case_id}.")
        else:
            ids.add(case_id)
        prompt = case.get("prompt")
        if not isinstance(prompt, dict) or not all(isinstance(prompt.get(key), str) and prompt[key].strip() for key in ("language", "text")):
            issues.append(f"cases[{index}].prompt requires non-empty language and text.")
        expected = case.get("expectations")
        if not isinstance(expected, dict):
            issues.append(f"cases[{index}].expectations must be an object.")
            continue
        intent = expected.get("viewIntent")
        if isinstance(intent, str):
            intents.add(intent)
        for key in ("minNodes", "minEdges"):
            if not isinstance(expected.get(key), int) or expected[key] < 0:
                issues.append(f"cases[{index}].expectations.{key} must be a non-negative integer.")
    required_intents = {"architecture", "workflow", "sequence", "data-flow", "lifecycle"}
    missing = required_intents - intents
    if missing:
        issues.append(f"Suite does not cover intents: {', '.join(sorted(missing))}.")
    return issues


def validate_adapter(adapter: Any) -> list[str]:
    if not isinstance(adapter, dict) or adapter.get("schemaVersion") != "1.0":
        return ["schemaVersion must be '1.0'."]
    issues: list[str] = []
    for key in ("id", "displayName"):
        if not isinstance(adapter.get(key), str) or not adapter[key].strip():
            issues.append(f"{key} must be a non-empty string.")
    if adapter.get("sharedSkill") != "SKILL.md":
        issues.append("sharedSkill must be SKILL.md; adapters cannot fork the workflow.")
    if adapter.get("execution") not in {"automated-cli", "manual-export"}:
        issues.append("execution must be automated-cli or manual-export.")
    for key in ("discoveryPaths", "evidence", "limitations"):
        if not isinstance(adapter.get(key), list):
            issues.append(f"{key} must be an array.")
    return issues


def validate_result(result: Any) -> list[str]:
    if not isinstance(result, dict) or result.get("schemaVersion") != "1.0":
        return ["conformance result schemaVersion must be '1.0'."]
    issues: list[str] = []
    mode = result.get("mode")
    status = result.get("status")
    if mode not in {"fixture", "observed"}:
        issues.append("mode must be fixture or observed.")
    if status not in {"fixture", "verified", "failed"}:
        issues.append("status must be fixture, verified, or failed.")
    if mode == "fixture" and status != "fixture":
        issues.append("Fixture results must use status fixture.")
    if mode == "observed" and status not in {"verified", "failed"}:
        issues.append("Observed results must use status verified or failed.")
    if mode == "observed" and not isinstance(result.get("execution"), dict):
        issues.append("Observed results must embed their execution record.")
    for key in ("resultId", "hostId", "caseId", "evaluatedAt"):
        if not isinstance(result.get(key), str) or not result[key].strip():
            issues.append(f"{key} must be a non-empty string.")
    dimensions = result.get("dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        issues.append(f"dimensions must contain exactly: {', '.join(DIMENSIONS)}.")
    else:
        scores = []
        for name in DIMENSIONS:
            score = dimensions[name].get("score") if isinstance(dimensions[name], dict) else None
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
                issues.append(f"dimensions.{name}.score must be between 0 and 1.")
            else:
                scores.append(float(score))
        expected_pass = len(scores) == len(DIMENSIONS) and all(score >= PASS_THRESHOLD for score in scores)
        if result.get("passed") is not expected_pass:
            issues.append("passed does not match the dimension threshold.")
        if mode == "observed" and status == "verified" and not expected_pass:
            issues.append("A verified result must pass every dimension.")
        if mode == "observed" and status == "failed" and expected_pass:
            issues.append("A failed result must fail at least one dimension.")
    digests = result.get("digests")
    if not isinstance(digests, dict) or not HASH_KEYS.issubset(digests):
        issues.append("digests must bind the skill, adapter, case, request, and project artifacts.")
    elif any(not isinstance(digests[key], str) or len(digests[key]) != 64 for key in HASH_KEYS):
        issues.append("Every conformance digest must be a 64-character SHA-256 value.")
    return issues


def host_capabilities(root: Path | None = None) -> dict[str, Any]:
    hosts = []
    for adapter in load_adapters(root):
        executables = adapter.get("executableNames", [])
        resolved = {name: shutil.which(name) for name in executables}
        available = any(resolved.values()) if executables else False
        hosts.append(
            {
                "id": adapter["id"],
                "displayName": adapter["displayName"],
                "available": available,
                "state": "not-run" if available else "unavailable",
                "execution": adapter["execution"],
                "discoveryPaths": adapter["discoveryPaths"],
                "executables": resolved,
                "limitations": adapter["limitations"],
            }
        )
    return {"schemaVersion": "1.0", "checkedAt": utc_now(), "hosts": hosts}


def prepare_run(case_id: str, host_id: str, output: Path, root: Path | None = None) -> dict[str, Any]:
    distribution = root or resource_root()
    suite = load_suite(distribution)
    cases = {case["id"]: case for case in suite["cases"]}
    adapters = {adapter["id"]: adapter for adapter in load_adapters(distribution)}
    if case_id not in cases:
        raise ValueError(f"Unknown conformance case: {case_id}")
    if host_id not in adapters:
        raise ValueError(f"Unknown conformance host: {host_id}")
    case = cases[case_id]
    adapter = adapters[host_id]
    skill_path = distribution / "SKILL.md"
    adapter_path = Path(adapter["_path"])
    request = {
        "schemaVersion": "1.0",
        "suiteId": suite["suiteId"],
        "hostId": host_id,
        "caseId": case_id,
        "createdAt": utc_now(),
        "digests": {
            "skillSha256": sha256_file(skill_path),
            "adapterSha256": sha256_file(adapter_path),
            "caseSha256": sha256_json(case),
        },
        "prompt": case["prompt"],
        "expectedOutput": "project",
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "request.json", request)
    template = {
        "schemaVersion": "1.0",
        "mode": "observed",
        "hostId": host_id,
        "hostVersion": "REPLACE_WITH_HOST_VERSION",
        "surface": "REPLACE_WITH_HOST_SURFACE",
        "caseId": case_id,
        "startedAt": "REPLACE_WITH_UTC_TIMESTAMP",
        "completedAt": "REPLACE_WITH_UTC_TIMESTAMP",
        "requestSha256": sha256_file(output / "request.json"),
        **request["digests"],
        "invocation": "REPLACE_WITH_HOST_AND_SURFACE",
        "evidence": [{"path": "REPLACE_WITH_TRANSCRIPT_OR_TASK_EXPORT", "sha256": "REPLACE_WITH_SHA256"}],
    }
    write_json(output / "execution.template.json", template)
    prompt = (
        f"Use the installed NexCanvas Draw.io skill to complete this conformance case.\n\n"
        f"{case['prompt']['text']}\n\n"
        "Requirements:\n"
        "- Follow the shared SKILL.md workflow; do not substitute Mermaid or a flattened image.\n"
        "- Write the complete editable project to the `project` directory beside request.json.\n"
        "- Run every applicable NexCanvas QA and postflight gate.\n"
        "- Preserve the session/task transcript as an evidence file.\n"
        "- Fill execution.template.json and save it as execution.json only after the run.\n"
    )
    (output / "PROMPT.md").write_text(prompt, encoding="utf-8", newline="\n")
    return {"request": portable_path(output / "request.json"), "prompt": portable_path(output / "PROMPT.md")}


def _text(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def _score(checks: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(checks)
    passed = sum(bool(item["ok"]) for item in values)
    return {"score": round(passed / len(values), 4) if values else 1.0, "passed": passed, "total": len(values), "checks": values}


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _model_parts(model: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    projection = normalize_diagram_model(model)
    return list(projection.get("nodes", [])), list(projection.get("edges", []))


def _matches(node: dict[str, Any], aliases: list[str]) -> bool:
    haystack = _text(f"{node.get('label', '')} {node.get('caption', '')} {node.get('id', '')}")
    return any(_text(alias) in haystack for alias in aliases)


def _semantic_checks(model: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    nodes, edges = _model_parts(model)
    checks = [
        _check("minimum-nodes", len(nodes) >= expected["minNodes"], f"{len(nodes)} >= {expected['minNodes']}"),
        _check("minimum-edges", len(edges) >= expected["minEdges"], f"{len(edges)} >= {expected['minEdges']}"),
    ]
    by_id = {str(node.get("id")): node for node in nodes}
    for index, aliases in enumerate(expected.get("requiredConcepts", []), 1):
        found = any(_matches(node, aliases) for node in nodes)
        checks.append(_check(f"required-concept-{index}", found, " | ".join(aliases)))
    for index, pair in enumerate(expected.get("requiredEdgePairs", []), 1):
        found = False
        for edge in edges:
            source = by_id.get(str(edge.get("source")), {})
            target = by_id.get(str(edge.get("target")), {})
            if _matches(source, pair["source"]) and _matches(target, pair["target"]):
                found = True
                break
        checks.append(_check(f"required-edge-{index}", found, f"{pair['source']} -> {pair['target']}"))
    return checks


def _evidence_checks(source: dict[str, Any], model: dict[str, Any]) -> list[dict[str, Any]]:
    nodes, edges = _model_parts(model)
    facts = {str(fact.get("id")) for fact in source.get("facts", []) if isinstance(fact, dict)}
    referenced = [item for item in [*nodes, *edges] if item.get("importance", "primary") == "primary"]
    valid_refs = all(
        isinstance(item.get("evidence"), list)
        and bool(item["evidence"])
        and all(str(reference) in facts for reference in item["evidence"])
        for item in referenced
    )
    facts_grounded = all(
        isinstance(fact.get("evidence"), list) and bool(fact["evidence"])
        for fact in source.get("facts", [])
        if isinstance(fact, dict)
    )
    return [
        _check("source-confirmed", source.get("status") == "confirmed", str(source.get("status"))),
        _check("source-contract", not any(issue.severity == "error" for issue in validate_source_model(source)), "source_model.json"),
        _check("facts-grounded", bool(facts) and facts_grounded, f"{len(facts)} facts"),
        _check("primary-semantics-grounded", bool(referenced) and valid_refs, f"{len(referenced)} primary items"),
    ]


def _asset_checks(project: Path, model: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_path = project / "assets" / "asset_manifest.json"
    if not manifest_path.is_file():
        return [_check("asset-manifest", False, "assets/asset_manifest.json missing")]
    manifest = load_json(manifest_path)
    nodes, _ = _model_parts(model)
    entries = {str(item.get("key")): item for item in manifest.get("assets", []) if isinstance(item, dict)}
    checks = [_check("asset-contract", not any(issue.severity == "error" for issue in validate_manifest(manifest, project)), "asset_manifest.json")]
    referenced = {str(node.get("assetRef")) for node in nodes if node.get("assetRef")}
    checks.append(_check("referenced-assets-resolved", all(key in entries and entries[key].get("state") in {"Embedded", "RenderVerified"} for key in referenced), f"{len(referenced)} references"))
    for key in expected.get("requiredAssetKeys", []):
        entry = entries.get(key, {})
        checks.append(_check(f"required-asset-{key}", entry.get("state") in {"Embedded", "RenderVerified"}, key))
    return checks


def _routing_checks(project: Path, model: dict[str, Any], lock: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    projection = normalize_diagram_model(model)
    route = projection.get("route", {})
    route_key = f"{route.get('family')}/{route.get('profile')}"
    intent = projection.get("viewIntent")
    lock_route = lock.get("route", {})
    lock_route_key = f"{lock_route.get('family')}/{lock_route.get('profile')}"
    return [
        _check("diagram-contract", not any(issue.severity == "error" for issue in validate_diagram_model(model)), "diagram_model.json"),
        _check("lock-contract", not any(issue.severity == "error" for issue in validate_lock(lock)), "diagram_lock.json"),
        _check("view-intent", intent == expected["viewIntent"], f"{intent!r} == {expected['viewIntent']!r}"),
        _check("allowed-route", route_key in expected.get("allowedRoutes", []), route_key),
        _check("lock-alignment", lock.get("viewIntent") == intent and lock_route_key == route_key, lock_route_key),
        _check("layout-brainstorm", not expected.get("requiresLayoutBrainstorm") or (project / "reports" / "layout_brainstorm.json").is_file(), "reports/layout_brainstorm.json"),
    ]


def _gate_checks(project: Path) -> list[dict[str, Any]]:
    diagram_qa = load_json(project / "reports" / "diagram_qa.json") if (project / "reports" / "diagram_qa.json").is_file() else {}
    visual_qa = load_json(project / "reports" / "visual_qa.json") if (project / "reports" / "visual_qa.json").is_file() else {}
    postflight = run_postflight(project)
    visual = visual_qa.get("manualReview", {})
    return [
        _check("editable-drawio", (project / "artifacts" / "diagram.drawio").is_file(), "artifacts/diagram.drawio"),
        _check("rendered-artifact", any((project / "artifacts").glob("diagram.drawio.*")), "artifacts/diagram.drawio.*"),
        _check("diagram-qa", diagram_qa.get("ok") is True and diagram_qa.get("counts", {}).get("error") == 0, "reports/diagram_qa.json"),
        _check("visual-qa", visual_qa.get("ok") is True and visual.get("status") == "approved", "reports/visual_qa.json"),
        _check("live-postflight", postflight.get("ok") is True, f"errors={postflight.get('counts', {}).get('error', 0)}"),
    ]


def _validate_observed_execution(execution: dict[str, Any], request: dict[str, Any], request_path: Path) -> list[str]:
    issues: list[str] = []
    required = {"schemaVersion", "mode", "hostId", "hostVersion", "surface", "caseId", "startedAt", "completedAt", "requestSha256", "skillSha256", "adapterSha256", "caseSha256", "invocation", "evidence"}
    missing = required - set(execution)
    if missing:
        return [f"Execution record is missing: {', '.join(sorted(missing))}."]
    if execution.get("schemaVersion") != "1.0" or execution.get("mode") != "observed":
        issues.append("Observed execution must use schemaVersion 1.0 and mode observed.")
    if execution.get("hostId") != request.get("hostId") or execution.get("caseId") != request.get("caseId"):
        issues.append("Execution hostId/caseId does not match the request.")
    for key in ("hostVersion", "surface", "invocation"):
        value = execution.get(key)
        if not isinstance(value, str) or not value.strip() or value.startswith("REPLACE_WITH_"):
            issues.append(f"Execution {key} must identify the real host run.")
    timestamps = []
    for key in ("startedAt", "completedAt"):
        try:
            value = str(execution.get(key, ""))
            if not value.endswith("Z"):
                raise ValueError
            timestamps.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            issues.append(f"Execution {key} must be an ISO-8601 UTC timestamp.")
    if len(timestamps) == 2 and timestamps[1] < timestamps[0]:
        issues.append("Execution completedAt cannot precede startedAt.")
    if execution.get("requestSha256") != sha256_file(request_path):
        issues.append("Execution requestSha256 does not match request.json.")
    for key in ("skillSha256", "adapterSha256", "caseSha256"):
        if execution.get(key) != request.get("digests", {}).get(key):
            issues.append(f"Execution {key} does not match request.json.")
    evidence = execution.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        issues.append("Observed execution requires at least one evidence file.")
    else:
        for index, item in enumerate(evidence):
            path = (request_path.parent / str(item.get("path", ""))).resolve()
            digest = item.get("sha256")
            if not path.is_file() or not isinstance(digest, str) or len(digest) != 64 or digest != sha256_file(path):
                issues.append(f"Execution evidence[{index}] is missing or has a mismatched digest.")
    return issues


def evaluate_run(request_path: Path, project: Path, *, mode: str, execution_path: Path | None = None, root: Path | None = None) -> dict[str, Any]:
    if mode not in {"fixture", "observed"}:
        raise ValueError("mode must be fixture or observed.")
    request = load_json(request_path)
    distribution = root or resource_root()
    suite = load_suite(distribution)
    if request.get("suiteId") != suite["suiteId"]:
        raise ValueError("Request suiteId is stale or invalid.")
    case = next((item for item in suite["cases"] if item["id"] == request.get("caseId")), None)
    if case is None:
        raise ValueError(f"Request references unknown case: {request.get('caseId')}")
    expected_case_hash = sha256_json(case)
    if request.get("digests", {}).get("caseSha256") != expected_case_hash:
        raise ValueError("Request case digest is stale or invalid.")
    adapter = next((item for item in load_adapters(distribution) if item["id"] == request.get("hostId")), None)
    if adapter is None:
        raise ValueError(f"Request references unknown host: {request.get('hostId')}")
    current = {
        "skillSha256": sha256_file(distribution / "SKILL.md"),
        "adapterSha256": sha256_file(Path(adapter["_path"])),
        "caseSha256": expected_case_hash,
    }
    if request.get("digests") != current:
        raise ValueError("Request is stale: the skill, host adapter, or corpus case has changed.")
    execution: dict[str, Any] | None = None
    if mode == "observed":
        if execution_path is None or not execution_path.is_file():
            raise ValueError("Observed evaluation requires an execution record.")
        execution = load_json(execution_path)
        issues = _validate_observed_execution(execution, request, request_path)
        if issues:
            raise ValueError(issues[0])
    required_paths = ["source_model.json", "diagram_lock.json", "diagram_model.json"]
    missing = [relative for relative in required_paths if not (project / relative).is_file()]
    if missing:
        raise ValueError(f"Project is missing required contracts: {', '.join(missing)}")
    source = load_json(project / "source_model.json")
    lock = load_json(project / "diagram_lock.json")
    model = load_json(project / "diagram_model.json")
    expected = case["expectations"]
    dimensions = {
        "semantics": _score(_semantic_checks(model, expected)),
        "evidence": _score(_evidence_checks(source, model)),
        "assets": _score(_asset_checks(project, model, expected)),
        "routing": _score(_routing_checks(project, model, lock, expected)),
        "gates": _score(_gate_checks(project)),
    }
    passed = all(dimensions[name]["score"] >= PASS_THRESHOLD for name in DIMENSIONS)
    artifacts = {}
    for relative in [*required_paths, "artifacts/diagram.drawio", "reports/diagram_qa.json", "reports/visual_qa.json"]:
        path = project / relative
        if path.is_file():
            artifacts[relative] = sha256_file(path)
    evaluated_at = utc_now()
    result = {
        "schemaVersion": "1.0",
        "resultId": f"{request['hostId']}:{request['caseId']}:{sha256_json(artifacts)[:12]}",
        "mode": mode,
        "status": "fixture" if mode == "fixture" else ("verified" if passed else "failed"),
        "hostId": request["hostId"],
        "caseId": request["caseId"],
        "digests": {**request["digests"], "requestSha256": sha256_file(request_path), "projectArtifactsSha256": sha256_json(artifacts)},
        "dimensions": dimensions,
        "passed": passed,
        "evaluatedAt": evaluated_at,
        "execution": execution,
    }
    return result


def build_matrix(results: list[dict[str, Any]], *, detect: bool = True, root: Path | None = None) -> dict[str, Any]:
    distribution = root or resource_root()
    capabilities = host_capabilities(distribution)
    suite = load_suite(distribution)
    case_hashes = {case["id"]: sha256_json(case) for case in suite["cases"]}
    skill_hash = sha256_file(distribution / "SKILL.md")
    adapter_hashes = {adapter["id"]: sha256_file(Path(adapter["_path"])) for adapter in load_adapters(distribution)}
    for index, result in enumerate(results):
        issues = validate_result(result)
        if issues:
            raise ValueError(f"Invalid conformance result at index {index}: {issues[0]}")
    rows = []
    for host in capabilities["hosts"]:
        current_results = [
            result
            for result in results
            if result.get("hostId") == host["id"]
            and result.get("mode") == "observed"
            and result.get("caseId") in case_hashes
            and result.get("digests", {}).get("skillSha256") == skill_hash
            and result.get("digests", {}).get("adapterSha256") == adapter_hashes[host["id"]]
            and result.get("digests", {}).get("caseSha256") == case_hashes[result["caseId"]]
        ]
        latest: dict[str, dict[str, Any]] = {}
        for result in sorted(current_results, key=lambda item: str(item.get("evaluatedAt", ""))):
            latest[str(result["caseId"])] = result
        observed = list(latest.values())
        verified = [result for result in observed if result.get("status") == "verified"]
        failed = [result for result in observed if result.get("status") == "failed"]
        if failed:
            state = "failed"
        elif len(verified) == len(suite["cases"]):
            state = "verified"
        elif detect and not host["available"]:
            state = "unavailable"
        else:
            state = "not-run"
        rows.append({**host, "state": state, "verifiedCases": sorted({item["caseId"] for item in verified}), "failedCases": sorted({item["caseId"] for item in failed})})
    return {"schemaVersion": "1.0", "generatedAt": utc_now(), "suiteId": suite["suiteId"], "hosts": rows}


def matrix_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Host capability and conformance matrix",
        "",
        f"Suite: `{matrix['suiteId']}`. A `verified` state requires observed execution evidence; fixtures never change host status.",
        "",
        "| Host | Local state | Execution | Discovery paths | Verified cases | Limitations |",
        "|---|---|---|---|---|---|",
    ]
    for host in matrix["hosts"]:
        paths = "<br>".join(f"`{path}`" for path in host["discoveryPaths"])
        cases = ", ".join(host["verifiedCases"]) or "None"
        limitations = " ".join(host["limitations"]).replace("|", "\\|")
        lines.append(f"| {host['displayName']} | **{host['state']}** | {host['execution']} | {paths} | {cases} | {limitations} |")
    lines.extend(["", "Local availability is diagnostic only. It is not proof that a host completed the NexCanvas workflow.", ""])
    return "\n".join(lines)

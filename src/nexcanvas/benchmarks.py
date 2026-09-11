from __future__ import annotations

import math
import struct
import zlib
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from .common import load_json, portable_path, resource_root, sha256_file, sha256_json, utc_now, write_json
from .contracts import validate_diagram_model
from .geometry import run_checks as run_geometry_checks
from .model_v3 import normalize_diagram_model
from .quality import validate_drawio_metadata
from .rendering import image_dimensions
from .registry import resolve_route


BENCHMARK_CLASSES = {"sparse", "dense", "cloud", "ai", "sequence", "data-flow", "lifecycle"}


def _benchmark_root(root: Path | None = None) -> Path:
    return (root or resource_root()) / "benchmarks"


def validate_suite(value: Any, root: Path | None = None) -> list[str]:
    if not isinstance(value, dict) or value.get("schemaVersion") != "1.0":
        return ["schemaVersion must be '1.0'."]
    issues: list[str] = []
    if not isinstance(value.get("suiteId"), str) or not value["suiteId"].strip():
        issues.append("suiteId must be a non-empty string.")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        return issues + ["cases must be a non-empty array."]
    seen_ids: set[str] = set()
    seen_classes: set[str] = set()
    base = (root or resource_root()).resolve()
    for index, case in enumerate(cases):
        location = f"cases[{index}]"
        if not isinstance(case, dict):
            issues.append(f"{location} must be an object.")
            continue
        case_id = case.get("id")
        benchmark_class = case.get("class")
        if not isinstance(case_id, str) or not case_id:
            issues.append(f"{location}.id must be a non-empty string.")
        elif case_id in seen_ids:
            issues.append(f"Duplicate benchmark case id: {case_id}.")
        else:
            seen_ids.add(case_id)
        if benchmark_class not in BENCHMARK_CLASSES:
            issues.append(f"{location}.class is unsupported: {benchmark_class!r}.")
        else:
            seen_classes.add(str(benchmark_class))
        for field in ("model", "drawio", "artifact", "visualReview"):
            relative = case.get(field)
            if not isinstance(relative, str) or not relative:
                issues.append(f"{location}.{field} must be a non-empty relative path.")
                continue
            candidate = (base / relative).resolve()
            if candidate != base and base not in candidate.parents:
                issues.append(f"{location}.{field} escapes the distribution root.")
            elif not candidate.is_file():
                issues.append(f"{location}.{field} does not exist: {relative}.")
        expected = case.get("expectations")
        if not isinstance(expected, dict):
            issues.append(f"{location}.expectations must be an object.")
        else:
            if expected.get("viewIntent") not in {"architecture", "workflow", "sequence", "data-flow", "lifecycle"}:
                issues.append(f"{location}.expectations.viewIntent is invalid.")
            for field in ("minNodes", "maxNodes", "minEdges"):
                if not isinstance(expected.get(field), int) or expected[field] < 0:
                    issues.append(f"{location}.expectations.{field} must be a non-negative integer.")
            if isinstance(expected.get("minNodes"), int) and isinstance(expected.get("maxNodes"), int):
                if expected["minNodes"] > expected["maxNodes"]:
                    issues.append(f"{location}.expectations minNodes cannot exceed maxNodes.")
    missing = BENCHMARK_CLASSES - seen_classes
    if missing:
        issues.append(f"Suite does not cover benchmark classes: {', '.join(sorted(missing))}.")
    return issues


def load_suite(root: Path | None = None) -> dict[str, Any]:
    distribution = root or resource_root()
    suite = load_json(_benchmark_root(distribution) / "suite.json")
    issues = validate_suite(suite, distribution)
    if issues:
        raise ValueError(f"Invalid benchmark suite: {issues[0]}")
    return suite


def _paeth(a: int, b: int, c: int) -> int:
    value = a + b - c
    pa = abs(value - a)
    pb = abs(value - b)
    pc = abs(value - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def png_statistics(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    stat = resolved.stat()
    return dict(_png_statistics_cached(str(resolved), stat.st_size, stat.st_mtime_ns))


@lru_cache(maxsize=32)
def _png_statistics_cached(path_value: str, _size: int, _mtime_ns: int) -> dict[str, Any]:
    path = Path(path_value)
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Perceptual benchmark requires a PNG artifact: {path}")
    offset = 8
    width = height = bit_depth = color_type = interlace = 0
    compressed = bytearray()
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type)
    if not width or not height or bit_depth != 8 or channels is None or interlace != 0:
        raise ValueError("PNG perceptual metrics support non-interlaced 8-bit grayscale, RGB, grayscale-alpha, or RGBA images.")
    decoded = zlib.decompress(bytes(compressed))
    stride = width * channels
    expected = height * (stride + 1)
    if len(decoded) != expected:
        raise ValueError("PNG scanline payload has an unexpected size.")
    previous = bytearray(stride)
    cursor = 0
    ink = 0
    visible = 0
    histogram: Counter[int] = Counter()
    step = max(1, int(math.sqrt((width * height) / 500_000)))
    for y in range(height):
        filter_type = decoded[cursor]
        cursor += 1
        scanline = bytearray(decoded[cursor : cursor + stride])
        cursor += stride
        for index in range(stride):
            left = scanline[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                scanline[index] = (scanline[index] + left) & 255
            elif filter_type == 2:
                scanline[index] = (scanline[index] + up) & 255
            elif filter_type == 3:
                scanline[index] = (scanline[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                scanline[index] = (scanline[index] + _paeth(left, up, upper_left)) & 255
            elif filter_type != 0:
                raise ValueError(f"Unsupported PNG filter type: {filter_type}")
        if y % step == 0:
            for x in range(0, width, step):
                pixel = scanline[x * channels : (x + 1) * channels]
                if color_type in {0, 4}:
                    red = green = blue = pixel[0]
                    alpha = pixel[1] if color_type == 4 else 255
                else:
                    red, green, blue = pixel[:3]
                    alpha = pixel[3] if color_type == 6 else 255
                if alpha < 16:
                    continue
                visible += 1
                luminance = round(0.2126 * red + 0.7152 * green + 0.0722 * blue)
                histogram[min(15, luminance // 16)] += 1
                if min(red, green, blue) < 245:
                    ink += 1
        previous = scanline
    entropy = 0.0
    for count in histogram.values():
        probability = count / max(1, visible)
        entropy -= probability * math.log2(probability)
    return {
        "width": width,
        "height": height,
        "sampleStep": step,
        "sampledPixels": visible,
        "inkCoverage": round(ink / max(1, visible), 6),
        "luminanceEntropy": round(entropy, 6),
    }


def _case_result(case: dict[str, Any], distribution: Path, automated_only: bool) -> dict[str, Any]:
    model_path = (distribution / case["model"]).resolve()
    drawio_path = (distribution / case["drawio"]).resolve()
    artifact_path = (distribution / case["artifact"]).resolve()
    review_path = (distribution / case["visualReview"]).resolve()
    canonical_model = load_json(model_path)
    model_issues = validate_diagram_model(canonical_model, distribution)
    model = normalize_diagram_model(canonical_model)
    route = resolve_route(model["route"]["family"], model["route"]["profile"], distribution)
    geometry_errors, geometry_warnings = run_geometry_checks(drawio_path, 10.0, str(route["geometryQa"]))
    metadata_issues = validate_drawio_metadata(drawio_path, canonical_model)
    dimensions = image_dimensions(artifact_path)
    perceptual = png_statistics(artifact_path)
    expectation = case["expectations"]
    intent = str(model.get("viewIntent", ""))
    counts_ok = (
        expectation["minNodes"] <= len(model.get("nodes", [])) <= expectation["maxNodes"]
        and len(model.get("edges", [])) >= expectation["minEdges"]
    )
    text_terms = ("label", "badge", "text", "caption", "glyph")
    text_errors = [error for error in geometry_errors if any(term in error.lower() for term in text_terms)]
    structural_errors = [error for error in geometry_errors if error not in text_errors]
    perceptual_checks = [
        {"name": "readable-size", "ok": bool(dimensions and dimensions[0] >= 640 and dimensions[1] >= 360)},
        {"name": "ink-coverage", "ok": 0.01 <= perceptual["inkCoverage"] <= 0.65},
        {"name": "luminance-entropy", "ok": perceptual["luminanceEntropy"] >= 0.08},
    ]
    review = load_json(review_path)
    review_current = (
        review.get("sha256") == sha256_file(artifact_path)
        and review.get("manualReview", {}).get("status") == "approved"
        and review.get("ok") is True
    )
    automated_passed = (
        not any(issue.severity == "error" for issue in model_issues)
        and not any(issue.severity == "error" for issue in metadata_issues)
        and not structural_errors
        and not text_errors
        and not geometry_warnings
        and counts_ok
        and intent == expectation["viewIntent"]
        and all(check["ok"] for check in perceptual_checks)
    )
    passed = automated_passed and review_current and not automated_only
    return {
        "id": case["id"],
        "class": case["class"],
        "status": "passed" if passed else "automated-only" if automated_only and automated_passed else "pending-review" if automated_passed else "failed",
        "passed": passed,
        "automatedPassed": automated_passed,
        "digests": {
            "modelSha256": sha256_file(model_path),
            "drawioSha256": sha256_file(drawio_path),
            "artifactSha256": sha256_file(artifact_path),
            "visualReviewSha256": sha256_file(review_path),
            "caseSha256": sha256_json(case),
        },
        "semantics": {
            "viewIntent": intent,
            "expectedViewIntent": expectation["viewIntent"],
            "nodes": len(model.get("nodes", [])),
            "edges": len(model.get("edges", [])),
            "densityWithinBounds": counts_ok,
            "contractIssues": [issue.to_dict() for issue in model_issues],
            "metadataIssues": [issue.to_dict() for issue in metadata_issues],
        },
        "geometry": {"errors": structural_errors, "warnings": geometry_warnings},
        "textBounds": {"errors": text_errors},
        "perceptual": {"metrics": perceptual, "checks": perceptual_checks},
        "humanReview": {
            "required": True,
            "current": review_current,
            "status": review.get("manualReview", {}).get("status", "missing"),
            "reviewer": review.get("manualReview", {}).get("reviewer", ""),
        },
    }


def run_benchmarks(
    *,
    root: Path | None = None,
    output: Path | None = None,
    automated_only: bool = False,
) -> dict[str, Any]:
    distribution = (root or resource_root()).resolve()
    suite = load_suite(distribution)
    cases = [_case_result(case, distribution, automated_only) for case in suite["cases"]]
    result = {
        "schemaVersion": "1.0",
        "suiteId": suite["suiteId"],
        "evaluatedAt": utc_now(),
        "mode": "automated-only" if automated_only else "release",
        "passed": all(case["passed"] for case in cases),
        "automatedPassed": all(case["automatedPassed"] for case in cases),
        "suiteSha256": sha256_file(_benchmark_root(distribution) / "suite.json"),
        "cases": cases,
    }
    if output:
        write_json(output.resolve(), result)
        result["output"] = portable_path(output.resolve(), distribution)
    return result

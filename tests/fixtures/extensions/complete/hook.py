from __future__ import annotations

import json
import re
import sys


envelope = json.load(sys.stdin)
kind = envelope["kind"]
request = envelope["request"]

if kind == "analyzer":
    content = request["content"]
    symbols = [
        {"name": match.group(1), "kind": "function", "line": content[: match.start()].count("\n") + 1, "exported": True}
        for match in re.finditer(r"(?m)^func\s+([A-Z][A-Za-z0-9_]*)\s*\(", content)
    ]
    result = {"symbols": symbols, "imports": [], "diagnostics": []}
elif kind == "layout":
    model = request["model"]
    nodes = {
        node["id"]: {"x": 100 + index * 260, "y": 180, "w": 180, "h": 90}
        for index, node in enumerate(model.get("nodes", []))
    }
    boundaries = {
        boundary["id"]: {"x": 60, "y": 120, "w": 620, "h": 220}
        for boundary in model.get("boundaries", [])
    }
    edges = {}
    for edge in model.get("edges", []):
        source = nodes[edge["source"]]
        target = nodes[edge["target"]]
        edges[edge["id"]] = {
            "points": [
                [source["x"] + source["w"], source["y"] + source["h"] / 2],
                [target["x"], target["y"] + target["h"] / 2]
            ],
            "exitX": 1,
            "exitY": 0.5,
            "entryX": 0,
            "entryY": 0.5
        }
    result = {"nodes": nodes, "boundaries": boundaries, "edges": edges}
elif kind == "qa-rule":
    result = {
        "issues": [
            {
                "severity": "info",
                "code": "fixture-executed",
                "message": "The isolated QA fixture ran.",
                "location": "extension"
            }
        ]
    }
else:
    raise SystemExit(2)

json.dump({"protocolVersion": "1.0", "ok": True, "result": result}, sys.stdout)

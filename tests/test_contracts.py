from __future__ import annotations

import json
import copy
import unittest
from pathlib import Path

from nexcanvas.contracts import validate_diagram_model, validate_source_model


FIXTURES = Path(__file__).parent / "fixtures"


class ContractTests(unittest.TestCase):
    def test_retired_offsets_fail_with_migration_guidance(self) -> None:
        model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        model["edges"][0].setdefault("layout", {})["labelOffsetX"] = 30
        self.assertIn("retired-label-offset", {issue.code for issue in validate_diagram_model(model)})

    def test_rag_fixture_contracts_are_valid(self) -> None:
        model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        source = json.loads((FIXTURES / "rag-source-model.json").read_text(encoding="utf-8"))
        self.assertFalse([issue for issue in validate_diagram_model(model) if issue.severity == "error"])
        self.assertFalse([issue for issue in validate_source_model(source) if issue.severity == "error"])

    def test_dangling_edge_is_rejected(self) -> None:
        model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        model["edges"][0]["target"] = "missing"
        self.assertIn("edge-target", {issue.code for issue in validate_diagram_model(model)})

    def test_edge_label_modes_and_placement_are_validated(self) -> None:
        model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        model["edges"][0]["labelMode"] = "callout"
        model["edges"][0]["labelPlacement"] = {"segment": 0, "t": 0.5, "side": "center", "width": 140, "height": 24}
        self.assertFalse([issue for issue in validate_diagram_model(model) if issue.severity == "error"])

        invalid = copy.deepcopy(model)
        invalid["edges"][0]["labelMode"] = "floating"
        invalid["edges"][0]["labelPlacement"]["t"] = 1.5
        codes = {issue.code for issue in validate_diagram_model(invalid)}
        self.assertIn("edge-label-mode", codes)
        self.assertIn("edge-label-placement", codes)

    def test_custom_waypoints_require_numeric_pairs(self) -> None:
        model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        model["edges"][0]["layout"]["waypoints"] = [[200, 300], ["bad", 400]]
        self.assertIn("edge-waypoints", {issue.code for issue in validate_diagram_model(model)})

    def test_icon_presentation_rejects_collapsed_text_envelope(self) -> None:
        model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        model["nodes"][0]["presentation"] = "service-icon"
        model["nodes"][0]["layout"] = {"width": 149, "height": 78}
        issues = validate_diagram_model(model)
        envelope_issues = [issue for issue in issues if issue.code == "node-content-envelope"]
        self.assertEqual({issue.location for issue in envelope_issues}, {"nodes[0].layout.width", "nodes[0].layout.height"})

    def test_view_intent_must_match_route_semantics(self) -> None:
        model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        model["viewIntent"] = "lifecycle"
        self.assertIn("view-intent-route", {issue.code for issue in validate_diagram_model(model)})

    def test_structured_repository_evidence_requires_known_source_and_valid_range(self) -> None:
        source = json.loads((FIXTURES / "rag-source-model.json").read_text(encoding="utf-8"))
        source["facts"][0]["evidence"] = [{"sourceId": "missing", "path": "src/app.py", "startLine": 8, "endLine": 3}]
        codes = {issue.code for issue in validate_source_model(source)}
        self.assertIn("fact-evidence-source", codes)
        self.assertIn("fact-evidence-range", codes)

    def test_repository_evidence_cannot_use_an_unverifiable_string_pointer(self) -> None:
        source = json.loads((FIXTURES / "rag-source-model.json").read_text(encoding="utf-8"))
        source["sources"] = [{
            "id": "repo-1",
            "type": "repository",
            "location": ".",
            "snapshot": "a" * 40,
            "repository": {
                "remote": "https://github.com/example/project.git",
                "revision": "a" * 40,
                "dirty": False,
                "capturedAt": "2026-09-06T00:00:00Z",
            },
        }]
        source["facts"][0]["evidence"] = ["repo-1:src/app.py#L1-L2"]
        self.assertIn("repository-evidence-structured", {issue.code for issue in validate_source_model(source)})

        source["facts"][0]["evidence"] = [{"sourceId": "repo-1", "path": "src/app.py"}]
        self.assertIn("repository-evidence-range-required", {issue.code for issue in validate_source_model(source)})


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from nexcanvas.builder import build_drawio
from nexcanvas.quality import run_quality


FIXTURES = Path(__file__).parent / "fixtures"


class QualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        self.source = json.loads((FIXTURES / "rag-source-model.json").read_text(encoding="utf-8"))

    def test_rag_semantics_pass(self) -> None:
        issues = run_quality(self.model, self.source)
        self.assertFalse([issue for issue in issues if issue.severity == "error"], issues)

    def test_missing_retrieval_is_rejected(self) -> None:
        self.model["nodes"] = [node for node in self.model["nodes"] if node["id"] != "retrieve"]
        self.model["edges"] = [edge for edge in self.model["edges"] if edge["source"] != "retrieve" and edge["target"] != "retrieve"]
        issues = run_quality(self.model, self.source)
        self.assertIn("rag-retrieval", {issue.code for issue in issues})

    def test_drawio_metadata_matches_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "diagram.drawio"
            build_drawio(FIXTURES / "rag-diagram-model.json", output)
            issues = run_quality(self.model, self.source, drawio_path=output)
            self.assertFalse([issue for issue in issues if issue.severity == "error"], issues)

    def test_suppressed_title_and_legend_cannot_reappear_in_drawio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
            model["showTitle"] = False
            model["legend"] = []
            model_path = root / "model.json"
            model_path.write_text(json.dumps(model), encoding="utf-8")
            output = root / "diagram.drawio"
            build_drawio(model_path, output)

            clean = run_quality(model, self.source, drawio_path=output)
            self.assertNotIn("drawio-title-drift", {issue.code for issue in clean})
            self.assertNotIn("drawio-legend-drift", {issue.code for issue in clean})

            tree = ET.parse(output)
            graph_root = tree.getroot().find(".//mxGraphModel/root")
            self.assertIsNotNone(graph_root)
            ET.SubElement(graph_root, "mxCell", {"id": "nc-title", "nc-kind": "title", "vertex": "1", "parent": "1"})
            ET.SubElement(graph_root, "mxCell", {"id": "nc-legend", "nc-kind": "legend", "vertex": "1", "parent": "1"})
            tree.write(output, encoding="utf-8", xml_declaration=True)

            drift = {issue.code for issue in run_quality(model, self.source, drawio_path=output)}
            self.assertIn("drawio-title-drift", drift)
            self.assertIn("drawio-legend-drift", drift)

    def test_representative_route_semantics_are_enforced(self) -> None:
        cases = [
            ("software", "c4-container", "c4-element"),
            ("security", "zero-trust", "trust-boundary"),
            ("ai-ml", "mlops", "ml-training"),
            ("data", "lakehouse-medallion", "medallion-layer"),
            ("product-ui", "service-blueprint", "blueprint-lanes"),
        ]
        for family, profile, expected in cases:
            model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
            model["route"] = {"family": family, "profile": profile}
            with self.subTest(route=f"{family}/{profile}"):
                self.assertIn(expected, {issue.code for issue in run_quality(model, self.source)})


if __name__ == "__main__":
    unittest.main()

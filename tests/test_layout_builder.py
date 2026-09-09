from __future__ import annotations

import copy
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from nexcanvas.builder import build_drawio, build_tree
from nexcanvas.layout import Rect, _grid_positions, layout_model, node_size
from nexcanvas.registry import all_profiles


FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]


class LayoutBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))

    def test_rag_layout_has_all_objects(self) -> None:
        result = layout_model(self.model, "rag")
        self.assertEqual(set(result.nodes), {node["id"] for node in self.model["nodes"]})
        self.assertEqual(set(result.boundaries), {"offline", "online"})
        self.assertEqual(set(result.edges), {edge["id"] for edge in self.model["edges"]})

    def test_service_icon_actor_preserves_separate_icon_and_text_bands(self) -> None:
        node = {
            "id": "approver",
            "label": "Human approval",
            "description": "Required for high risk or exhausted retries",
            "kind": "actor",
            "presentation": "service-icon",
            "layout": {"width": 120, "height": 78},
        }
        self.assertEqual(node_size(node), (150.0, 112.0))
        placed = _grid_positions([node], Rect(0, 0, 120, 60), columns=1)["approver"]
        self.assertGreaterEqual(placed.w, 150.0)
        self.assertGreaterEqual(placed.h, 112.0)

    def test_every_registered_route_builds_native_xml(self) -> None:
        for family, profile, _ in all_profiles():
            model = copy.deepcopy(self.model)
            model["route"] = {"family": family, "profile": profile}
            if profile == "sequence":
                model["boundaries"] = []
                for node in model["nodes"]:
                    node.pop("boundary", None)
            with self.subTest(route=f"{family}/{profile}"):
                tree, _ = build_tree(model)
                root = tree.getroot()
                self.assertEqual(root.tag, "mxfile")
                self.assertEqual(len([cell for cell in root.iter("mxCell") if cell.get("nc-kind") == "node"]), len(model["nodes"]))

    def test_file_build_contains_uncompressed_editable_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "diagram.drawio"
            result = build_drawio(FIXTURES / "rag-diagram-model.json", output)
            parsed = ET.parse(output).getroot()
            self.assertIsNotNone(parsed.find("./diagram/mxGraphModel/root"))
            self.assertEqual(result["nodes"], 7)
            self.assertNotIn("image=http", output.read_text(encoding="utf-8"))

    def test_microsoft_reference_layout_uses_phases_icons_and_step_badges(self) -> None:
        project = ROOT / "examples" / "v2-rag-reference"
        model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        result = layout_model(model, "reference")
        self.assertEqual(result.adapter, "reference")
        self.assertLess(result.boundaries["sources"].bottom, result.boundaries["platform"].top)
        tree, embedded = build_tree(model, project_root=project, root=ROOT)
        cells = list(tree.getroot().iter("mxCell"))
        self.assertEqual(len([cell for cell in cells if cell.get("nc-kind") == "step-badge"]), 8)
        self.assertIn("azure-ai-search", embedded)
        search = next(cell for cell in cells if cell.get("id") == "node-search")
        self.assertIn("shape=label", search.get("style", ""))
        self.assertIn("image=data:image/svg+xml", search.get("style", ""))

    def test_dense_reference_honors_cross_tracks_and_reserved_rails(self) -> None:
        project = ROOT / "examples" / "v3-dense-industrial-ai"
        model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        result = layout_model(model, "reference")
        self.assertLess(result.boundaries["sources"].left, result.boundaries["consume"].left)
        self.assertLess(result.nodes["ml"].cy, result.nodes["foundry"].cy)
        self.assertAlmostEqual(result.nodes["ml"].cx, result.nodes["foundry"].cx, delta=2.0)
        self.assertEqual((result.edges["e5d"].entry_x, result.edges["e5d"].entry_y), (0.5, 1.0))
        self.assertEqual((result.edges["e6d"].exit_x, result.edges["e6d"].exit_y), (1.0, 0.5))
        self.assertEqual((result.edges["e6d"].entry_x, result.edges["e6d"].entry_y), (0.5, 1.0))
        self.assertEqual((result.edges["e7"].entry_x, result.edges["e7"].entry_y), (1.0, 0.5))
        self.assertEqual(len(result.edges["e7"].points), 4)
        tree, embedded = build_tree(model, project_root=project, root=ROOT)
        cells = list(tree.getroot().iter("mxCell"))
        self.assertEqual(len([cell for cell in cells if cell.get("nc-kind") == "step-badge"]), 17)
        self.assertGreaterEqual(len([cell for cell in cells if cell.get("nc-label-mode") == "callout"]), 5)
        self.assertIn("azure-stream-analytics", embedded)

    def test_label_modes_build_as_explicit_editable_cells(self) -> None:
        model = copy.deepcopy(self.model)
        model["edges"][0]["labelMode"] = "callout"
        model["edges"][0]["labelPlacement"] = {"segment": 0, "t": 0.5, "side": "center"}
        model["edges"][1]["labelMode"] = "none"
        tree, _ = build_tree(model)
        cells = {cell.get("id"): cell for cell in tree.getroot().iter("mxCell")}
        self.assertEqual(cells[f"edge-{model['edges'][0]['id']}"].get("value"), "")
        callout = cells[f"label-{model['edges'][0]['id']}"]
        self.assertEqual(callout.get("nc-label-mode"), "callout")
        self.assertIn("fillColor=#FFFFFF", callout.get("style", ""))
        self.assertNotIn(f"label-{model['edges'][1]['id']}", cells)

    def test_named_rail_lanes_receive_independent_coordinates(self) -> None:
        project = ROOT / "examples" / "v2-rag-reference"
        model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        first = copy.deepcopy(model["edges"][0])
        second = copy.deepcopy(model["edges"][0])
        first["id"] = "lane-a"
        first["layout"] = {"rail": "top", "lane": 0}
        second["id"] = "lane-b"
        second["layout"] = {"rail": "top", "lane": 1}
        model["edges"] = [first, second]
        result = layout_model(model, "reference")
        self.assertNotEqual(result.edges["lane-a"].points[2][1], result.edges["lane-b"].points[2][1])

    def test_custom_route_supports_distinct_perimeter_ports(self) -> None:
        project = ROOT / "examples" / "v2-rag-reference"
        model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        edge = copy.deepcopy(model["edges"][0])
        edge["layout"] = {
            "sourcePort": [1.0, 0.8],
            "targetPort": [0.0, 0.2],
            "waypoints": [[400.0, 300.0], [600.0, 300.0]],
        }
        model["edges"] = [edge]
        result = layout_model(model, "reference")
        route = result.edges[edge["id"]]
        self.assertEqual((route.exit_x, route.exit_y), (1.0, 0.8))
        self.assertEqual((route.entry_x, route.entry_y), (0.0, 0.2))

    def test_automatic_route_supports_distinct_perimeter_ports(self) -> None:
        project = ROOT / "examples" / "v2-rag-reference"
        model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        edge = copy.deepcopy(model["edges"][0])
        edge["layout"] = {
            "sourcePort": [1.0, 0.75],
            "targetPort": [0.0, 0.25],
        }
        model["edges"] = [edge]
        result = layout_model(model, "reference")
        route = result.edges[edge["id"]]
        self.assertEqual((route.exit_x, route.exit_y), (1.0, 0.75))
        self.assertEqual((route.entry_x, route.entry_y), (0.0, 0.25))

    def test_named_rail_supports_distinct_target_ports(self) -> None:
        project = ROOT / "examples" / "v2-rag-reference"
        model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        first = copy.deepcopy(model["edges"][0])
        second = copy.deepcopy(model["edges"][0])
        first["id"] = "rail-port-a"
        first["layout"] = {"rail": "top", "targetPort": [0.0, 0.3]}
        second["id"] = "rail-port-b"
        second["layout"] = {"rail": "top", "targetPort": [0.0, 0.7]}
        model["edges"] = [first, second]
        result = layout_model(model, "reference")
        self.assertEqual(result.edges["rail-port-a"].entry_y, 0.3)
        self.assertEqual(result.edges["rail-port-b"].entry_y, 0.7)
        self.assertNotEqual(result.edges["rail-port-a"].points[-1][1], result.edges["rail-port-b"].points[-1][1])

    def test_reference_strategy_changes_phase_orientation_and_treatment(self) -> None:
        project = ROOT / "examples" / "v2-rag-reference"
        base = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))

        compact = copy.deepcopy(base)
        compact["layoutStrategy"] = "compact-pipeline"
        compact_tree, _ = build_tree(compact, project_root=project, root=ROOT)
        compact_phase = next(cell for cell in compact_tree.getroot().iter("mxCell") if cell.get("id") == "boundary-sources")
        self.assertIn("fillColor=#FFFFFF", compact_phase.get("style", ""))
        self.assertIn("strokeWidth=1", compact_phase.get("style", ""))

        rows = copy.deepcopy(base)
        rows["layoutStrategy"] = "phase-rows"
        rows["direction"] = "TB"
        rows["canvas"] = {"width": 1100, "height": 1700, "background": "#FFFFFF"}
        row_layout = layout_model(rows, "reference")
        self.assertLess(row_layout.boundaries["sources"].top, row_layout.boundaries["consume"].top)
        row_tree, _ = build_tree(rows, project_root=project, root=ROOT)
        row_phase = next(cell for cell in row_tree.getroot().iter("mxCell") if cell.get("id") == "boundary-sources")
        self.assertIn("horizontal=0", row_phase.get("style", ""))

    def test_hub_and_spoke_reference_places_towers_hub_and_satellite(self) -> None:
        project = ROOT / "examples" / "v4-hub-spoke-industrial"
        model = json.loads((project / "diagram_model.json").read_text(encoding="utf-8"))
        result = layout_model(model, "reference")
        self.assertLess(result.boundaries["sources"].right, result.boundaries["hub"].left)
        self.assertLess(result.boundaries["hub"].right, result.boundaries["insights"].left)
        self.assertGreater(result.boundaries["advanced"].top, result.boundaries["hub"].bottom)
        self.assertAlmostEqual(result.nodes["synapse"].cx, result.boundaries["hub"].cx, delta=2.0)
        tree, embedded = build_tree(model, project_root=project, root=ROOT)
        cells = {cell.get("id"): cell for cell in tree.getroot().iter("mxCell")}
        self.assertIn("ellipse", cells["boundary-hub"].get("style", ""))
        self.assertIn("azure-synapse-analytics", embedded)


if __name__ == "__main__":
    unittest.main()

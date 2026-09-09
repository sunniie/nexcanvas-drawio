from __future__ import annotations

import unittest

from nexcanvas.planning import brainstorm_layout


def model(nodes: int, phases: int, *, direction: str = "LR", nested: int = 0) -> dict:
    boundaries = [
        {"id": f"p{index}", "label": f"Phase {index}", "kind": "phase", "presentation": "phase-column", "order": index}
        for index in range(phases)
    ]
    for index in range(nested):
        boundaries.append({"id": f"g{index}", "label": f"Group {index}", "kind": "group", "presentation": "solid-group", "parent": f"p{index % phases}"})
    node_items = [
        {"id": f"n{index}", "label": f"Node {index}", "kind": "service", "boundary": f"p{min(phases - 1, index * phases // max(nodes, 1))}"}
        for index in range(nodes)
    ]
    edges = [
        {"id": f"e{index}", "source": f"n{index}", "target": f"n{index + 1}", "kind": "data"}
        for index in range(max(0, nodes - 1))
    ]
    return {
        "canvas": {"width": 1800, "height": 1000},
        "direction": direction,
        "boundaries": boundaries,
        "nodes": node_items,
        "edges": edges,
    }


class PlanningTests(unittest.TestCase):
    def test_sparse_ordered_story_selects_compact_pipeline(self) -> None:
        report = brainstorm_layout(model(8, 5))
        self.assertEqual(report["automaticRecommendation"], "compact-pipeline")
        self.assertEqual(report["geometryPlan"]["phaseTreatment"], "outline")

    def test_dense_ordered_story_selects_dense_phase_columns(self) -> None:
        report = brainstorm_layout(model(20, 6, nested=3))
        self.assertEqual(report["automaticRecommendation"], "dense-phase-columns")
        self.assertIn("top", report["geometryPlan"]["reservedRails"])

    def test_portrait_direction_selects_phase_rows(self) -> None:
        candidate = model(12, 5, direction="TB")
        candidate["canvas"] = {"width": 1000, "height": 1600}
        report = brainstorm_layout(candidate)
        self.assertEqual(report["automaticRecommendation"], "phase-rows")

    def test_explicit_strategy_is_recorded_without_hiding_comparison(self) -> None:
        candidate = model(8, 5)
        candidate["layoutStrategy"] = "phase-columns"
        report = brainstorm_layout(candidate)
        self.assertEqual(report["automaticRecommendation"], "compact-pipeline")
        self.assertEqual(report["selectedStrategy"], "phase-columns")
        self.assertEqual(len(report["candidates"]), 7)


if __name__ == "__main__":
    unittest.main()

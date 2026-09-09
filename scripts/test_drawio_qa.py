import tempfile
import textwrap
import unittest
from pathlib import Path

from nexcanvas.geometry import run_checks


class DrawioQaProfileTests(unittest.TestCase):
    def run_fixture(self, body: str, qa_profile: str):
        xml = textwrap.dedent(
            f"""\
            <mxGraphModel pageWidth="1000" pageHeight="600">
              <root>
                <mxCell id="0"/>
                <mxCell id="1" parent="0"/>
                {body}
              </root>
            </mxGraphModel>
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fixture.drawio"
            path.write_text(xml, encoding="utf-8")
            return run_checks(path, padding=0, qa_profile=qa_profile)

    def test_baseline_profile_runs_core_checks(self):
        errors, warnings = self.run_fixture(
            """
            <mxCell id="a" value="Source" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="120" height="60" as="geometry"/></mxCell>
            <mxCell id="b" value="Target" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="100" width="120" height="60" as="geometry"/></mxCell>
            <mxCell id="e" edge="1" parent="1" source="a" target="b" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "baseline",
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_tagged_page_background_is_ignored(self):
        errors, warnings = self.run_fixture(
            """
            <mxCell id="background" value="" tags="qa-background" vertex="1" parent="1" style="fillColor=#FFFFFF;strokeColor=none"><mxGeometry x="1" y="1" width="998" height="598" as="geometry"/></mxCell>
            <mxCell id="card" value="Primary card" vertex="1" parent="1" style="rounded=1"><mxGeometry x="100" y="100" width="160" height="70" as="geometry"/></mxCell>
            """,
            "baseline",
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_composition_profile_flags_composition_and_sparse_leaf(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="meta" value="Source snapshot" tags="qa-metadata" vertex="1" parent="1" style="text;"><mxGeometry x="0" y="0" width="1000" height="90" as="geometry"/></mxCell>
            <mxCell id="primary" value="Primary" tags="qa-primary qa-icon-exempt" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="0" y="100" width="600" height="500" as="geometry"/></mxCell>
            <mxCell id="sparse" value="Short card" vertex="1" parent="primary" style="rounded=1"><mxGeometry x="20" y="40" width="250" height="180" as="geometry"/></mxCell>
            <mxCell id="support" value="Support" tags="qa-support qa-icon-exempt" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="690" y="100" width="310" height="500" as="geometry"/></mxCell>
            """,
            "composition",
        )
        joined = "\n".join(warnings)
        self.assertIn("support regions occupy", joined)
        self.assertIn("metadata and legend bands occupy", joined)
        self.assertIn("primary content spans only", joined)
        self.assertIn("sparse leaf card", joined)

    def test_prefixed_badges_must_share_full_signature(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="s1" value="S1" tags="qa-sequence:scan" vertex="1" parent="1" style="ellipse;fillColor=#0B63B6;strokeColor=#0B63B6;fontColor=#FFFFFF;fontSize=12;fontStyle=1"><mxGeometry x="50" y="50" width="34" height="34" as="geometry"/></mxCell>
            <mxCell id="a1" value="A1" tags="qa-sequence:assessment" vertex="1" parent="1" style="ellipse;fillColor=#0B63B6;strokeColor=#FFFFFF;fontColor=#FFFFFF;fontSize=12;fontStyle=1"><mxGeometry x="150" y="50" width="34" height="34" as="geometry"/></mxCell>
            """,
            "interaction",
        )
        self.assertTrue(any("inconsistent size or styling" in warning for warning in warnings))

    def test_response_flow_warns_on_remote_detour(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Source" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="Target" vertex="1" parent="1" style="rounded=1"><mxGeometry x="800" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="response" tags="qa-response-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle">
              <mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="200" y="125"/><mxPoint x="200" y="350"/><mxPoint x="700" y="350"/><mxPoint x="700" y="125"/></Array></mxGeometry>
            </mxCell>
            """,
            "interaction",
        )
        joined = "\n".join(warnings)
        self.assertIn("Response edge response", joined)
        self.assertIn("nearest response lane", joined)

    def test_required_relationship_label_is_enforced(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="400" y="100" width="100" height="70" as="geometry"/></mxCell>
            <mxCell id="flow" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("tagged qa-labeled-flow but has no" in error for error in errors))

    def test_relationship_label_needs_a_clear_segment(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="175" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow" value="Export structured analysis history" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("no clear segment long enough" in warning for warning in warnings))

    def test_opaque_relationship_label_background_is_flagged(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="400" y="100" width="100" height="70" as="geometry"/></mxCell>
            <mxCell id="flow" value="Save result" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=#FFFFFF"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "interaction",
        )
        self.assertTrue(any("inline opaque background" in warning for warning in warnings))

    def test_explicit_callout_may_mask_only_its_own_edge(self):
        errors, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Source" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="Target" vertex="1" parent="1" style="rounded=1"><mxGeometry x="500" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow" value="" tags="qa-labeled-flow" nc-label-mode="callout" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="flow-label" value="Score streaming events" tags="qa-flow-label:flow qa-label-callout" nc-kind="flow-label" nc-edge-id="flow" nc-label-mode="callout" vertex="1" parent="1" style="text;html=1;strokeColor=none;fillColor=#FFFFFF"><mxGeometry x="220" y="112" width="170" height="26" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("Line-label collision" in error for error in errors))
        self.assertFalse(any("does not intersect its own edge" in warning for warning in warnings))

    def test_unrelated_edge_cannot_hide_behind_a_callout(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="source" value="Source" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="Target" vertex="1" parent="1" style="rounded=1"><mxGeometry x="500" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="top" value="Top" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="20" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="bottom" value="Bottom" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="200" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow" value="" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="flow-label" value="Rail callout" tags="qa-flow-label:flow qa-label-callout" nc-kind="flow-label" nc-edge-id="flow" nc-label-mode="callout" vertex="1" parent="1" style="text;html=1;strokeColor=none;fillColor=#FFFFFF"><mxGeometry x="260" y="112" width="120" height="26" as="geometry"/></mxCell>
            <mxCell id="other" edge="1" parent="1" source="top" target="bottom" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("Line-label collision: edge other" in error for error in errors))

    def test_flow_label_cannot_cross_elliptical_boundary_outline(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="hub" value="Hub" vertex="1" parent="1" style="ellipse;container=1;fillColor=#FFFFFF;strokeColor=#222222"><mxGeometry x="200" y="100" width="300" height="300" as="geometry"/></mxCell>
            <mxCell id="flow-label" value="Historical telemetry" tags="qa-flow-label:flow qa-label-note" nc-kind="flow-label" nc-edge-id="flow" nc-label-mode="note" vertex="1" parent="1" style="text;html=1;strokeColor=none;fillColor=none"><mxGeometry x="170" y="235" width="120" height="30" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("Boundary-label collision" in error for error in errors))

    def test_flow_label_may_use_clear_space_inside_elliptical_boundary(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="hub" value="Hub" vertex="1" parent="1" style="ellipse;container=1;fillColor=#FFFFFF;strokeColor=#222222"><mxGeometry x="200" y="100" width="300" height="300" as="geometry"/></mxCell>
            <mxCell id="flow-label" value="Curated exchange" tags="qa-flow-label:flow qa-label-note" nc-kind="flow-label" nc-edge-id="flow" nc-label-mode="note" vertex="1" parent="1" style="text;html=1;strokeColor=none;fillColor=none"><mxGeometry x="285" y="235" width="130" height="30" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("Boundary-label collision" in error for error in errors))

    def test_flow_label_cannot_cross_rectangular_boundary_outline(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="zone" value="Zone" vertex="1" parent="1" style="swimlane;container=1;fillColor=#FFFFFF;strokeColor=#707070"><mxGeometry x="200" y="100" width="300" height="300" as="geometry"/></mxCell>
            <mxCell id="flow-label" value="Curated telemetry" tags="qa-flow-label:flow qa-label-note" nc-kind="flow-label" nc-edge-id="flow" nc-label-mode="note" vertex="1" parent="1" style="text;html=1;strokeColor=none;fillColor=none"><mxGeometry x="450" y="230" width="100" height="30" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("Boundary-label collision" in error for error in errors))

    def test_independent_connector_crossing_is_rejected(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="left" value="Left" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="right" value="Right" vertex="1" parent="1" style="rounded=1"><mxGeometry x="500" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="top" value="Top" vertex="1" parent="1" style="rounded=1"><mxGeometry x="275" y="20" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="bottom" value="Bottom" vertex="1" parent="1" style="rounded=1"><mxGeometry x="275" y="200" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="horizontal" edge="1" parent="1" source="left" target="right" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="vertical" edge="1" parent="1" source="top" target="bottom" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("Connector collision" in error for error in errors))

    def test_semantic_bus_allows_shared_connector_lane(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="source" value="Source" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="Target" vertex="1" parent="1" style="rounded=1"><mxGeometry x="500" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow-a" nc-bus-id="events" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="flow-b" nc-bus-id="events" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("Connector collision" in error for error in errors))
        self.assertFalse(any("Ambiguous connector port" in error for error in errors))

    def test_same_port_relay_is_rejected(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="upstream" value="Upstream" vertex="1" parent="1" style="rounded=1"><mxGeometry x="520" y="40" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="service" value="Service" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="120" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="consumer" value="Consumer" vertex="1" parent="1" style="rounded=1"><mxGeometry x="520" y="220" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="incoming" edge="1" parent="1" source="upstream" target="service" style="edgeStyle=orthogonalEdgeStyle;exitX=0;exitY=0.5;entryX=1;entryY=0.5"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="outgoing" edge="1" parent="1" source="service" target="consumer" style="edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.5;entryX=0;entryY=0.5"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("same-port relay on service" in error for error in errors))

    def test_distinct_ports_make_fan_in_and_fan_out_unambiguous(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="upstream" value="Upstream" vertex="1" parent="1" style="rounded=1"><mxGeometry x="520" y="40" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="service" value="Service" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="120" width="100" height="100" as="geometry"/></mxCell>
            <mxCell id="consumer" value="Consumer" vertex="1" parent="1" style="rounded=1"><mxGeometry x="520" y="250" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="incoming" edge="1" parent="1" source="upstream" target="service" style="edgeStyle=orthogonalEdgeStyle;exitX=0;exitY=0.5;entryX=1;entryY=0.25"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="outgoing" edge="1" parent="1" source="service" target="consumer" style="edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.75;entryX=0;entryY=0.5"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("Ambiguous connector port" in error for error in errors))

    def test_near_parallel_independent_lanes_are_rejected(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="source" value="Source" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="80" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target-a" value="Target A" vertex="1" parent="1" style="rounded=1"><mxGeometry x="320" y="340" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target-b" value="Target B" vertex="1" parent="1" style="rounded=1"><mxGeometry x="500" y="340" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow-a" nc-lane-id="lane-a" edge="1" parent="1" source="source" target="target-a" style="edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.5;entryX=0;entryY=0.5">
              <mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="210" y="105"/><mxPoint x="210" y="300"/><mxPoint x="290" y="300"/><mxPoint x="290" y="365"/></Array></mxGeometry>
            </mxCell>
            <mxCell id="flow-b" nc-lane-id="lane-b" edge="1" parent="1" source="source" target="target-b" style="edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.5;entryX=0;entryY=0.5">
              <mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="214" y="105"/><mxPoint x="214" y="300"/><mxPoint x="470" y="300"/><mxPoint x="470" y="365"/></Array></mxGeometry>
            </mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("near-parallel lanes only 4.0px apart" in error for error in errors))

    def test_foreign_connector_cannot_cross_step_badge(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="source-a" value="Source A" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target-a" value="Target A" vertex="1" parent="1" style="rounded=1"><mxGeometry x="500" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="source-b" value="Source B" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="20" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target-b" value="Target B" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="220" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow-a" edge="1" parent="1" source="source-a" target="target-a" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="flow-b" edge="1" parent="1" source="source-b" target="target-b" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            <mxCell id="badge-a" value="1" nc-kind="step-badge" nc-edge-id="flow-a" tags="qa-step-badge" vertex="1" parent="1" style="ellipse;fillColor=#107C10;fontColor=#FFFFFF"><mxGeometry x="336" y="111" width="28" height="28" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("Foreign connector through badge: edge flow-b" in error for error in errors))

    def test_important_relationship_label_requires_perpendicular_clearance(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="500" y="100" width="100" height="70" as="geometry"/></mxCell>
            <mxCell id="flow" value="Save result" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry x="0" y="-6" relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertTrue(any("perpendicular offset" in warning for warning in warnings))

    def test_important_relationship_label_accepts_clear_offset(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="500" y="100" width="100" height="70" as="geometry"/></mxCell>
            <mxCell id="flow" value="Save result" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry x="0" y="-16" relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("perpendicular offset" in warning for warning in warnings))

    def test_labeled_flow_accepts_associated_standalone_text_vertex(self):
        errors, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Frontend" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="API" vertex="1" parent="1" style="rounded=1"><mxGeometry x="500" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow-label" value="Upload CV" tags="qa-flow-label:flow" vertex="1" parent="1" style="text;html=1;strokeColor=none;fillColor=none"><mxGeometry x="220" y="70" width="100" height="16" as="geometry"/></mxCell>
            <mxCell id="flow" value="" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("Labeled flow" in error for error in errors))
        self.assertFalse(any("perpendicular offset" in warning for warning in warnings))

    def test_text_led_stage_is_valid(self):
        errors, warnings = self.run_fixture(
            """
            <mxCell id="primary" value="Primary" tags="qa-primary" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="20" y="20" width="960" height="560" as="geometry"/></mxCell>
            <mxCell id="stage" value="Extract" tags="qa-stage" vertex="1" parent="primary" style="swimlane;container=1"><mxGeometry x="40" y="60" width="260" height="220" as="geometry"/></mxCell>
            <mxCell id="copy" value="Text only" vertex="1" parent="stage" style="rounded=1"><mxGeometry x="20" y="60" width="160" height="60" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("semantic anchor visual" in warning for warning in warnings))
        self.assertEqual(errors, [])

    def test_interaction_title_rail_width_is_limited(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="primary" value="Primary" tags="qa-primary" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="0" y="0" width="1000" height="600" as="geometry"/></mxCell>
            <mxCell id="rail" value="PRIVATE VPC" tags="qa-title-rail" vertex="1" parent="primary" style="rounded=1"><mxGeometry x="0" y="0" width="140" height="300" as="geometry"/></mxCell>
            """,
            "interaction",
        )
        self.assertTrue(any("Title rail rail occupies" in warning for warning in warnings))

    def test_layered_shapes_inside_illustrative_group_are_allowed(self):
        errors, _ = self.run_fixture(
            """
            <mxCell id="primary" value="Primary" tags="qa-primary" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="20" y="20" width="960" height="560" as="geometry"/></mxCell>
            <mxCell id="stage" value="Intake" tags="qa-stage" vertex="1" parent="primary" style="swimlane;container=1"><mxGeometry x="40" y="60" width="300" height="240" as="geometry"/></mxCell>
            <mxCell id="art" value="" tags="qa-illustrative" vertex="1" parent="stage" style="container=1;fillColor=none;strokeColor=none"><mxGeometry x="20" y="60" width="100" height="120" as="geometry"/></mxCell>
            <mxCell id="doc" value="" vertex="1" parent="art" style="shape=document"><mxGeometry x="10" y="10" width="60" height="80" as="geometry"/></mxCell>
            <mxCell id="check" value="✓" vertex="1" parent="art" style="ellipse"><mxGeometry x="55" y="65" width="30" height="30" as="geometry"/></mxCell>
            """,
            "composition",
        )
        self.assertFalse(any("doc" in error and "check" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

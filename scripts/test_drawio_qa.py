import tempfile
import textwrap
import unittest
from pathlib import Path

from drawio_qa import run_checks


class DrawioQaProfileTests(unittest.TestCase):
    def run_fixture(self, body: str, diagram_type: str):
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
            return run_checks(path, padding=0, diagram_type=diagram_type)

    def test_general_profile_remains_backward_compatible(self):
        errors, warnings = self.run_fixture(
            """
            <mxCell id="a" value="Source" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="120" height="60" as="geometry"/></mxCell>
            <mxCell id="b" value="Target" vertex="1" parent="1" style="rounded=1"><mxGeometry x="300" y="100" width="120" height="60" as="geometry"/></mxCell>
            <mxCell id="e" edge="1" parent="1" source="a" target="b" style="edgeStyle=orthogonalEdgeStyle"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "general",
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_tagged_page_background_is_ignored(self):
        errors, warnings = self.run_fixture(
            """
            <mxCell id="background" value="" tags="qa-background" vertex="1" parent="1" style="fillColor=#FFFFFF;strokeColor=none"><mxGeometry x="1" y="1" width="998" height="598" as="geometry"/></mxCell>
            <mxCell id="card" value="Primary card" vertex="1" parent="1" style="rounded=1"><mxGeometry x="100" y="100" width="160" height="70" as="geometry"/></mxCell>
            """,
            "general",
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_overview_profile_flags_composition_and_sparse_leaf(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="meta" value="Source snapshot" tags="qa-metadata" vertex="1" parent="1" style="text;"><mxGeometry x="0" y="0" width="1000" height="90" as="geometry"/></mxCell>
            <mxCell id="primary" value="Primary" tags="qa-primary qa-icon-exempt" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="0" y="100" width="600" height="500" as="geometry"/></mxCell>
            <mxCell id="sparse" value="Short card" vertex="1" parent="primary" style="rounded=1"><mxGeometry x="20" y="40" width="250" height="180" as="geometry"/></mxCell>
            <mxCell id="support" value="Support" tags="qa-support qa-icon-exempt" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="690" y="100" width="310" height="500" as="geometry"/></mxCell>
            """,
            "overview",
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
            "detailed",
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
            "detailed",
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
            "overview",
        )
        self.assertTrue(any("tagged qa-labeled-flow but has no" in error for error in errors))

    def test_relationship_label_needs_a_clear_segment(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="175" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="flow" value="Export structured analysis history" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "overview",
        )
        self.assertTrue(any("no clear segment long enough" in warning for warning in warnings))

    def test_opaque_relationship_label_background_is_flagged(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="400" y="100" width="100" height="70" as="geometry"/></mxCell>
            <mxCell id="flow" value="Save result" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=#FFFFFF"><mxGeometry relative="1" as="geometry"/></mxCell>
            """,
            "detailed",
        )
        self.assertTrue(any("uses opaque background" in warning for warning in warnings))

    def test_important_relationship_label_requires_perpendicular_clearance(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="500" y="100" width="100" height="70" as="geometry"/></mxCell>
            <mxCell id="flow" value="Save result" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry x="0" y="-6" relative="1" as="geometry"/></mxCell>
            """,
            "overview",
        )
        self.assertTrue(any("perpendicular offset" in warning for warning in warnings))

    def test_important_relationship_label_accepts_clear_offset(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="source" value="Feature" vertex="1" parent="1" style="rounded=1"><mxGeometry x="50" y="100" width="100" height="50" as="geometry"/></mxCell>
            <mxCell id="target" value="History" vertex="1" parent="1" style="shape=cylinder"><mxGeometry x="500" y="100" width="100" height="70" as="geometry"/></mxCell>
            <mxCell id="flow" value="Save result" tags="qa-labeled-flow" edge="1" parent="1" source="source" target="target" style="edgeStyle=orthogonalEdgeStyle;labelBackgroundColor=none"><mxGeometry x="0" y="-16" relative="1" as="geometry"/></mxCell>
            """,
            "overview",
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
            "overview",
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
            "overview",
        )
        self.assertFalse(any("semantic anchor visual" in warning for warning in warnings))
        self.assertEqual(errors, [])

    def test_detailed_title_rail_width_is_limited(self):
        _, warnings = self.run_fixture(
            """
            <mxCell id="primary" value="Primary" tags="qa-primary" vertex="1" parent="1" style="swimlane;container=1"><mxGeometry x="0" y="0" width="1000" height="600" as="geometry"/></mxCell>
            <mxCell id="rail" value="PRIVATE VPC" tags="qa-title-rail" vertex="1" parent="primary" style="rounded=1"><mxGeometry x="0" y="0" width="140" height="300" as="geometry"/></mxCell>
            """,
            "detailed",
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
            "overview",
        )
        self.assertFalse(any("doc" in error and "check" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

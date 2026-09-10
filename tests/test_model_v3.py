from __future__ import annotations

import copy
import contextlib
import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from nexcanvas.builder import build_drawio
from nexcanvas.cli import main
from nexcanvas.contracts import validate_diagram_model
from nexcanvas.model_v3 import migrate_v2_model, normalize_diagram_model, semantic_fingerprint
from nexcanvas.quality import run_quality


FIXTURES = Path(__file__).parent / "fixtures"


class SemanticModelV3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.v2 = json.loads((FIXTURES / "rag-diagram-model.json").read_text(encoding="utf-8"))
        self.source = json.loads((FIXTURES / "rag-source-model.json").read_text(encoding="utf-8"))

    def test_migration_is_deterministic_lossless_and_valid(self) -> None:
        first = migrate_v2_model(self.v2, self.source)
        second = migrate_v2_model(self.v2, self.source)
        self.assertEqual(first, second)
        effective_v2 = copy.deepcopy(self.v2)
        effective_v2.update(
            {"viewIntent": "architecture", "visualArchetype": "technical-editorial", "showTitle": True}
        )
        self.assertEqual(normalize_diagram_model(first), effective_v2)
        self.assertFalse([issue for issue in validate_diagram_model(first) if issue.severity == "error"])
        self.assertEqual(
            first["semantics"]["entities"][0]["provenance"][0],
            {"factId": "fact-ingest", "confidence": "confirmed"},
        )

    def test_presentation_changes_do_not_change_semantic_fingerprint(self) -> None:
        model = migrate_v2_model(self.v2, self.source)
        before = semantic_fingerprint(model)
        model["presentation"]["canvas"]["width"] += 200
        model["presentation"]["entities"][0]["layout"] = {"x": 900, "y": 450}
        model["semantics"]["entities"].reverse()
        model["semantics"]["relationships"].reverse()
        self.assertEqual(semantic_fingerprint(model), before)

    def test_semantic_layer_rejects_geometry_or_style_fields(self) -> None:
        model = migrate_v2_model(self.v2, self.source)
        model["semantics"]["entities"][0]["layout"] = {"x": 10, "y": 20}
        model["semantics"]["relationships"][0]["lineClass"] = "data"
        codes = {issue.code for issue in validate_diagram_model(model)}
        self.assertIn("v3-presentation-leak", codes)

    def test_every_semantic_id_has_exactly_one_presentation_record(self) -> None:
        model = migrate_v2_model(self.v2, self.source)
        model["presentation"]["entities"].append(copy.deepcopy(model["presentation"]["entities"][0]))
        model["presentation"]["relationships"].pop()
        codes = {issue.code for issue in validate_diagram_model(model)}
        self.assertIn("v3-presentation-duplicate", codes)
        self.assertIn("v3-presentation-missing", codes)

    def test_provenance_confidence_must_match_source_fact(self) -> None:
        model = migrate_v2_model(self.v2, self.source)
        model["semantics"]["entities"][0]["provenance"][0]["confidence"] = "inferred"
        codes = {issue.code for issue in run_quality(model, self.source)}
        self.assertIn("v3-provenance-confidence-drift", codes)

    def test_v3_build_binds_artifact_to_model_and_semantics(self) -> None:
        model = migrate_v2_model(self.v2, self.source)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "diagram_model.json"
            output = root / "diagram.drawio"
            model_path.write_text(json.dumps(model), encoding="utf-8")
            result = build_drawio(model_path, output)
            xml = ET.parse(output).getroot()
            self.assertEqual(result["modelSchemaVersion"], "3.0")
            self.assertEqual(result["semanticFingerprint"], semantic_fingerprint(model))
            self.assertEqual(xml.get("nc-model-schema-version"), "3.0")
            self.assertEqual(xml.get("nc-semantic-hash"), semantic_fingerprint(model))
            drawn = {cell.get("nc-model-id") for cell in xml.iter("mxCell") if cell.get("nc-kind") == "node"}
            self.assertEqual(drawn, {item["id"] for item in model["semantics"]["entities"]})

    def test_cli_migration_is_non_destructive_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "diagram_model.json"
            source_path = root / "source_model.json"
            output_path = root / "diagram_model.v3.json"
            original = json.dumps(self.v2, indent=2) + "\n"
            input_path.write_text(original, encoding="utf-8")
            source_path.write_text(json.dumps(self.source), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main(["migrate", "v2-to-v3", str(input_path), "--output", str(output_path)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["toSchemaVersion"], "3.0")
            self.assertEqual(input_path.read_text(encoding="utf-8"), original)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["schemaVersion"], "3.0")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["migrate", "v2-to-v3", str(input_path), "--output", str(output_path)])
            self.assertEqual(code, 2)
            self.assertIn("already exists", json.loads(stderr.getvalue())["error"])
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(
                    ["migrate", "v2-to-v3", str(input_path), "--output", str(output_path), "--force"]
                )
            self.assertEqual(code, 0)
            self.assertEqual(input_path.read_text(encoding="utf-8"), original)

            same_path_error = io.StringIO()
            with contextlib.redirect_stderr(same_path_error):
                code = main(["migrate", "v2-to-v3", str(input_path), "--output", str(input_path), "--force"])
            self.assertEqual(code, 2)
            self.assertIn("must differ", json.loads(same_path_error.getvalue())["error"])


if __name__ == "__main__":
    unittest.main()

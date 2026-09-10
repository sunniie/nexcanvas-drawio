from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexcanvas.common import sha256_file
from nexcanvas.conformance import (
    build_matrix,
    evaluate_run,
    host_capabilities,
    load_adapters,
    load_suite,
    matrix_markdown,
    prepare_run,
    validate_adapter,
    validate_suite,
)


class ConformanceTests(unittest.TestCase):
    def test_suite_covers_all_semantic_intents(self) -> None:
        suite = load_suite(ROOT)
        self.assertEqual(validate_suite(suite), [])
        self.assertEqual(
            {case["expectations"]["viewIntent"] for case in suite["cases"]},
            {"architecture", "workflow", "sequence", "data-flow", "lifecycle"},
        )

    def test_adapters_share_one_skill_core(self) -> None:
        adapters = load_adapters(ROOT)
        self.assertEqual({adapter["id"] for adapter in adapters}, {"codex", "github-copilot", "claude-code", "generic-agent-skills"})
        for adapter in adapters:
            self.assertEqual(validate_adapter(adapter), [])
            self.assertEqual(adapter["sharedSkill"], "SKILL.md")

    def test_prepare_binds_skill_adapter_and_case_digests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            prepare_run("multi-agent-workflow", "codex", output, ROOT)
            request = json.loads((output / "request.json").read_text(encoding="utf-8"))
            template = json.loads((output / "execution.template.json").read_text(encoding="utf-8"))
            self.assertEqual(request["digests"]["skillSha256"], sha256_file(ROOT / "SKILL.md"))
            self.assertEqual(template["requestSha256"], sha256_file(output / "request.json"))
            self.assertTrue((output / "PROMPT.md").is_file())

    def test_reference_project_passes_fixture_evaluation_without_verifying_host(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            prepare_run("multi-agent-workflow", "codex", output, ROOT)
            manifest = ROOT / "examples" / "v5-multi-agent-workflow" / "assets" / "asset_manifest.json"
            before = sha256_file(manifest)
            result = evaluate_run(
                output / "request.json",
                ROOT / "examples" / "v5-multi-agent-workflow",
                mode="fixture",
                root=ROOT,
            )
            self.assertTrue(result["passed"])
            self.assertEqual(result["status"], "fixture")
            self.assertTrue(all(result["dimensions"][name]["score"] == 1.0 for name in result["dimensions"]))
            self.assertEqual(sha256_file(manifest), before)

    def test_observed_evaluation_requires_execution_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            prepare_run("multi-agent-workflow", "codex", output, ROOT)
            with self.assertRaisesRegex(ValueError, "execution record"):
                evaluate_run(
                    output / "request.json",
                    ROOT / "examples" / "v5-multi-agent-workflow",
                    mode="observed",
                    root=ROOT,
                )

    def test_observed_evaluation_binds_real_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            prepare_run("multi-agent-workflow", "codex", output, ROOT)
            transcript = output / "transcript.jsonl"
            transcript.write_text('{"event":"fixture host execution"}\n', encoding="utf-8")
            execution = json.loads((output / "execution.template.json").read_text(encoding="utf-8"))
            execution.update(
                {
                    "hostVersion": "test-host 1.0",
                    "surface": "unit-test",
                    "startedAt": "2026-09-10T00:00:00Z",
                    "completedAt": "2026-09-10T00:01:00Z",
                    "invocation": "unit-test runner",
                    "evidence": [{"path": transcript.name, "sha256": sha256_file(transcript)}],
                }
            )
            execution_path = output / "execution.json"
            execution_path.write_text(json.dumps(execution), encoding="utf-8")
            result = evaluate_run(
                output / "request.json",
                ROOT / "examples" / "v5-multi-agent-workflow",
                mode="observed",
                execution_path=execution_path,
                root=ROOT,
            )
            self.assertEqual(result["status"], "verified")
            transcript.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mismatched digest"):
                evaluate_run(
                    output / "request.json",
                    ROOT / "examples" / "v5-multi-agent-workflow",
                    mode="observed",
                    execution_path=execution_path,
                    root=ROOT,
                )

    def test_stale_skill_digest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            prepare_run("multi-agent-workflow", "codex", output, ROOT)
            request = json.loads((output / "request.json").read_text(encoding="utf-8"))
            request["digests"]["skillSha256"] = "0" * 64
            (output / "request.json").write_text(json.dumps(request), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale"):
                evaluate_run(
                    output / "request.json",
                    ROOT / "examples" / "v5-multi-agent-workflow",
                    mode="fixture",
                    root=ROOT,
                )

    def test_fixture_never_changes_host_matrix_to_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            prepare_run("multi-agent-workflow", "codex", output, ROOT)
            fixture = evaluate_run(
                output / "request.json",
                ROOT / "examples" / "v5-multi-agent-workflow",
                mode="fixture",
                root=ROOT,
            )
            matrix = build_matrix([fixture], detect=False, root=ROOT)
            codex = next(host for host in matrix["hosts"] if host["id"] == "codex")
            self.assertEqual(codex["state"], "not-run")
            self.assertIn("fixtures never change host status", matrix_markdown(matrix))

    def test_one_observed_case_cannot_verify_an_entire_host(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            prepare_run("multi-agent-workflow", "codex", output, ROOT)
            partial = evaluate_run(
                output / "request.json",
                ROOT / "examples" / "v5-multi-agent-workflow",
                mode="fixture",
                root=ROOT,
            )
            partial["mode"] = "observed"
            partial["status"] = "verified"
            partial["execution"] = {"mode": "observed"}
            matrix = build_matrix([partial], detect=False, root=ROOT)
            codex = next(host for host in matrix["hosts"] if host["id"] == "codex")
            self.assertEqual(codex["state"], "not-run")
            self.assertEqual(codex["verifiedCases"], ["multi-agent-workflow"])

    def test_doctor_uses_explicit_truthful_states(self) -> None:
        report = host_capabilities(ROOT)
        self.assertTrue(report["hosts"])
        self.assertTrue({host["state"] for host in report["hosts"]}.issubset({"not-run", "unavailable"}))


if __name__ == "__main__":
    unittest.main()

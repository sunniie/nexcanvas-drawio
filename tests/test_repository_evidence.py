from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from nexcanvas.repository import inspect_repository, verify_repository_evidence


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


class RepositoryEvidenceTests(unittest.TestCase):
    def test_revision_origin_blob_and_line_range_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            git(root, "init")
            git(root, "config", "user.name", "NexCanvas Test")
            git(root, "config", "user.email", "nexcanvas@example.test")
            git(root, "remote", "add", "origin", "https://github.com/example/repository.git")
            (root / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
            git(root, "add", "app.py")
            git(root, "commit", "-m", "fixture")
            source = inspect_repository(root, "repo-1", root)
            revision = source["repository"]["revision"]
            blob = git(root, "rev-parse", f"{revision}:app.py")
            model = {
                "sources": [source],
                "facts": [
                    {
                        "id": "fact-entry",
                        "claim": "The repository exposes a main entry point.",
                        "confidence": "confirmed",
                        "evidence": [{"sourceId": "repo-1", "path": "app.py", "startLine": 1, "endLine": 2, "blob": blob}],
                    }
                ],
            }
            self.assertFalse([issue for issue in verify_repository_evidence(model, root) if issue.severity == "error"])
            model["facts"][0]["evidence"][0]["endLine"] = 99
            self.assertIn("repository-line-range", {issue.code for issue in verify_repository_evidence(model, root)})

            model["facts"][0]["evidence"][0]["endLine"] = 2
            model["sources"][0]["snapshot"] = "0" * 40
            self.assertIn("repository-snapshot", {issue.code for issue in verify_repository_evidence(model, root)})

    def test_repository_source_requires_explicit_local_root(self) -> None:
        model = {"sources": [{"id": "repo-1", "type": "repository"}], "facts": []}
        self.assertIn("repository-root-required", {issue.code for issue in verify_repository_evidence(model, None)})


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_skill", ROOT / "scripts" / "validate_skill.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SkillPackageTests(unittest.TestCase):
    def test_repository_skill_package_is_self_consistent(self) -> None:
        self.assertEqual(VALIDATOR.validate(), [])


if __name__ == "__main__":
    unittest.main()

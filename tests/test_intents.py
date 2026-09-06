from __future__ import annotations

import unittest

from scripts.nexcanvas.intents import classify_brief


class IntentTests(unittest.TestCase):
    def test_infers_five_semantic_views_from_english_and_vietnamese_briefs(self) -> None:
        cases = {
            "Vẽ kiến trúc tổng quan hệ thống multi-agent": "architecture",
            "Mô tả quy trình CI/CD có approval và rollback": "workflow",
            "Show one API request calling Redis with a cache miss fallback": "sequence",
            "Vẽ luồng dữ liệu từ Kafka qua ETL vào warehouse": "data-flow",
            "Vẽ vòng đời và các trạng thái của order": "lifecycle",
        }
        for brief, expected in cases.items():
            with self.subTest(brief=brief):
                self.assertEqual(classify_brief(brief)["viewIntent"], expected)

    def test_ambiguous_brief_defaults_to_architecture_without_user_menu(self) -> None:
        self.assertEqual(classify_brief("Show the multi-agent platform")["viewIntent"], "architecture")

    def test_repository_request_movement_is_classified_as_data_flow(self) -> None:
        brief = "Read this repository and draw how requests move through the API, queue, workers, and database"
        self.assertEqual(classify_brief(brief)["viewIntent"], "data-flow")


if __name__ == "__main__":
    unittest.main()

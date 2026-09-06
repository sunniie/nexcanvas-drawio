from __future__ import annotations

import unittest

from scripts.nexcanvas.registry import SUPPORTED_LAYOUTS, all_profiles, resolve_route, resolve_theme
from scripts.nexcanvas.archetypes import resolve_archetype, resolve_provider_pack
from scripts.nexcanvas.intents import VIEW_INTENTS, compatible_view_intents, default_view_intent


class RegistryTests(unittest.TestCase):
    def test_all_routes_use_supported_layouts(self) -> None:
        profiles = all_profiles()
        self.assertGreaterEqual(len(profiles), 45)
        for family, profile, entry in profiles:
            with self.subTest(route=f"{family}/{profile}"):
                self.assertIn(entry["layout"], SUPPORTED_LAYOUTS)
                self.assertIn(entry["geometryQa"], {"baseline", "composition", "interaction"})
                resolved = resolve_route(family, profile)
                self.assertEqual(resolved["family"], family)
                self.assertEqual(resolved["profile"], profile)
                self.assertEqual(resolved["layout"], entry["layout"])
                self.assertIn(default_view_intent(family, profile), VIEW_INTENTS)
                self.assertIn(default_view_intent(family, profile), compatible_view_intents(family, profile))

    def test_all_public_themes_resolve(self) -> None:
        for name in (
            "technical-editorial",
            "cloud-reference",
            "blueprint-engineering",
            "dark-operations",
            "minimal-monochrome",
            "executive-layered",
            "data-lab",
            "strict-notation",
            "microsoft-reference",
        ):
            self.assertEqual(resolve_theme(name)["label"], resolve_theme(name)["label"])

    def test_reference_archetypes_and_official_packs_resolve(self) -> None:
        for name in ("microsoft-reference", "aws-reference", "google-cloud-reference", "provider-neutral-reference"):
            self.assertEqual(resolve_archetype(name)["layoutAdapter"], "reference")
        self.assertEqual(resolve_provider_pack("microsoft-azure-official")["version"], "V24")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nexcanvas.assets import load_manifest, search_catalog, svg_data_uri, sync_catalog_asset, sync_provider_asset, sync_user_asset


class AssetTests(unittest.TestCase):
    def test_alias_search_resolves_exact_product(self) -> None:
        self.assertEqual(search_catalog("postgres")[0]["key"], "postgresql")
        self.assertEqual(search_catalog("openai")[0]["version"], "15.0.0")
        self.assertEqual(search_catalog("amazon web services")[0]["slug"], "amazonaws")

    def test_native_asset_resolves_offline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = sync_catalog_asset(Path(directory), "database", offline=True)
            self.assertEqual(result["state"], "Resolved")
            self.assertEqual(result["provider"], "drawio-native")

    def test_user_svg_is_safely_synced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "brand.svg"
            source.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10H0z"/></svg>', encoding="utf-8")
            result = sync_user_asset(root, "brand", source)
            self.assertEqual(result["state"], "Synced")
            self.assertTrue((root / result["localPath"]).is_file())
            self.assertEqual(load_manifest(root)["assets"][0]["sha256"], result["sha256"])
            uri = svg_data_uri(root / result["localPath"])
            self.assertTrue(uri.startswith("data:image/svg+xml,%3Csvg"))
            self.assertNotIn(";base64", uri)

    def test_unsafe_svg_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "unsafe.svg"
            source.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', encoding="utf-8")
            with self.assertRaises(ValueError):
                sync_user_asset(root, "unsafe", source)

    def test_official_provider_asset_is_synced_from_local_pack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = root / "official-pack"
            pack.mkdir()
            icon = pack / "10029-icon-service-Function-Apps.svg"
            icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10H0z"/></svg>', encoding="utf-8")
            project = root / "project"
            result = sync_provider_asset(
                project,
                "microsoft-azure-official",
                "azure-functions",
                source_archive=pack,
                accept_terms=True,
            )
            self.assertEqual(result["state"], "Synced")
            self.assertEqual(result["provider"], "microsoft-azure-official")
            self.assertTrue((project / result["localPath"]).is_file())

    def test_unpinned_official_pack_discovers_exact_filename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = root / "aws-pack"
            pack.mkdir()
            (pack / "Arch_AWS-Lambda_64.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10H0z"/></svg>',
                encoding="utf-8",
            )
            result = sync_provider_asset(
                root / "project",
                "aws-official",
                "AWS Lambda",
                source_archive=pack,
                accept_terms=True,
            )
            self.assertEqual(result["state"], "Synced")
            self.assertEqual(result["provider"], "aws-official")


if __name__ == "__main__":
    unittest.main()

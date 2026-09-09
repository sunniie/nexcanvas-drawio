from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from nexcanvas.runtime import inspect_runtime
from nexcanvas.visual import create_visual_report


def tiny_png(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    rows = b"".join(b"\x00" + b"\xff\xff\xff\xff" * width for _ in range(height))
    return signature + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


class RuntimeVisualTests(unittest.TestCase):
    def test_runtime_contract(self) -> None:
        report = inspect_runtime()
        self.assertEqual(report["schemaVersion"], "2.0")
        self.assertTrue(report["capabilities"]["authorNativeDrawio"])

    def test_visual_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "preview.png"
            image.write_bytes(tiny_png(640, 360))
            pending = create_visual_report(image, 1600, 900)
            approved = create_visual_report(image, 1600, 900, approved=True, reviewer="test")
            self.assertFalse(pending["ok"])
            self.assertTrue(approved["ok"])


if __name__ == "__main__":
    unittest.main()

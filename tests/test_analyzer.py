"""Tests for boot image analyzer."""
from __future__ import annotations
import struct
import tempfile
from pathlib import Path
import unittest

from src.analyzer.boot_analysis import BootAnalyzer, AnalysisReport
from unittest.mock import patch


def _make_boot_img(**overrides: int) -> bytes:
    """Build a minimal valid boot.img header (page_size=4096)."""
    data = bytearray(8192)
    data[0:8] = b"ANDROID!"
    defaults = {
        8: 1024,   # kernel_size
        12: 0x00008000,  # kernel_addr
        16: 2048,  # ramdisk_size
        20: 0x10000000,  # ramdisk_addr
        24: 0,     # second_size
        28: 0,     # second_addr
        32: 0x00000100,  # tags_addr
        36: 4096,  # page_size
        40: 0,     # header_version
        44: 0,     # os_version
    }
    for offset, val in {**defaults, **overrides}.items():
        struct.pack_into("<I", data, offset, val)
    data[64:72] = b"testimg\x00"
    data[512:560] = b"console=tty0 root=/dev/sda1"
    return bytes(data)


class TestBootAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = BootAnalyzer()

    def test_nonexistent_file(self) -> None:
        result = self.analyzer.analyze("/nonexistent/boot.img")
        self.assertFalse(result.is_valid)
        self.assertIn("does not exist", result.issues[0])

    def test_too_small(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name
        try:
            result = self.analyzer.analyze(path)
            self.assertFalse(result.is_valid)
            self.assertIn("Too small", result.issues[0])
        finally:
            Path(path).unlink()

    def test_bad_magic(self) -> None:
        data = bytearray(8192)
        data[0:8] = b"BADMAGIC!"
        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
            f.write(bytes(data))
            path = f.name
        try:
            result = self.analyzer.analyze(path)
            self.assertFalse(result.is_valid)
            self.assertIn("Bad magic", result.issues[0])
        finally:
            Path(path).unlink()

    def test_valid_boot_img(self) -> None:
        data = _make_boot_img()
        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            result = self.analyzer.analyze(path)
            self.assertTrue(result.is_valid)
            self.assertIsNotNone(result.header)
            self.assertEqual(result.header.magic, "ANDROID!")
            self.assertEqual(result.header.page_size, 4096)
            self.assertEqual(result.header.kernel_size, 1024)
            self.assertEqual(result.header.ramdisk_size, 2048)
        finally:
            Path(path).unlink()

    def test_report_to_dict(self) -> None:
        data = _make_boot_img()
        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            result = self.analyzer.analyze(path)
            d = result.to_dict()
            self.assertIn("file", d)
            self.assertIn("header", d)
            self.assertTrue(d["valid"])
        finally:
            Path(path).unlink()

    def test_report_summary(self) -> None:
        data = _make_boot_img()
        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            result = self.analyzer.analyze(path)
            self.assertIn("Boot v0", result.summary)
            self.assertIn("Kernel", result.summary)
        finally:
            Path(path).unlink()

    def test_invalid_report_summary(self) -> None:
        result = AnalysisReport("/x", 0, None, False, ["broken"])
        self.assertIn("Invalid", result.summary)

    def test_oversized_file_rejected(self) -> None:
        import src.analyzer.boot_analysis as mod

        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
            f.write(b"\x00" * 8192)
            path = f.name
        try:
            with patch("src.analyzer.boot_analysis._MAX_BOOT_BYTES", 1024):
                result = self.analyzer.analyze(path)
            self.assertFalse(result.is_valid)
            self.assertIn("too large", result.issues[0].lower())
        finally:
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()

"""Tests for the installer's release resolution logic."""
from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from installer.installer import pick_asset, latest_scrcpy  # noqa: E402


class TestPickAsset(unittest.TestCase):
    def test_picks_matching_prefix_and_suffix(self) -> None:
        assets = [
            {"name": "AXIS-v1.0.0.zip", "size": 10},
            {"name": "scrcpy-win64-v3.6.zip", "size": 20},
            {"name": "release-notes.txt", "size": 1},
        ]
        self.assertEqual(
            pick_asset(assets, "AXIS-v", ".zip")["name"], "AXIS-v1.0.0.zip"
        )
        self.assertEqual(
            pick_asset(assets, "scrcpy-win64-", ".zip")["name"], "scrcpy-win64-v3.6.zip"
        )

    def test_largest_wins_when_same_prefix(self) -> None:
        assets = [
            {"name": "AXIS-v1.0.0.zip", "size": 50},
            {"name": "AXIS-v1.0.1.zip", "size": 60},
        ]
        self.assertEqual(pick_asset(assets, "AXIS-v", ".zip")["name"], "AXIS-v1.0.1.zip")

    def test_returns_none_when_no_match(self) -> None:
        assets = [{"name": "AXIS-v1.0.0.zip", "size": 10}]
        self.assertIsNone(pick_asset(assets, "scrcpy-win64-", ".zip"))

    def test_scrcpy_dir_name_drops_zip_suffix(self) -> None:
        from installer.installer import scrcpy_dir_name
        self.assertEqual(scrcpy_dir_name("scrcpy-win64-v3.6.zip"), "scrcpy-win64-v3.6")
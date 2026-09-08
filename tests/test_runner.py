"""Tests for the script runner."""
from __future__ import annotations
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.core.runner import ScriptRunner, ScriptResult, _script_cmd


class TestScriptCommandBuilder(unittest.TestCase):
    def test_paths_are_positional_parameters_not_interpolated(self) -> None:
        cmd = _script_cmd("bash", PROJECT_ROOT, os.path.join(PROJECT_ROOT, "scripts", "x.sh"))
        self.assertEqual(cmd[1], "-c")
        self.assertIn("$1", cmd[2])
        self.assertIn("$2", cmd[2])
        # nothing spliced into the program text
        self.assertNotIn("Desktop", cmd[2])
        self.assertNotIn(r"C:\Users", cmd[2])
        self.assertNotIn("scripts", cmd[2])
        # values travel as argv, so shell metacharacters cannot escape quotes
        cmd2 = _script_cmd("bash", '"/tmp; rm -rf /"', '"$(id).sh"')
        self.assertEqual(cmd2[4], '"/tmp; rm -rf /"')  # $1 = root
        self.assertEqual(cmd2[5], '"$(id).sh"')        # $2 = script_path


class TestScriptRunner(unittest.TestCase):
    def test_resolves_self_contained_root(self) -> None:
        runner = ScriptRunner(PROJECT_ROOT)
        root = runner.root
        self.assertTrue(root.rstrip("\\/").endswith("AXIS"), f"Expected AXIS root, got {root}")
        self.assertTrue(os.path.isdir(os.path.join(root, "scripts")))
        self.assertTrue(os.path.isdir(os.path.join(root, "tools")))

    def test_nonexistent_script(self) -> None:
        runner = ScriptRunner(PROJECT_ROOT)
        result = runner.run_script("scripts/does_not_exist.sh")
        self.assertFalse(result.success)
        self.assertIn("not found", result.output)

    def test_script_result_dataclass(self) -> None:
        r = ScriptResult(True, "hello", 0)
        self.assertTrue(r.success)
        self.assertEqual(r.output, "hello")
        self.assertEqual(r.returncode, 0)

    def test_get_scrcpy_path(self) -> None:
        runner = ScriptRunner(PROJECT_ROOT)
        path = runner.get_scrcpy_path()
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isfile(path), f"scrcpy not found at {path}")

    def test_run_adb_missing(self) -> None:
        runner = ScriptRunner(PROJECT_ROOT)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = runner.run_adb("version")
            self.assertFalse(result.success)
            self.assertIn("adb not found", result.output)

    def test_git_bash_found(self) -> None:
        from src.core.runner import _git_bash_path
        path = _git_bash_path()
        self.assertTrue(path, "bash path should be non-empty")

    def test_adb_resolves_inside_project(self) -> None:
        from src.gui.logic import _adb_path
        from src.core.config import find_root
        path = _adb_path()
        self.assertEqual(path, os.path.join(str(find_root()), "tools", "platform-tools", "adb.exe"))
        self.assertTrue(os.path.isfile(path), f"bundled adb not found at {path}")

    def test_rejects_shell_injection_script_path(self) -> None:
        runner = ScriptRunner(PROJECT_ROOT)
        for bad in (
            "scripts/evil.sh; rm -rf /",
            "scripts/$(rm -rf /).sh",
            "scripts/`id`.sh",
            "scripts/evil.sh & curl x",
            "/etc/passwd",
            "\\windows\\evil.sh",
        ):
            result = runner.run_script(bad)
            self.assertFalse(result.success)
            self.assertEqual(result.returncode, -4, f"path not rejected: {bad!r}")

    def test_rejects_path_traversal_out_of_mare(self) -> None:
        runner = ScriptRunner(PROJECT_ROOT)
        result = runner.run_script("scripts/../../../../etc/hosts")
        self.assertFalse(result.success)
        self.assertEqual(result.returncode, -4)
        self.assertIn("escapes", result.output)

    def test_rejects_oversized_script_path(self) -> None:
        runner = ScriptRunner(PROJECT_ROOT)
        result = runner.run_script("scripts/" + "a" * 200 + ".sh")
        self.assertFalse(result.success)
        self.assertEqual(result.returncode, -4)


if __name__ == "__main__":
    unittest.main()

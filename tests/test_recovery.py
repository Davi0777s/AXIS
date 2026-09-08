"""Tests for diagnostics engine and recovery tools."""
from __future__ import annotations
import unittest

from src.doctor.diagnostics import DiagnosticsEngine, CheckResult, Severity
from src.recovery.wifi_fix import WiFiFix
from src.recovery.pin_remove import PINRemove
from src.recovery.screen_unlock import ScreenUnlock
from src.recovery.game_mode import GameMode
from src.recovery.base import FixResult


class TestDiagnosticsEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DiagnosticsEngine()

    def test_run_all_returns_results(self) -> None:
        def fake_shell(cmd: str) -> str:
            return "ok"

        results = self.engine.run_all(fake_shell)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertTrue(all(isinstance(r, CheckResult) for r in results))

    def test_check_result_icon(self) -> None:
        self.assertEqual(CheckResult("t", Severity.OK, "m").icon, "\u2705")
        self.assertEqual(CheckResult("t", Severity.WARNING, "m").icon, "\u26a0\ufe0f")
        self.assertEqual(CheckResult("t", Severity.ERROR, "m").icon, "\u274c")

    def test_adb_check_ok(self) -> None:
        results = self.engine.run_all(lambda cmd: "ok")
        adb = [r for r in results if r.name == "ADB Connection"]
        self.assertEqual(len(adb), 1)
        self.assertEqual(adb[0].severity, Severity.OK)

    def test_adb_check_fail(self) -> None:
        results = self.engine.run_all(lambda cmd: "")
        adb = [r for r in results if r.name == "ADB Connection"]
        self.assertEqual(len(adb), 1)
        self.assertEqual(adb[0].severity, Severity.ERROR)

    def test_selinux_enforcing(self) -> None:
        results = self.engine.run_all(lambda cmd: "Enforcing" if "getenforce" in cmd else "ok")
        selinux = [r for r in results if r.name == "SELinux"]
        self.assertEqual(len(selinux), 1)
        self.assertEqual(selinux[0].severity, Severity.OK)

    def test_selinux_permissive(self) -> None:
        results = self.engine.run_all(lambda cmd: "Permissive" if "getenforce" in cmd else "ok")
        selinux = [r for r in results if r.name == "SELinux"]
        self.assertEqual(len(selinux), 1)
        self.assertEqual(selinux[0].severity, Severity.WARNING)

    def test_exception_in_check_produces_error(self) -> None:
        def broken(cmd: str) -> str:
            raise RuntimeError("boom")

        results = self.engine.run_all(broken)
        errors = [r for r in results if r.severity == Severity.ERROR]
        self.assertGreater(len(errors), 0)


class TestWiFiFix(unittest.TestCase):
    def test_already_disabled(self) -> None:
        fix = WiFiFix()
        result = fix.run(lambda cmd: "1")
        self.assertTrue(result.success)
        self.assertIn("already", result.message.lower())

    def test_applies_fix(self) -> None:
        fix = WiFiFix()
        calls: dict[str, int] = {}

        def mock_shell(cmd: str) -> str:
            calls[cmd] = calls.get(cmd, 0) + 1
            if "settings get" in cmd:
                return "1" if calls[cmd] > 1 else "0"
            return "ok"

        result = fix.run(mock_shell)
        self.assertTrue(result.success)
        self.assertIn("disabled", result.message.lower())


class TestPINRemove(unittest.TestCase):
    def test_returns_result(self) -> None:
        tool = PINRemove()
        result = tool.run(lambda cmd: "cleared")
        self.assertIsInstance(result, FixResult)


class TestScreenUnlock(unittest.TestCase):
    def test_returns_result(self) -> None:
        tool = ScreenUnlock()
        result = tool.run(lambda cmd: "ok")
        self.assertIsInstance(result, FixResult)
        self.assertTrue(result.success)

    def test_verify(self) -> None:
        tool = ScreenUnlock()
        output = tool.verify(lambda cmd: "2147483647" if "timeout" in cmd else "3")
        self.assertIn("Timeout", output)


class TestGameMode(unittest.TestCase):
    def test_activate(self) -> None:
        tool = GameMode()
        result = tool.run(lambda cmd: "ok")
        self.assertTrue(result.success)
        self.assertIn("activated", result.message.lower())

    def test_deactivate(self) -> None:
        tool = GameMode()
        result = tool.disable(lambda cmd: "ok")
        self.assertTrue(result.success)
        self.assertIn("deactivated", result.message.lower())


if __name__ == "__main__":
    unittest.main()

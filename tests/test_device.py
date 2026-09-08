"""Tests for device manager and ADB/fastboot clients."""
from __future__ import annotations
import unittest
from unittest.mock import patch, MagicMock

from src.device.adb import AdbClient, AdbResult
from src.device.fastboot import FastbootClient, FastbootResult
from src.device.manager import DeviceManager, DeviceInfo, sanitize_serial


class TestSerializeSerial(unittest.TestCase):
    def test_accepts_valid_serials(self) -> None:
        for serial in (
            "ABCD1234",
            "0123456789ABCDEF",
            "emulator-5554",
            "192.168.1.5:5555",
            "usb-1-1.2",
            "a._b:+-c",
        ):
            self.assertEqual(sanitize_serial(serial), serial)

    def test_rejects_shell_metacharacters(self) -> None:
        for serial in (
            "",
            "a b",
            "$(rm -rf /)",
            "`id`",
            "$HOME",
            "a;b",
            "a&b",
            "a|b",
            'a"b',
            "a'b",
            "a<b",
            "a>b",
            "\n",
        ):
            with self.assertRaises(ValueError, msg=f"serial accepted: {serial!r}"):
                sanitize_serial(serial)

    def test_rejects_oversized_serial(self) -> None:
        with self.assertRaises(ValueError):
            sanitize_serial("A" * 65)

    def test_manager_falls_back_for_hostile_serial(self) -> None:
        mock_devices = [{"serial": "$(rm -rf /)", "state": "unauthorized"}]
        with patch("src.device.adb.AdbClient.get_devices", return_value=mock_devices):
            dm = DeviceManager()
            result = dm.refresh()
            self.assertIsNotNone(result)
            self.assertEqual(result.serial, "device")
            self.assertEqual(result.state, "unauthorized")


class TestAdbClient(unittest.TestCase):
    def test_run_uses_no_window_flag_on_windows(self) -> None:
        import os
        import subprocess

        if os.name != "nt":
            self.skipTest("Windows-only behavior")

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            AdbClient("adb", "SER").run("devices")
            kwargs = mock_run.call_args.kwargs
            self.assertEqual(kwargs["creationflags"], subprocess.CREATE_NO_WINDOW)

    def test_is_available_returns_false_when_adb_missing(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError):
            client = AdbClient()
            self.assertFalse(client.is_available())

    def test_get_devices_parses_output(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "List of devices attached\nABCD1234\tdevice\n"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = AdbClient()
            devices = client.get_devices()
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]["serial"], "ABCD1234")

    def test_get_devices_empty(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "List of devices attached\n"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = AdbClient()
            devices = client.get_devices()
            self.assertEqual(len(devices), 0)

    def test_get_devices_preserves_unauthorized_state(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = (
            "List of devices attached\n"
            "ABCD1234\tunauthorized\ttransport_id:7\n"
        )
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = AdbClient()
            devices = client.get_devices()
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]["state"], "unauthorized")

    def test_get_devices_preserves_offline_state(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "List of devices attached\nABCD1234\toffline\n"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = AdbClient()
            devices = client.get_devices()
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]["state"], "offline")

    def test_get_prop(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "13"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = AdbClient()
            prop = client.get_prop("ro.build.version.sdk")
            self.assertEqual(prop, "13")

    def test_shell(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = AdbClient()
            result = client.shell("echo ok")
            self.assertTrue(result.success)
            self.assertEqual(result.stdout, "ok")


class TestFastbootClient(unittest.TestCase):
    def test_is_available_returns_false_when_missing(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError):
            client = FastbootClient()
            self.assertFalse(client.is_available())

    def test_run_uses_no_window_flag_on_windows(self) -> None:
        import os
        import subprocess

        if os.name != "nt":
            self.skipTest("Windows-only behavior")

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            FastbootClient("fastboot", "SER").run("getvar", "product")
            kwargs = mock_run.call_args.kwargs
            self.assertEqual(kwargs["creationflags"], subprocess.CREATE_NO_WINDOW)


class TestDeviceInfo(unittest.TestCase):
    def test_creation(self) -> None:
        dev = DeviceInfo(serial="ABC", model="Pixel", state="device")
        self.assertEqual(dev.serial, "ABC")
        self.assertEqual(dev.model, "Pixel")
        self.assertEqual(dev.state, "device")
        self.assertEqual(dev.android_version, "")

    def test_frozen(self) -> None:
        dev = DeviceInfo(serial="ABC", model="Pixel", state="device")
        with self.assertRaises(AttributeError):
            dev.serial = "XYZ"  # type: ignore[misc]


class TestDeviceManager(unittest.TestCase):
    def test_refresh_no_device(self) -> None:
        with patch("src.device.adb.AdbClient.get_devices", return_value=[]):
            with patch("src.device.fastboot.FastbootClient.is_available", return_value=False):
                dm = DeviceManager()
                result = dm.refresh()
                self.assertIsNone(result)
                self.assertFalse(dm.is_connected())

    def test_refresh_with_device(self) -> None:
        mock_devices = [{"serial": "TEST123", "state": "device"}]
        mock_prop_results = {
            "ro.product.model": "Redmi Note 11",
            "ro.build.version.release": "13",
            "ro.build.version.sdk": "33",
            "ro.product.device": "spes",
        }

        with patch("src.device.adb.AdbClient.get_devices", return_value=mock_devices):
            with patch("src.device.adb.AdbClient.get_prop", side_effect=lambda p: mock_prop_results.get(p, "")):
                dm = DeviceManager()
                result = dm.refresh()
                self.assertIsNotNone(result)
                self.assertEqual(result.model, "Redmi Note 11")
                self.assertEqual(result.state, "device")
                self.assertEqual(result.android_version, "13")

    def test_listener_notification(self) -> None:
        callback = MagicMock()
        dm = DeviceManager()
        dm.add_listener(callback)

        with patch("src.device.adb.AdbClient.get_devices", return_value=[]):
            with patch("src.device.fastboot.FastbootClient.is_available", return_value=False):
                dm.refresh()
                callback.assert_called_once()

    def test_refresh_preserves_unauthorized_state(self) -> None:
        mock_devices = [{"serial": "TEST123", "state": "unauthorized"}]

        with patch("src.device.adb.AdbClient.get_devices", return_value=mock_devices):
            dm = DeviceManager()
            result = dm.refresh()
            self.assertIsNotNone(result)
            self.assertEqual(result.state, "unauthorized")
            self.assertEqual(result.serial, "TEST123")
            self.assertFalse(dm.is_connected())
            self.assertTrue(dm.is_authorization_blocked())

    def test_refresh_preserves_offline_state(self) -> None:
        mock_devices = [{"serial": "TEST123", "state": "offline"}]

        with patch("src.device.adb.AdbClient.get_devices", return_value=mock_devices):
            dm = DeviceManager()
            result = dm.refresh()
            self.assertIsNotNone(result)
            self.assertEqual(result.state, "offline")
            self.assertFalse(dm.is_connected())
            self.assertTrue(dm.is_authorization_blocked())


class TestFastbootClientAvailable(unittest.TestCase):
    def test_is_available_true_when_device_listed(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "ABCD1234\tfastboot\n"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = FastbootClient()
            self.assertTrue(client.is_available())

    def test_is_available_false_when_no_transport(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            client = FastbootClient()
            self.assertFalse(client.is_available())


if __name__ == "__main__":
    unittest.main()

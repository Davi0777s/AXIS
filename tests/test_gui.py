"""Smoke tests for the GUI — verify all pages construct and navigate.

Uses Qt's offscreen platform so these run headless (no window shown).
"""
from __future__ import annotations
import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication


class TestGuiSmoke(unittest.TestCase):
    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_builds(self) -> None:
        from src.gui.main_window import MainWindow
        window = MainWindow()
        window.show()
        self.assertIsNotNone(window._stack)
        self.assertEqual(window._stack.count(), 6)

    def test_navigation(self) -> None:
        from src.gui.main_window import MainWindow
        window = MainWindow()
        for i in range(6):
            window._switch_page(i)
            self.assertEqual(window._stack.currentIndex(), i)

    def test_all_pages_are_widgets(self) -> None:
        from src.gui.main_window import MainWindow
        from PySide6.QtWidgets import QWidget
        window = MainWindow()
        for page in window._pages:
            self.assertIsInstance(page, QWidget)

    def test_launchers_page_card_count(self) -> None:
        from src.gui.pages.launchers import LaunchersPage, _LauncherCard
        from src.core.runner import ScriptRunner
        page = LaunchersPage(ScriptRunner())
        cards = [c for c in page.findChildren(_LauncherCard)]
        self.assertEqual(len(cards), 4)

    def test_gaming_controls(self) -> None:
        from src.gui.pages.gaming import GamingPage
        from src.core.runner import ScriptRunner
        from src.device.manager import DeviceManager
        page = GamingPage(ScriptRunner(), DeviceManager())
        page._res_slider.setValue(1024)
        self.assertEqual(page._res_slider.value(), 1024)
        page._fps_combo.setCurrentText("90")
        self.assertEqual(page._fps_combo.currentText(), "90")
        page._reset_defaults()
        self.assertEqual(page._res_slider.value(), 800)
        self.assertEqual(page._fps_combo.currentText(), "60")

    def test_gaming_collect_commands(self) -> None:
        from src.gui.pages.gaming import GamingPage
        from src.core.runner import ScriptRunner
        from src.device.manager import DeviceManager
        page = GamingPage(ScriptRunner(), DeviceManager())
        cmds = page._collect_commands()
        self.assertGreater(len(cmds), 0)
        joined = " ".join(cmds)
        self.assertIn("schedutil", joined)
        self.assertIn("min_pwrlevel", joined)
        self.assertIn("swappiness", joined)

    def test_app_run_importable(self) -> None:
        from src.gui.app import run
        self.assertTrue(callable(run))

    def test_sidebar_items(self) -> None:
        from src.gui.widgets.sidebar import Sidebar
        sidebar = Sidebar()
        self.assertEqual(len(sidebar._buttons_by_index), 6)

    def test_topbar_badge_state(self) -> None:
        from src.gui.main_window import MainWindow
        window = MainWindow()
        self.assertIsNotNone(window._top_badge)
        # Badge reflects the (possibly live) device state after initial poll
        self.assertIn("tag-", window._top_badge.property("class"))
        self.assertTrue(window._top_badge.text().strip())

    def test_sidebar_set_device_none(self) -> None:
        from src.gui.widgets.sidebar import Sidebar
        sidebar = Sidebar()
        sidebar.set_device(None)
        self.assertEqual(sidebar._chip_top.text(), "NO DEVICE")
        self.assertIn("tag-offline", sidebar._chip_top.property("class"))

    def test_word_contains_device_isolation(self) -> None:
        from src.gui.widgets.device_card import DeviceCard
        card = DeviceCard()
        card.set_device(None)
        self.assertEqual(card._state_badge.text(), "NO DEVICE")
        for lbl in card._spec_items.values():
            self.assertEqual(lbl.text(), "—")

    def test_device_data_rendered_as_plain_text_not_html(self) -> None:
        from PySide6.QtCore import Qt
        from src.gui.widgets.device_card import DeviceCard
        from src.device.manager import DeviceInfo
        card = DeviceCard()
        self.assertEqual(card._serial.textFormat(), Qt.TextFormat.PlainText)
        self.assertEqual(card._title.textFormat(), Qt.TextFormat.PlainText)
        self.assertEqual(card._model.textFormat(), Qt.TextFormat.PlainText)
        for lbl in card._spec_items.values():
            self.assertEqual(lbl.textFormat(), Qt.TextFormat.PlainText)
        card.set_device(DeviceInfo(serial="ABC<img src=x>", model="<b>nope</b>", state="device"))
        # markup must be carried as literal text, never parsed/interpreted
        self.assertIn("ABC", card._serial.text())
        self.assertEqual(card._title.text(), "<b>nope</b>")

    def test_connection_banner_hidden_when_device_connected(self) -> None:
        from src.gui.widgets.connection_banner import ConnectionBanner
        from src.device.manager import DeviceInfo
        banner = ConnectionBanner()
        banner.refresh(DeviceInfo(serial="ABC", model="Redmi", state="device"))
        self.assertFalse(banner.isVisible())

    def test_connection_banner_shown_when_no_device(self) -> None:
        from src.gui.widgets.connection_banner import ConnectionBanner
        banner = ConnectionBanner()
        banner.refresh(None)
        self.assertTrue(banner.isVisible())

    def test_connection_banner_shows_repair_when_unauthorized(self) -> None:
        from src.gui.widgets.connection_banner import ConnectionBanner
        from src.device.manager import DeviceInfo
        banner = ConnectionBanner()
        banner.refresh(DeviceInfo(serial="ABC", model="", state="unauthorized"))
        self.assertTrue(banner.isVisible())
        self.assertTrue(banner._btn_repair.isVisible())
        self.assertFalse(banner._btn_rescan.isVisible())

    def test_connection_banner_hides_repair_when_no_device(self) -> None:
        from src.gui.widgets.connection_banner import ConnectionBanner
        banner = ConnectionBanner()
        banner.refresh(None)
        self.assertTrue(banner.isVisible())
        self.assertFalse(banner._btn_repair.isVisible())
        self.assertTrue(banner._btn_rescan.isVisible())

    def test_adb_panel_offers_daily_use_when_connected(self) -> None:
        from src.gui.pages.dashboard import _AdbPanel
        from src.device.manager import DeviceInfo
        panel = _AdbPanel(on_rescan=None, on_daily_use=None)
        panel.show()
        panel.refresh(DeviceInfo(serial="ABC", model="Redmi", state="device"))
        self.assertTrue(panel._btn_daily.isVisible())
        self.assertFalse(panel._btn_authorize.isVisible())

    def test_adb_panel_offers_authorize_when_blocked(self) -> None:
        from src.gui.pages.dashboard import _AdbPanel
        from src.device.manager import DeviceInfo
        panel = _AdbPanel(on_rescan=None, on_daily_use=None)
        panel.show()
        panel.refresh(DeviceInfo(serial="ABC", model="", state="unauthorized"))
        self.assertTrue(panel._btn_authorize.isVisible())
        self.assertFalse(panel._btn_daily.isVisible())

    def test_adb_panel_offers_authorize_when_fastboot(self) -> None:
        from src.gui.pages.dashboard import _AdbPanel
        from src.device.manager import DeviceInfo
        panel = _AdbPanel(on_rescan=None, on_daily_use=None)
        panel.show()
        panel.refresh(DeviceInfo(serial="ABC", model="", state="bootloader"))
        self.assertTrue(panel._btn_authorize.isVisible())
        self.assertFalse(panel._btn_daily.isVisible())


if __name__ == "__main__":
    unittest.main()

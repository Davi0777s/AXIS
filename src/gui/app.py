"""QApplication bootstrap for AXIS — with robust error handling."""
from __future__ import annotations
import ctypes
import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from src.gui.theme import DARK_THEME
from src.gui.assets import load_icon


def _set_app_user_model_id() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AXIS.axis.1.0")
    except Exception:
        pass


def run() -> int:
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("AXIS")
        app.setApplicationDisplayName("AXIS")
        app.setOrganizationName("Davi0777s")
        app.setStyle("Fusion")
        app.setStyleSheet(DARK_THEME)
        icon = load_icon("axis.ico")
        if icon is not None:
            app.setWindowIcon(icon)
        _set_app_user_model_id()

        from src.gui.splash import Splash
        splash = Splash()
        splash.setWindowTitle("AXIS")
        splash.show()
        app.processEvents()

        from src.gui.main_window import MainWindow
        window = MainWindow()
        splash.set_message("Ready")
        app.processEvents()
        window.show()
        splash.close()
        app.processEvents()
        return app.exec()

    except Exception:
        tb = traceback.format_exc()
        try:
            _app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "AXIS — Error",
                f"Failed to start:\n\n{tb}",
            )
        except Exception:
            print(f"FATAL: {tb}", file=sys.stderr)
        return 1

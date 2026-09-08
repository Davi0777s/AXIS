"""ConnectionBanner — dynamic strip shown when no device is connected or ADB
is blocked (unauthorized/offline), offering corrective actions.

Hidden whenever a healthy authorized device is present. The primary action,
"Authorize ADB", launches the desktop repair script that fixes the ADB
``unauthorized`` state without touching the phone screen.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

from src.device.manager import DeviceInfo


class ConnectionBanner(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("connection-banner")
        self.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        self._icon = QLabel()
        self._icon.setObjectName("connection-banner-icon")
        self._icon.setFixedWidth(24)
        layout.addWidget(self._icon)

        self._message = QLabel("No device connected")
        self._message.setObjectName("connection-banner-text")
        self._message.setWordWrap(True)
        layout.addWidget(self._message, 1)

        self._btn_repair = QPushButton("\u26a0  Autorización ADB")
        self._btn_repair.setProperty("class", "action-btn")
        self._btn_repair.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_repair.clicked.connect(self._authorize_adb)
        self._btn_repair.hide()
        layout.addWidget(self._btn_repair)

        self._btn_restart = QPushButton("\u21bb  Restart ADB server")
        self._btn_restart.setProperty("class", "secondary-btn")
        self._btn_restart.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_restart.clicked.connect(self._restart_adb)
        layout.addWidget(self._btn_restart)

        self._btn_rescan = QPushButton("\u21ba  Scan for device")
        self._btn_rescan.setProperty("class", "secondary-btn")
        self._btn_rescan.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rescan.clicked.connect(self._rescan)
        layout.addWidget(self._btn_rescan)

        self._on_scan: object | None = None

    def set_on_scan(self, callback: object) -> None:
        self._on_scan = callback

    def refresh(self, device: DeviceInfo | None) -> None:
        """Show/hide based on connection health; returns nothing."""
        if device is not None and device.state == "device":
            self.hide()
            return

        blocked = device is not None and device.state in ("unauthorized", "offline")

        if blocked:
            self.setObjectName("connection-banner")
            self._icon.setText("\u26a0")
            self._message.setText(
                "ADB is blocked on this device. Re-authorize the connection "
                "to unlock access: put the phone in Fastboot (Vol- + Power) and "
                "run the repair below."
            )
            self._btn_repair.show()
            self._btn_restart.show()
            self._btn_rescan.setVisible(False)
        else:
            self.setObjectName("connection-banner")
            self._icon.setText("\u25c9")
            self._message.setText(
                "No device connected. Plug it in via USB (enable USB debugging), "
                "or start the ADB server and rescan."
            )
            self._btn_repair.hide()
            self._btn_restart.show()
            self._btn_rescan.setVisible(True)

        self._restyle()
        self.show()

    def _restyle(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)

    def _authorize_adb(self) -> None:
        from src.gui.logic import authorize_adb_repair
        authorize_adb_repair()

    def _restart_adb(self) -> None:
        from src.gui.logic import restart_adb_server
        restart_adb_server()
        if self._on_scan is not None:
            self._on_scan()

    def _rescan(self) -> None:
        if self._on_scan is not None:
            self._on_scan()

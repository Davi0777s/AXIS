"""Dashboard page — device overview, connection health and quick actions."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QPushButton,
)
from PySide6.QtCore import Qt, QSize

from src.device.manager import DeviceManager, DeviceInfo
from src.gui.widgets.device_card import DeviceCard
from src.gui.logic import authorize_adb_repair, restart_adb_server
from src.gui.assets import load_icon


class _QuickAction(QFrame):
    def __init__(self, title: str, desc: str, icon: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "tool")
        self.setMinimumHeight(96)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setProperty("class", "tool-icon")
        icon_lbl.setFixedWidth(24)
        lay.addWidget(icon_lbl)

        text = QVBoxLayout()
        text.setSpacing(4)
        name = QLabel(title)
        name.setProperty("class", "tool-name")
        text.addWidget(name)
        desc_lbl = QLabel(desc)
        desc_lbl.setProperty("class", "tool-desc")
        desc_lbl.setWordWrap(True)
        text.addWidget(desc_lbl)
        lay.addLayout(text, 1)


class _AdbPanel(QFrame):
    """Prominent connection-health strip with a state-dependent primary action.

    While the device is *connected* (authorized) the flagship action is
    **Daily Use**; the ADB repair button only matters when ADB is blocked
    (``unauthorized`` / ``offline``) or in fastboot.
    """

    def __init__(self, on_rescan: object, on_daily_use: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("adb-panel")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(16)

        self._status = QLabel("NO DEVICE CONNECTED")
        self._status.setObjectName("adb-panel-status")
        self._status.setTextFormat(Qt.TextFormat.PlainText)
        self._status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._status, 1)

        self._btn_authorize = QPushButton("Autorización ADB")
        self._btn_authorize.setProperty("class", "big-btn")
        self._btn_authorize.setCursor(Qt.CursorShape.PointingHandCursor)
        skull = load_icon("skull-icon.svg")
        if skull is not None:
            self._btn_authorize.setIcon(skull)
            self._btn_authorize.setIconSize(QSize(18, 18))
        self._btn_authorize.setToolTip(
            "Repara el estado ADB 'unauthorized' sin tocar la pantalla "
            "(phone en Fastboot Vol- + Power). "
            "Ejecuta scripts/fix_auth.sh de AXIS."
        )
        self._btn_authorize.clicked.connect(authorize_adb_repair)

        self._btn_daily = QPushButton("\u25b6  Daily Use")
        self._btn_daily.setProperty("class", "big-btn")
        self._btn_daily.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_daily.setToolTip(
            "Arranca Daily Use: pantalla vertical, mouse/teclado y audio "
            "desde tu PC (scripts/scrcpy_daily.sh)."
        )
        self._btn_daily.clicked.connect(self._daily)
        self._btn_daily.setVisible(False)

        layout.addWidget(self._btn_authorize)
        layout.addWidget(self._btn_daily)

        self._btn_restart = QPushButton("\u21bb  Restart ADB")
        self._btn_restart.setProperty("class", "secondary-btn")
        self._btn_restart.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_restart.setToolTip("Reinicia el servidor ADB local")
        self._btn_restart.clicked.connect(self._restart)
        layout.addWidget(self._btn_restart)

        self._btn_rescan = QPushButton("\u21ba  Scan")
        self._btn_rescan.setProperty("class", "secondary-btn")
        self._btn_rescan.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rescan.setToolTip("Rebusca dispositivos conectados")
        self._btn_rescan.clicked.connect(self._rescan)
        layout.addWidget(self._btn_rescan)

        self._on_rescan = on_rescan
        self._on_daily_use = on_daily_use
        self.refresh(None)

    def _restart(self) -> None:
        restart_adb_server()
        self._rescan()

    def _rescan(self) -> None:
        if self._on_rescan is not None:
            self._on_rescan()

    def _daily(self) -> None:
        if self._on_daily_use is not None:
            self._on_daily_use()

    def refresh(self, device: DeviceInfo | None) -> None:
        connected = device is not None and device.state == "device"
        self._btn_daily.setVisible(connected)
        self._btn_authorize.setVisible(not connected)

        if connected:
            self.setProperty("class", "")
            self._status.setText(
                f"\u25cf  CONNECTED — {device.serial} — {device.state.upper()}"
            )
            self._status.setProperty("class", "status-ok")
        elif device is not None and device.state in ("unauthorized", "offline"):
            self.setProperty("class", "alert")
            self._status.setText(
                f"\u26a0  ADB BLOCKED ({device.state.upper()}) — {device.serial}"
            )
            self._status.setProperty("class", "status-error")
        else:
            self.setProperty("class", "")
            self._status.setText("\u25c9  NO DEVICE CONNECTED")
            self._status.setProperty("class", "status-warn")
        self._repolish()

    def _repolish(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)


class DashboardPage(QWidget):
    def __init__(
        self,
        device_manager: DeviceManager,
        on_daily_use: object = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._dm = device_manager
        self._dm.add_listener(self._on_device_change)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        self._device_card = DeviceCard()
        layout.addWidget(self._device_card)

        self._adb_panel = _AdbPanel(
            on_rescan=self._refresh_devices,
            on_daily_use=on_daily_use,
        )
        layout.addWidget(self._adb_panel)

        actions_title = QLabel("Quick Actions")
        actions_title.setProperty("class", "section-title")
        layout.addWidget(actions_title)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)
        for title, desc, icon in [
            ("Analyze Boot Image", "Inspect boot.img / vendor_boot.img headers", "\u25c7"),
            ("Run Diagnostics", "Check device health and configuration", "\u271a"),
            ("Recovery Tools", "WiFi fix, PIN, screen unlock, game mode", "\u21ba"),
        ]:
            actions_row.addWidget(_QuickAction(title, desc, icon), 1)
        layout.addLayout(actions_row)

        layout.addStretch()

        self._on_device_change(self._dm.current_device)

    def _refresh_devices(self) -> None:
        self._dm.refresh()
        self._on_device_change(self._dm.current_device)

    def _on_device_change(self, device: object) -> None:
        self._device_card.set_device(device if isinstance(device, DeviceInfo) else None)
        self._adb_panel.refresh(device if isinstance(device, DeviceInfo) else None)
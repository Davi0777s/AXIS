"""Device info card widget — high-density spec panel."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGridLayout,
)
from PySide6.QtCore import Qt

from src.device.manager import DeviceInfo

_STATE_TAG: dict[str, str] = {
    "device": "tag-online",
    "offline": "tag-offline",
    "unauthorized": "tag-offline",
    "fastboot": "tag-boot",
    "bootloader": "tag-boot",
    "recovery": "tag-recovery",
}


class DeviceCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self._state_badge = QLabel("OFFLINE")
        self._state_badge.setProperty("class", "tag tag-offline")
        header.addWidget(self._state_badge)
        header.addStretch()
        self._serial = QLabel("")
        self._serial.setProperty("class", "mono-pad")
        self._serial.setTextFormat(Qt.TextFormat.PlainText)
        header.addWidget(self._serial)
        layout.addLayout(header)

        self._title = QLabel("No Device")
        self._title.setProperty("class", "hdr")
        self._title.setTextFormat(Qt.TextFormat.PlainText)
        self._title.setStyleSheet("font-size: 17px; font-weight: 700;")
        layout.addWidget(self._title)

        self._model = QLabel("Connect an Android device via USB to begin.")
        self._model.setProperty("class", "subtitle")
        self._model.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self._model)

        self._spec_grid = QGridLayout()
        self._spec_grid.setHorizontalSpacing(28)
        self._spec_grid.setVerticalSpacing(4)
        self._spec_items: dict[str, QLabel] = {}
        self._populate_spec_grid()
        layout.addLayout(self._spec_grid)

        layout.addStretch()

    def _add_spec(self, row: int, col: int, label: str, value: str) -> None:
        lbl = QLabel(label.upper())
        lbl.setProperty("class", "spec-key")
        val = QLabel(value)
        val.setProperty("class", "spec-val")
        val.setTextFormat(Qt.TextFormat.PlainText)
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._spec_grid.addWidget(lbl, row * 2, col)
        self._spec_grid.addWidget(val, row * 2 + 1, col)
        self._spec_items[label] = val

    def _populate_spec_grid(self) -> None:
        self._spec_items = {}
        self._add_spec(0, 0, "Codename", "—")
        self._add_spec(0, 1, "Android", "—")
        self._add_spec(0, 2, "SDK", "—")
        self._add_spec(0, 3, "State", "—")

    def set_device(self, device: DeviceInfo | None) -> None:
        self._serial.setText("")
        for k, lbl in self._spec_items.items():
            lbl.setText("—")

        if device is None:
            self._state_badge.setText("NO DEVICE")
            self._state_badge.setProperty("class", "tag tag-offline")
            self._title.setText("No Device")
            self._model.setText("Connect an Android device via USB to begin.")
            self._repolish(self._state_badge)
            return

        tag = _STATE_TAG.get(device.state.lower(), "tag-muted")
        self._state_badge.setText(device.state.upper())
        self._state_badge.setProperty("class", f"tag {tag}")
        self._repolish(self._state_badge)

        self._title.setText(device.model or "Unknown Model")
        self._model.setText(device.state.capitalize())
        self._serial.setText(device.serial or "")

        value_map = {
            "Codename": device.codename or "—",
            "Android": f"Android {device.android_version}" if device.android_version else "—",
            "SDK": f"API {device.sdk_version}" if device.sdk_version else "—",
            "State": device.state or "—",
        }
        for k, lbl in self._spec_items.items():
            lbl.setText(value_map.get(k, "—"))

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
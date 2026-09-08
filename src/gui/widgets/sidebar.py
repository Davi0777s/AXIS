"""Sidebar navigation widget — AXIS brand, sections, device status."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame,
)
from PySide6.QtCore import Signal, Qt

from src.device.manager import DeviceInfo
from src.gui.widgets.image_panel import ImagePanel

_ASSET_BG = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "personalizacion.png")


class Sidebar(QWidget):
    page_changed = Signal(int)

    _SECTIONS: list[tuple[str, list[tuple[int, str, str]]]] = [
        ("WORKBENCH", [
            (0, "\u25c8", "Dashboard"),
            (1, "\u25b6", "Launchers"),
            (2, "\u2605", "Gaming"),
        ]),
        ("ANALYSIS", [
            (3, "\u25c7", "Boot"),
            (4, "\u271a", "Doctor"),
        ]),
        ("SERVICE", [
            (5, "\u21ba", "Recovery"),
        ]),
    ]

    _PAGE_TITLES = {
        0: "Dashboard",
        1: "Launchers",
        2: "Gaming Tuner",
        3: "Boot Analyzer",
        4: "System Doctor",
        5: "Recovery Tools",
    }

    _STATE_TAG: dict[str, str] = {
        "device": "tag-online",
        "offline": "tag-offline",
        "unauthorized": "tag-offline",
        "fastboot": "tag-boot",
        "bootloader": "tag-boot",
        "recovery": "tag-recovery",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(210)

        self._buttons_by_index: dict[int, QPushButton] = {}

        # Left decorative strip of personalizacion.png as background (204/736)
        # scrim=0.42 keeps text readable over the light areas of the frame
        self._bg = ImagePanel(_ASSET_BG, slice_left=0.0, slice_width=204 / 736, scrim=0.42, parent=self)
        self._bg.lower()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(4)

        # Brand
        brand_row = QVBoxLayout()
        brand_row.setSpacing(4)
        brand = QLabel("AXIS")
        brand.setObjectName("sidebar-brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(brand)

        line = QFrame()
        line.setObjectName("sidebar-brand-line")
        line.setFixedWidth(48)
        line.setFrameShape(QFrame.Shape.NoFrame)
        brand_row.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)

        brand_sub = QLabel("ANDROID SERVICE CONSOLE")
        brand_sub.setObjectName("sidebar-brand-sub")
        brand_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(brand_sub)
        layout.addLayout(brand_row)

        layout.addSpacing(16)

        # Device status card
        self._device_card = QFrame()
        self._device_card.setObjectName("sidebar-device")
        chip = QVBoxLayout(self._device_card)
        chip.setContentsMargins(12, 8, 12, 8)
        chip.setSpacing(4)
        self._chip_top = QLabel("NO DEVICE")
        self._chip_top.setObjectName("sidebar-device-top")
        self._chip_top.setProperty("class", "tag tag-offline")
        self._chip_top.setTextFormat(Qt.TextFormat.PlainText)
        chip.addWidget(self._chip_top, alignment=Qt.AlignmentFlag.AlignLeft)
        self._chip_sub = QLabel("connect via USB / ADB")
        self._chip_sub.setObjectName("sidebar-device-sub")
        self._chip_sub.setTextFormat(Qt.TextFormat.PlainText)
        chip.addWidget(self._chip_sub)
        layout.addWidget(self._device_card)

        layout.addSpacing(12)

        # Nav sections
        for section_title, items in self._SECTIONS:
            sec = QLabel(section_title)
            sec.setObjectName("sidebar-section")
            layout.addWidget(sec)
            layout.addSpacing(2)
            for index, icon, label in items:
                btn = QPushButton(f"{icon}  {label}")
                btn.setProperty("class", "nav-btn")
                btn.setCheckable(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda checked, i=index: self._on_click(i))
                self._buttons_by_index[index] = btn
                layout.addWidget(btn)
            layout.addSpacing(8)

        layout.addStretch()

        sep = QFrame()
        sep.setObjectName("sidebar-sep")
        layout.addWidget(sep)

        footer = QLabel("AXIS v1.0\nAndroid eXploration\n& Inspection Suite")
        footer.setObjectName("sidebar-footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        self._set_active(0)

    def _on_click(self, index: int) -> None:
        self._set_active(index)
        self.page_changed.emit(index)

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)
        self._bg.setGeometry(self.rect())

    def _set_active(self, index: int) -> None:
        for i, btn in self._buttons_by_index.items():
            btn.setChecked(i == index)

    def page_title(self, index: int) -> str:
        return self._PAGE_TITLES.get(index, "Dashboard")

    def set_device(self, device: DeviceInfo | None) -> None:
        if device is None:
            self._chip_top.setText("NO DEVICE")
            self._chip_top.setProperty("class", "tag tag-offline")
            self._chip_sub.setText("connect via USB / ADB")
            self._repolish(self._chip_top)
            return

        tag = self._STATE_TAG.get(device.state.lower(), "tag-muted")
        self._chip_top.setText(device.state.upper())
        self._chip_top.setProperty("class", f"tag {tag}")
        details = []
        if device.model:
            details.append(device.model)
        if device.serial:
            details.append(device.serial)
        self._chip_sub.setText(" \u00b7 ".join(details))
        self._repolish(self._chip_top)

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
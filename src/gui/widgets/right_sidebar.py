"""Right sidebar — secondary panel with the right strip of the cover art."""
from __future__ import annotations
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from src.gui.widgets.image_panel import ImagePanel

_ASSET_BG = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "personalizacion.png")


class RightSidebar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar-right")
        self.setFixedWidth(210)

        # Right decorative strip of personalizacion.png (532..736 / 736)
        self._bg = ImagePanel(_ASSET_BG, slice_left=532 / 736, slice_width=204 / 736, scrim=0.42, parent=self)
        self._bg.lower()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(4)

        sec = QLabel("SESSION")
        sec.setObjectName("sidebar-section")
        layout.addWidget(sec)
        layout.addSpacing(2)

        self._status_label = QLabel("Not connected")
        self._status_label.setProperty("class", "status-warn")
        self._status_label.setObjectName("sidebar-device-top")
        self._status_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self._status_label)

        self._reset_state(True)

        layout.addStretch()

        sep = QFrame()
        sep.setObjectName("sidebar-sep")
        layout.addWidget(sep)

        footer = QLabel("SESSION PANEL")
        footer.setObjectName("sidebar-footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    def _reset_state(self, first: bool = True) -> None:
        if first:
            self._info_top = QLabel("Ready")
            self._info_top.setObjectName("sidebar-device-sub")
            self._info_top.setTextFormat(Qt.TextFormat.PlainText)
            layout = self.layout()
            layout.addWidget(self._info_top)
            self._info_bottom = QLabel("Select a tool to begin")
            self._info_bottom.setObjectName("sidebar-device-sub")
            self._info_bottom.setTextFormat(Qt.TextFormat.PlainText)
            layout.addWidget(self._info_bottom)

    def set_session(self, status: str, info: str = "Ready", detail: str = "Select a tool to begin") -> None:
        self._status_label.setText(status)
        self._status_label.setProperty(
            "class",
            "status-ok" if status == "Connected" else "status-warn",
        )
        self._info_top.setText(info)
        self._info_bottom.setText(detail)

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)
        self._bg.setGeometry(self.rect())
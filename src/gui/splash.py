"""Startup splash — branded, text-based (no imagery).

Shows the product title and the only brand: by Davi0777s.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

_GOLD = "#D9B65C"


class Splash(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 44, 40, 28)
        layout.setSpacing(6)

        self._title = QLabel("AXIS")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            f"color: {_GOLD}; font-size: 46px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(self._title)

        self._subtitle = QLabel("Android eXploration & Inspection Suite")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setStyleSheet(
            "color: #c8cdd4; font-size: 14px; background: transparent;"
        )
        layout.addWidget(self._subtitle)

        self._brand = QLabel("by Davi0777s")
        self._brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._brand.setStyleSheet(
            "color: #99a3b1; font-size: 12px; background: transparent;"
        )
        layout.addWidget(self._brand)

        layout.addStretch()

        self._progress = QLabel("Initializing AXIS...")
        self._progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress.setStyleSheet(
            "color: #99a3b1; font-size: 12px; padding: 6px; background: transparent;"
        )
        layout.addWidget(self._progress)

        self._center_on_screen()

    def _center_on_screen(self) -> None:
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

    def set_message(self, text: str) -> None:
        self._progress.setText(text)
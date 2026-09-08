"""ImagePanel — paints a cropped/scaled pixmap as a widget background.

Used by the left/right sidebars to display the decorative strips sliced from
`assets/personalizacion.png`. A dark scrim (semi-transparent carbone) can be
painted over the image so foreground text stays readable even over white areas
of the art work.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPainter, QPixmap, QColor, Qt


class ImagePanel(QWidget):
    def __init__(
        self,
        image_path: str,
        slice_left: float = 0.0,
        slice_width: float = 1.0,
        scrim: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        """Paint `slice_left..slice_left+slice_width` (fraction of width) scaled
        to fill the widget. `scrim` (0..1) darkens the image for text contrast."""
        super().__init__(parent)
        self._slice_left = slice_left
        self._slice_width = slice_width
        self._scrim = max(0.0, min(1.0, scrim))
        self._pixmap: QPixmap | None = None

        src = QImage(image_path)
        if not src.isNull():
            x0 = int(src.width() * slice_left)
            x1 = int(src.width() * (slice_left + slice_width))
            self._pixmap = QPixmap.fromImage(src.copy(x0, 0, max(1, x1 - x0), src.height()))

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if self._pixmap is not None and not self._pixmap.isNull():
            painter.drawPixmap(self.rect(), self._pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        if self._scrim > 0:
            alpha = int(255 * self._scrim)
            painter.fillRect(self.rect(), QColor(8, 8, 12, alpha))
        painter.end()
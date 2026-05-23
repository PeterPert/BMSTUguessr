from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from app.paths import MAP_SIZE

Marker = tuple[int, int, QColor | str, str]


class MapCanvas(QLabel):
    clicked = Signal(int, int)

    def __init__(self, parent=None, clickable: bool = True) -> None:
        super().__init__(parent)
        self.clickable = clickable
        self.base_pixmap: QPixmap | None = None
        self.markers: list[Marker] = []
        self.lines: list[tuple[int, int, int, int, QColor | str]] = []
        self.setFixedSize(*MAP_SIZE)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #f5eef2; border: 1px solid #b87b8e;")

    def load_map(self, path: str | Path) -> None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            placeholder = QPixmap(*MAP_SIZE)
            placeholder.fill(QColor("#f9d9e4"))
            pixmap = placeholder
        if pixmap.width() != MAP_SIZE[0] or pixmap.height() != MAP_SIZE[1]:
            pixmap = pixmap.scaled(*MAP_SIZE, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.base_pixmap = pixmap
        self._redraw()

    def set_markers(self, markers: Iterable[Marker]) -> None:
        self.markers = list(markers)
        self._redraw()

    def set_lines(self, lines: Iterable[tuple[int, int, int, int, QColor | str]]) -> None:
        self.lines = list(lines)
        self._redraw()

    def clear_overlays(self) -> None:
        self.markers.clear()
        self.lines.clear()
        self._redraw()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt method name
        if self.clickable and event.button() == Qt.LeftButton:
            point = event.position().toPoint()
            x = max(0, min(MAP_SIZE[0] - 1, point.x()))
            y = max(0, min(MAP_SIZE[1] - 1, point.y()))
            self.clicked.emit(x, y)
        super().mousePressEvent(event)

    def _redraw(self) -> None:
        if self.base_pixmap is None:
            pixmap = QPixmap(*MAP_SIZE)
            pixmap.fill(QColor("#f9d9e4"))
        else:
            pixmap = self.base_pixmap.copy()

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        for x1, y1, x2, y2, color in self.lines:
            pen = QPen(QColor(color), 4)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(QPoint(x1, y1), QPoint(x2, y2))

        for x, y, color, label in self.markers:
            qcolor = QColor(color)
            painter.setPen(QPen(QColor("white"), 4))
            painter.setBrush(qcolor)
            painter.drawEllipse(QPoint(x, y), 11, 11)
            painter.setPen(QPen(qcolor.darker(140), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPoint(x, y), 16, 16)
            if label:
                painter.setPen(QPen(QColor("#4d2732"), 2))
                painter.drawText(x + 18, y - 12, label)

        painter.end()
        self.setPixmap(pixmap)


def build_scaled_result_pixmap(
    map_path: str | Path,
    markers: Iterable[Marker],
    lines: Iterable[tuple[int, int, int, int, QColor | str]],
    max_width: int = 560,
    max_height: int = 360,
) -> QPixmap:
    canvas = MapCanvas(clickable=False)
    canvas.load_map(map_path)
    canvas.set_lines(lines)
    canvas.set_markers(markers)
    pixmap = canvas.pixmap()
    if pixmap is None:
        fallback = QPixmap(*MAP_SIZE)
        fallback.fill(QColor("#f9d9e4"))
        pixmap = fallback
    return pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

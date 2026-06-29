from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from app.paths import MAP_SIZE
from app.theme import get_colors

Marker = tuple[int, int, QColor | str, str]


def _draw_pin_marker(painter: QPainter, x: int, y: int, color: QColor, label: str = "") -> None:
    """
    Рисует маркер в стиле гео-пина.
    Координата (x, y) находится ровно в кончике маркера.
    """

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Размеры маркера
    pin_width = 34
    pin_height = 46
    head_radius = 16
    inner_radius = 7

    tip_x = float(x)
    tip_y = float(y)

    center_x = tip_x
    center_y = tip_y - pin_height + head_radius + 2

    # Основная форма пина
    path = QPainterPath()
    path.moveTo(tip_x, tip_y)

    path.cubicTo(
        tip_x - pin_width * 0.55,
        tip_y - 16,
        center_x - head_radius,
        center_y + 8,
        center_x - head_radius,
        center_y,
    )

    path.cubicTo(
        center_x - head_radius,
        center_y - head_radius,
        center_x + head_radius,
        center_y - head_radius,
        center_x + head_radius,
        center_y,
    )

    path.cubicTo(
        center_x + head_radius,
        center_y + 8,
        tip_x + pin_width * 0.55,
        tip_y - 16,
        tip_x,
        tip_y,
    )

    path.closeSubpath()

    # Тень
    shadow_path = QPainterPath(path)
    painter.translate(2, 3)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 0, 0, 45))
    painter.drawPath(shadow_path)
    painter.translate(-2, -3)

    # Основной цвет пина
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPath(path)

    # Лёгкая обводка
    painter.setPen(QPen(color.darker(125), 2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(path)

    # Белое отверстие внутри
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("white"))
    painter.drawEllipse(QPointF(center_x, center_y), inner_radius, inner_radius)

    # Маленькая цветная точка внутри
    painter.setBrush(color.darker(110))
    painter.drawEllipse(QPointF(center_x, center_y), 3, 3)

    # Подпись, если передана
    if label:
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#0f2740")))
        painter.drawText(QPointF(tip_x + 18, tip_y - 20), label)

    painter.restore()


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
        self._apply_frame_style()

    def _apply_frame_style(self) -> None:
        c = get_colors()
        self.setStyleSheet(f"background: {c.map_frame_background}; border: 1px solid {c.map_frame_border};")

    def load_map(self, path: str | Path) -> None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            placeholder = QPixmap(*MAP_SIZE)
            placeholder.fill(QColor(get_colors().placeholder))
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
            pixmap.fill(QColor(get_colors().placeholder))
        else:
            pixmap = self.base_pixmap.copy()

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        for x1, y1, x2, y2, color in self.lines:
            pen = QPen(QColor(color), 3)
            pen.setStyle(Qt.DashLine)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPoint(x1, y1), QPoint(x2, y2))

        for x, y, color, label in self.markers:
            _draw_pin_marker(painter, x, y, QColor(color), label)

        painter.end()
        self.setPixmap(pixmap)


def build_scaled_result_pixmap(
    map_path: str | Path,
    markers: Iterable[Marker],
    lines: Iterable[tuple[int, int, int, int, QColor | str]],
    max_width: int = 1000,
    max_height: int = 640,
) -> QPixmap:
    canvas = MapCanvas(clickable=False)
    canvas.load_map(map_path)
    canvas.set_lines(lines)
    canvas.set_markers(markers)
    pixmap = canvas.pixmap()
    if pixmap is None:
        fallback = QPixmap(*MAP_SIZE)
        fallback.fill(QColor(get_colors().placeholder))
        pixmap = fallback
    return pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

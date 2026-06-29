from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.paths import PROJECT_ROOT

LOGO_PATH = PROJECT_ROOT / "data" / "icons" / "navigator_icon.svg"


def make_pin_pixmap(
    color: str = "#176ed2", width: int = 30, height: int = 40
) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    pin_color = QColor(color)
    tip_x = width / 2
    tip_y = height - 3
    head_radius = width * 0.34
    center_x = tip_x
    center_y = height * 0.34

    path = QPainterPath()
    path.moveTo(QPointF(tip_x, tip_y))
    path.cubicTo(
        QPointF(width * 0.05, height * 0.58),
        QPointF(width * 0.05, height * 0.10),
        QPointF(center_x, height * 0.06),
    )
    path.cubicTo(
        QPointF(width * 0.95, height * 0.10),
        QPointF(width * 0.95, height * 0.58),
        QPointF(tip_x, tip_y),
    )
    path.closeSubpath()

    painter.setPen(Qt.NoPen)
    painter.setBrush(pin_color)
    painter.drawPath(path)
    painter.setBrush(QColor("white"))
    painter.drawEllipse(
        QPointF(center_x, center_y),
        head_radius * 0.38,
        head_radius * 0.38,
    )

    painter.end()
    return pixmap


def make_logo_pixmap(size: int = 72) -> QPixmap:
    if LOGO_PATH.exists():
        pixmap = QIcon(str(LOGO_PATH)).pixmap(size, size)
        if not pixmap.isNull():
            return pixmap

    return make_pin_pixmap("#176ed2", size, int(size * 1.25))


def build_logo_header(
    title_size: int = 34,
    icon_size: int = 72,
    spacing: int = 10,
    vertical: bool = True,
) -> QWidget:
    widget = QWidget()
    widget.setStyleSheet("""
        QWidget {
            background: transparent;
            border: none;
        }
        """)

    if vertical:
        layout = QVBoxLayout(widget)
    else:
        layout = QHBoxLayout(widget)

    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(spacing)
    layout.setAlignment(Qt.AlignCenter)

    icon_label = QLabel()
    icon_label.setPixmap(make_logo_pixmap(icon_size))
    icon_label.setFixedSize(icon_size + 8, icon_size + 8)
    icon_label.setAlignment(Qt.AlignCenter)
    icon_label.setStyleSheet("""
        QLabel {
            background: transparent;
            border: none;
        }
        """)

    title_label = QLabel("BMSTUguessr")
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet(f"""
        QLabel {{
            color: #0b3b66;
            font-size: {title_size}px;
            font-weight: 900;
            background: transparent;
            border: none;
        }}
        """)

    layout.addWidget(icon_label, 0, Qt.AlignCenter)
    layout.addWidget(title_label, 0, Qt.AlignCenter)

    return widget

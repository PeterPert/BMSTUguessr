from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QLabel, QPushButton, QWidget


class ColorPickerRow(QWidget):
    color_changed = Signal(str, str)

    def __init__(self, field_key: str, label: str, initial_color: str, parent=None) -> None:
        super().__init__(parent)
        self.field_key = field_key
        self._color = initial_color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.name_label = QLabel(label)
        self.name_label.setMinimumWidth(190)

        self.swatch = QPushButton()
        self.swatch.setFixedSize(44, 44)
        self.swatch.setCursor(Qt.PointingHandCursor)
        self.swatch.clicked.connect(self._pick_color)

        self.hex_label = QLabel(initial_color.upper())
        self.hex_label.setObjectName("EditorStatusPending")
        self.hex_label.setMinimumWidth(72)

        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.swatch)
        layout.addWidget(self.hex_label)
        self._refresh_swatch()

    def set_color(self, color: str) -> None:
        self._color = color
        self.hex_label.setText(color.upper())
        self._refresh_swatch()

    def color(self) -> str:
        return self._color

    def _refresh_swatch(self) -> None:
        self.swatch.setStyleSheet(
            f"background: {self._color}; border: 3px solid white; border-radius: 10px;"
        )

    def _pick_color(self) -> None:
        picked = QColorDialog.getColor(QColor(self._color), self, "Выберите цвет")
        if not picked.isValid():
            return
        self.set_color(picked.name(QColor.HexRgb))
        self.color_changed.emit(self.field_key, self._color)

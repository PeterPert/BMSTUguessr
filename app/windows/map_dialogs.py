from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout

from app.widgets.map_canvas import MapCanvas, Marker


class MapPickerDialog(QDialog):
    point_selected = Signal(int, int)

    def __init__(self, map_path: str | Path, parent=None, existing_marker: tuple[int, int] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Поставьте точку на карте")
        self.setFixedSize(1100, 700)
        self.selected_point: tuple[int, int] | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = MapCanvas(clickable=True)
        self.canvas.load_map(map_path)
        if existing_marker is not None:
            self.canvas.set_markers([(existing_marker[0], existing_marker[1], QColor("#2aa876"), "точка")])
        layout.addWidget(self.canvas)
        self.canvas.clicked.connect(self._select_point)

    def _select_point(self, x: int, y: int) -> None:
        self.selected_point = (x, y)
        self.point_selected.emit(x, y)
        self.accept()


class ResultMapDialog(QDialog):
    def __init__(
        self,
        map_path: str | Path,
        markers: list[Marker],
        lines: list[tuple[int, int, int, int, QColor | str]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Карта результата")
        self.setFixedSize(1100, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = MapCanvas(clickable=False)
        self.canvas.load_map(map_path)
        self.canvas.set_lines(lines)
        self.canvas.set_markers(markers)
        layout.addWidget(self.canvas)

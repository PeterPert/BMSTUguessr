from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from app import database
from app.widgets.logo_header import build_logo_header


class ResultsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(620, 420)
        layout = QVBoxLayout(self)
        title = build_logo_header(title_size=30, icon_size=64, spacing=8)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Игрок", "Очки", "Максимум", "Когда"])
        self.table.horizontalHeader().setStretchLastSection(True)
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(title)
        layout.addWidget(self.table, 1)
        layout.addWidget(close_button)
        self._load()

    def _load(self) -> None:
        rows = database.get_results()
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [row["username"], str(row["score"]), str(row["max_score"]), row["played_at"]]
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

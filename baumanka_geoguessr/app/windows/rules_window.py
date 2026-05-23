from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class RulesDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Правила")
        self.setMinimumSize(620, 520)
        layout = QVBoxLayout(self)
        title = QLabel("Правила игры")
        title.setObjectName("TitleLabel")
        text = QLabel(
            """
            <p><b>Цель:</b> по фотографии понять, где она сделана в главном здании, выбрать этаж и поставить точку на карте.</p>
            <p><b>Раундов:</b> 6. Максимум за игру: 30 очков.</p>
            <p><b>Карта:</b> открывается в отдельном фиксированном окне 1100×700, чтобы координаты не гуляли, как кот по клавиатуре.</p>
            <p><b>Расстояние:</b> считается по прямой между выбранной точкой и правильной меткой.</p>
            <p>Если этаж выбран неверно, добавляется штраф: <b>4 м × разница этажей</b>.</p>
            <p><b>Очки:</b></p>
            <ul>
                <li>меньше 5 м: 5 очков;</li>
                <li>меньше 10 м: 4 очка;</li>
                <li>меньше 20 м: 3 очка;</li>
                <li>меньше 30 м: 2 очка;</li>
                <li>меньше 40 м: 1 очко;</li>
                <li>40 м и больше: 0 очков.</li>
            </ul>
            <p><b>Редактор:</b> позволяет добавлять этажи, схемы, фотографии и правильные точки без ручного редактирования базы.</p>
            """
        )
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignTop)
        close_button = QPushButton("Понятно")
        close_button.clicked.connect(self.accept)
        layout.addWidget(title)
        layout.addWidget(text, 1)
        layout.addWidget(close_button)

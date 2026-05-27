from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from app.widgets.logo_header import build_logo_header


class RulesDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(620, 520)

        # Разрешаем сворачивание/разворачивание
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        # Горячая клавиша F11
        from PySide6.QtGui import QKeySequence, QShortcut
        self.fs_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.fs_shortcut.activated.connect(self._toggle_fullscreen)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        title = build_logo_header(title_size=34, icon_size=72, spacing=10)

        card = QWidget()
        card.setObjectName("GlassCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)

        text = QLabel(
            """
            <p><b>Раундов:</b> 6</p>
            <p><b>Максимум:</b> 30 очков</p>
            <p><b>Как играть:</b> по фотографии выбрать этаж и поставить точку на карте.</p>
            <p><b>Расстояние:</b> считается по прямой между выбранной точкой и правильной меткой.</p>
            <p><b>Штраф за неверный этаж:</b> 15 м × разница этажей.</p>
            <p><b>Очки:</b></p>
            <ul>
                <li>меньше 5 м: 5 очков;</li>
                <li>меньше 10 м: 4 очка;</li>
                <li>меньше 20 м: 3 очка;</li>
                <li>меньше 30 м: 2 очка;</li>
                <li>меньше 40 м: 1 очко;</li>
                <li>40 м и больше: 0 очков.</li>
            </ul>
            """
        )
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignTop)
        card_layout.addWidget(text)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(card, 1)
        layout.addWidget(close_button)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

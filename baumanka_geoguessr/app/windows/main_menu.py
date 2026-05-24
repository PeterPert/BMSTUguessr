from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.theme import get_colors
from app.windows.editor_window import EditorWindow
from app.windows.game_window import GameWindow
from app.windows.results_window import ResultsDialog
from app.windows.rules_window import RulesDialog
from app.windows.settings_window import SettingsWindow


class MainMenuWindow(QMainWindow):
    switch_user_requested = Signal()

    def __init__(self, user: dict) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle("Baumanka GeoGuessr")
        self.setMinimumSize(520, 640)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        title = QLabel("Baumanka GeoGuessr")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Локальный геогессер по главному зданию Бауманки")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        self.user_label = QLabel(f"Текущий игрок: {self.user['username']}")
        self.user_label.setAlignment(Qt.AlignCenter)
        c = get_colors()
        self.user_label.setStyleSheet(f"font-weight: 700; color: {c.user_accent};")

        start_button = QPushButton("Начать игру")
        editor_button = QPushButton("Редактор")
        settings_button = QPushButton("Настройки")
        rules_button = QPushButton("Правила")
        results_button = QPushButton("Результаты")
        switch_button = QPushButton("Сменить пользователя")
        exit_button = QPushButton("Выход")
        for button in (settings_button, rules_button, results_button, switch_button, exit_button):
            button.setObjectName("SecondaryButton")

        start_button.clicked.connect(self._start_game)
        editor_button.clicked.connect(self._open_editor)
        settings_button.clicked.connect(self._open_settings)
        rules_button.clicked.connect(self._open_rules)
        results_button.clicked.connect(self._open_results)
        switch_button.clicked.connect(self.switch_user_requested.emit)
        exit_button.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.user_label)
        layout.addSpacing(20)
        for button in (start_button, editor_button, settings_button, rules_button, results_button, switch_button, exit_button):
            button.setMinimumHeight(46)
            layout.addWidget(button)
        layout.addStretch(1)

        self.info_label = QLabel("Совет: сначала откройте редактор и добавьте хотя бы 6 фото-меток.")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(f"color: {c.hint_text}; font-size: 12px;")
        layout.addWidget(self.info_label)

        self.setCentralWidget(central)

    def _start_game(self) -> None:
        dialog = GameWindow(self.user, self)
        dialog.exec()

    def _open_editor(self) -> None:
        dialog = EditorWindow(self)
        dialog.exec()

    def _open_settings(self) -> None:
        SettingsWindow(self).exec()

    def _open_rules(self) -> None:
        RulesDialog(self).exec()

    def _open_results(self) -> None:
        ResultsDialog(self).exec()

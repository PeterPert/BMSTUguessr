from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from app.widgets.logo_header import build_logo_header

from app.windows.editor_window import EditorWindow
from app.windows.game_window import GameWindow
from app.windows.rules_window import RulesDialog


class MainMenuWindow(QMainWindow):
    def __init__(self, session: dict) -> None:
        super().__init__()
        self.session = session
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(520, 620)

        # Горячая клавиша F11 для перехода в полноэкранный режим
        from PySide6.QtGui import QKeySequence, QShortcut

        self.fs_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.fs_shortcut.activated.connect(self._toggle_fullscreen)

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        title = build_logo_header(title_size=44, icon_size=96, spacing=14)

        layout.addStretch(1)
        layout.addWidget(title)

        if self.session.get("is_admin"):
            admin_label = QLabel(f"Администратор: {self.session.get('admin_username')}")
            admin_label.setAlignment(Qt.AlignCenter)
            admin_label.setObjectName("SubtitleLabel")
            layout.addWidget(admin_label)

        start_button = QPushButton("Начать игру")
        start_button.setMinimumHeight(48)
        start_button.clicked.connect(self._start_game)
        layout.addWidget(start_button)

        if self.session.get("is_admin"):
            editor_button = QPushButton("Редактор")
            editor_button.setMinimumHeight(48)
            editor_button.clicked.connect(self._open_editor)
            layout.addWidget(editor_button)

        rules_button = QPushButton("Правила")
        rules_button.setObjectName("SecondaryButton")
        rules_button.setMinimumHeight(46)
        rules_button.clicked.connect(self._open_rules)
        layout.addWidget(rules_button)

        exit_button = QPushButton("Выход")
        exit_button.setObjectName("SecondaryButton")
        exit_button.setMinimumHeight(46)
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button)

        layout.addStretch(1)
        self.setCentralWidget(central)

    def _start_game(self) -> None:
        dialog = GameWindow(self)
        dialog.exec()

    def _open_editor(self) -> None:
        dialog = EditorWindow(self)
        dialog.exec()

    def _open_rules(self) -> None:
        RulesDialog(self).exec()

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

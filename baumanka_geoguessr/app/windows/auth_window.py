from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import database


class AuthDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.user: dict | None = None
        self.setWindowTitle("Вход в Baumanka GeoGuessr")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(14)

        title = QLabel("Baumanka GeoGuessr")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Войдите или зарегистрируйтесь, чтобы сохранять результаты")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("например: prostonet690")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("минимум 8 символов, буква и цифра")
        form.addRow("Никнейм:", self.username_edit)
        form.addRow("Пароль:", self.password_edit)

        buttons = QHBoxLayout()
        self.login_button = QPushButton("Войти")
        self.register_button = QPushButton("Зарегистрироваться")
        self.register_button.setObjectName("SecondaryButton")
        buttons.addWidget(self.login_button)
        buttons.addWidget(self.register_button)

        

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(form_widget)
        root.addLayout(buttons)

        self.login_button.clicked.connect(self._login)
        self.register_button.clicked.connect(self._register)
        self.password_edit.returnPressed.connect(self._login)

    def _login(self) -> None:
        ok, message, user = database.authenticate_user(
            self.username_edit.text(), self.password_edit.text()
        )
        if not ok:
            QMessageBox.warning(self, "Вход", message)
            return
        self.user = user
        self.accept()

    def _register(self) -> None:
        ok, message, user = database.create_user(
            self.username_edit.text(), self.password_edit.text()
        )
        if not ok:
            QMessageBox.warning(self, "Регистрация", message)
            return
        self.user = user
        QMessageBox.information(self, "Регистрация", "Пользователь создан. Входим в игру.")
        self.accept()

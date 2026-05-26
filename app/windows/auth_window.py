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
from app.widgets.logo_header import build_logo_header


class AdminLoginDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.admin: dict | None = None
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(14)

        title = build_logo_header(title_size=30, icon_size=64, spacing=8)

        card = QWidget()
        card.setObjectName("GlassCard")
        form = QFormLayout(card)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Логин:", self.username_edit)
        form.addRow("Пароль:", self.password_edit)

        buttons = QHBoxLayout()
        self.login_button = QPushButton("Войти")
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setObjectName("SecondaryButton")
        buttons.addWidget(self.login_button)
        buttons.addWidget(self.cancel_button)

        root.addWidget(title)
        root.addWidget(card)
        root.addLayout(buttons)

        self.login_button.clicked.connect(self._login)
        self.cancel_button.clicked.connect(self.reject)
        self.password_edit.returnPressed.connect(self._login)

    def _login(self) -> None:
        ok, message, admin = database.authenticate_admin(
            self.username_edit.text(), self.password_edit.text()
        )
        if not ok:
            QMessageBox.warning(self, "Вход", message)
            return
        self.admin = admin
        self.accept()


class StartDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.session: dict | None = None
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(520, 360)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 30, 32, 28)
        root.setSpacing(18)
        root.setAlignment(Qt.AlignCenter)

        title = build_logo_header(title_size=40, icon_size=88, spacing=12)

        card = QWidget()
        card.setObjectName("GlassCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 22)
        card_layout.setSpacing(16)

        self.continue_button = QPushButton("Продолжить")
        self.continue_button.setMinimumHeight(56)
        self.admin_button = QPushButton("Войти как администратор")
        self.admin_button.setObjectName("SecondaryButton")
        self.admin_button.setMinimumHeight(36)

        admin_row = QHBoxLayout()
        admin_row.addStretch(1)
        admin_row.addWidget(self.admin_button)
        admin_row.addStretch(1)

        card_layout.addWidget(self.continue_button)
        card_layout.addLayout(admin_row)

        root.addStretch(1)
        root.addWidget(title)
        root.addWidget(card)
        root.addStretch(1)

        self.continue_button.clicked.connect(self._continue_as_guest)
        self.admin_button.clicked.connect(self._login_as_admin)

    def _continue_as_guest(self) -> None:
        self.session = {"is_admin": False, "admin_username": None}
        self.accept()

    def _login_as_admin(self) -> None:
        dialog = AdminLoginDialog(self)
        if dialog.exec() != QDialog.Accepted or dialog.admin is None:
            return
        self.session = {
            "is_admin": True,
            "admin_username": dialog.admin["username"],
        }
        self.accept()

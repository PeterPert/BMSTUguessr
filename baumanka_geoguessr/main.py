from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app import database
from app.style import APP_STYLE
from app.windows.auth_window import AuthDialog
from app.windows.main_menu import MainMenuWindow


class AppController:
    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(APP_STYLE)
        database.initialize_db()
        self.window: MainMenuWindow | None = None

    def run(self) -> int:
        self._show_auth()
        return self.app.exec()

    def _show_auth(self) -> None:
        dialog = AuthDialog()
        if dialog.exec() != AuthDialog.Accepted or dialog.user is None:
            self.app.quit()
            return
        self._show_main_menu(dialog.user)

    def _show_main_menu(self, user: dict) -> None:
        if self.window is not None:
            self.window.close()
        self.window = MainMenuWindow(user)
        self.window.switch_user_requested.connect(self._switch_user)
        self.window.show()

    def _switch_user(self) -> None:
        if self.window is not None:
            self.window.hide()
        self._show_auth()


if __name__ == "__main__":
    controller = AppController()
    sys.exit(controller.run())

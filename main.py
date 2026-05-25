from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app import database
from app.theme import apply_theme, load_theme
from app.windows.auth_window import StartDialog
from app.windows.main_menu import MainMenuWindow


class AppController:
    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        load_theme()
        apply_theme(self.app)
        database.initialize_db()
        self.window: MainMenuWindow | None = None

    def run(self) -> int:
        self._show_start()
        return self.app.exec()

    def _show_start(self) -> None:
        dialog = StartDialog()
        if dialog.exec() != StartDialog.Accepted or dialog.session is None:
            self.app.quit()
            return
        self.window = MainMenuWindow(dialog.session)
        self.window.show()


if __name__ == "__main__":
    controller = AppController()
    sys.exit(controller.run())

from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import database, paths
from app.scoring import calculate_distance_meters, points_for_distance
from app.widgets.map_canvas import build_scaled_result_pixmap
from app.windows.map_dialogs import MapPickerDialog, ResultMapDialog

ROUNDS_PER_GAME = 6
MAX_SCORE = ROUNDS_PER_GAME * 5


class GameWindow(QDialog):
    def __init__(self, user: dict, parent=None) -> None:
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Игра")
        self.setMinimumSize(1040, 720)
        self.locations = database.get_locations()
        self.floors = database.get_floors()
        self.round_locations: list[dict] = []
        self.round_index = 0
        self.total_score = 0
        self.round_results: list[dict] = []
        self.result_saved = False
        self.current_result_context: dict | None = None
        self._build_ui()
        self._prepare_game()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.title = QLabel("Раунд 1/6")
        self.title.setObjectName("TitleLabel")
        self.score_label = QLabel("Счёт: 0/30")
        self.score_label.setObjectName("SubtitleLabel")
        top.addWidget(self.title)
        top.addStretch(1)
        top.addWidget(self.score_label)

        body = QHBoxLayout()
        self.photo_label = QLabel("Фото")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setMinimumSize(560, 520)
        self.photo_label.setStyleSheet("background: white; border: 1px solid #e3c2ca; border-radius: 16px;")

        side = QVBoxLayout()
        self.location_hint = QLabel("Угадайте место по фотографии")
        self.location_hint.setObjectName("SubtitleLabel")
        self.location_hint.setWordWrap(True)
        self.floor_combo = QComboBox()
        self.map_button = QPushButton("Карта")
        self.map_button.clicked.connect(self._open_guess_map)

        self.result_panel = QWidget()
        self.result_panel.setStyleSheet("background: #fff0f4; border: 1px solid #e3c2ca; border-radius: 16px;")
        result_layout = QVBoxLayout(self.result_panel)
        self.result_title = QLabel("Результат")
        self.result_title.setObjectName("SubtitleLabel")
        self.result_text = QLabel("")
        self.result_text.setWordWrap(True)
        self.result_map_label = QLabel()
        self.result_map_label.setAlignment(Qt.AlignCenter)
        self.open_full_result_button = QPushButton("Открыть большую карту результата")
        self.next_button = QPushButton("Следующий раунд")
        self.save_result_button = QPushButton("Сохранить результат")
        self.save_result_button.setObjectName("SecondaryButton")
        result_layout.addWidget(self.result_title)
        result_layout.addWidget(self.result_text)
        result_layout.addWidget(self.result_map_label)
        result_layout.addWidget(self.open_full_result_button)
        result_layout.addWidget(self.next_button)
        result_layout.addWidget(self.save_result_button)
        self.result_panel.hide()

        self.open_full_result_button.clicked.connect(self._open_full_result_map)
        self.next_button.clicked.connect(self._next_round)
        self.save_result_button.clicked.connect(self._save_result)

        side.addWidget(self.location_hint)
        side.addWidget(QLabel("Выберите этаж:"))
        side.addWidget(self.floor_combo)
        side.addWidget(self.map_button)
        side.addSpacing(16)
        side.addWidget(self.result_panel, 1)
        side.addStretch(1)

        body.addWidget(self.photo_label, 2)
        body.addLayout(side, 1)

        root.addLayout(top)
        root.addLayout(body, 1)

    def _prepare_game(self) -> None:
        if len(self.floors) == 0:
            QMessageBox.warning(self, "Игра", "Сначала добавьте хотя бы один этаж в редакторе.")
            self.reject()
            return
        if len(self.locations) < ROUNDS_PER_GAME:
            QMessageBox.warning(
                self,
                "Игра",
                f"Для полной игры нужно минимум {ROUNDS_PER_GAME} меток. Сейчас: {len(self.locations)}.\n"
                "Откройте редактор и добавьте фотографии с точками.",
            )
            self.reject()
            return
        self.floor_combo.clear()
        for floor in self.floors:
            self.floor_combo.addItem(f"{floor['floor_number']} этаж", int(floor["floor_number"]))
        self.round_locations = random.sample(self.locations, ROUNDS_PER_GAME)
        self.round_index = 0
        self.total_score = 0
        self.round_results.clear()
        self._show_round()

    def _show_round(self) -> None:
        self.result_panel.hide()
        self.map_button.setEnabled(True)
        self.floor_combo.setEnabled(True)
        location = self.round_locations[self.round_index]
        self.title.setText(f"Раунд {self.round_index + 1}/{ROUNDS_PER_GAME}")
        self.score_label.setText(f"Счёт: {self.total_score}/{MAX_SCORE}")
        self.location_hint.setText("Где сделано это фото? Выберите этаж и откройте карту.")
        pixmap = QPixmap(str(paths.resolve_path(location["image_path"])))
        if pixmap.isNull():
            self.photo_label.setText("Фото не удалось открыть")
            self.photo_label.setPixmap(QPixmap())
        else:
            self.photo_label.setText("")
            self.photo_label.setPixmap(
                pixmap.scaled(620, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        correct_floor_index = self.floor_combo.findData(int(location["floor"]))
        if correct_floor_index >= 0:
            self.floor_combo.setCurrentIndex(correct_floor_index)

    def _open_guess_map(self) -> None:
        guessed_floor = self.floor_combo.currentData()
        if guessed_floor is None:
            QMessageBox.warning(self, "Карта", "Выберите этаж.")
            return
        floor = database.get_floor(int(guessed_floor))
        if floor is None:
            QMessageBox.warning(self, "Карта", "Схема выбранного этажа не найдена.")
            return
        dialog = MapPickerDialog(paths.resolve_path(floor["map_path"]), self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_point:
            self._process_guess(int(guessed_floor), dialog.selected_point[0], dialog.selected_point[1])

    def _process_guess(self, guessed_floor: int, guessed_x: int, guessed_y: int) -> None:
        location = self.round_locations[self.round_index]
        correct_floor = int(location["floor"])
        correct_floor_data = database.get_floor(correct_floor)
        if correct_floor_data is None:
            QMessageBox.warning(self, "Результат", "Правильный этаж не найден в базе.")
            return
        distance = calculate_distance_meters(
            answer_x=int(location["answer_x"]),
            answer_y=int(location["answer_y"]),
            answer_floor=correct_floor,
            guessed_x=guessed_x,
            guessed_y=guessed_y,
            guessed_floor=guessed_floor,
            meters_per_pixel=float(correct_floor_data["meters_per_pixel"]),
        )
        points = points_for_distance(distance)
        self.total_score += points

        result_item = {
            "location_id": int(location["id"]),
            "guessed_x": guessed_x,
            "guessed_y": guessed_y,
            "guessed_floor": guessed_floor,
            "distance_meters": distance,
            "points": points,
        }
        self.round_results.append(result_item)

        markers = [
            (guessed_x, guessed_y, "#2aa876", "ваш ответ"),
            (int(location["answer_x"]), int(location["answer_y"]), "#dd3344", "правильно"),
        ]
        lines = [
            (guessed_x, guessed_y, int(location["answer_x"]), int(location["answer_y"]), "#6d4a59")
        ]
        correct_map_path = paths.resolve_path(correct_floor_data["map_path"])
        self.current_result_context = {
            "map_path": correct_map_path,
            "markers": markers,
            "lines": lines,
        }

        title = location["title"] or "Без названия"
        floor_note = ""
        if guessed_floor != correct_floor:
            floor_note = f"<br>Штраф за этаж: {4 * abs(correct_floor - guessed_floor)} м."
        self.result_text.setText(
            f"<b>{title}</b><br>"
            f"Ваш этаж: {guessed_floor}. Правильный этаж: {correct_floor}.<br>"
            f"Расстояние: <b>{distance:.1f} м</b>.{floor_note}<br>"
            f"Очки за раунд: <b>{points}/5</b>."
        )
        self.result_map_label.setPixmap(
            build_scaled_result_pixmap(correct_map_path, markers, lines)
        )
        self.map_button.setEnabled(False)
        self.floor_combo.setEnabled(False)
        self.score_label.setText(f"Счёт: {self.total_score}/{MAX_SCORE}")

        if self.round_index == ROUNDS_PER_GAME - 1:
            self.next_button.hide()
            self.save_result_button.show()
            self.result_title.setText("Финальный результат")
            self.location_hint.setText(f"Игра завершена. Итог: {self.total_score}/{MAX_SCORE}.")
        else:
            self.next_button.show()
            self.save_result_button.hide()
            self.result_title.setText("Результат раунда")

        self._fade_in_result_panel()

    def _fade_in_result_panel(self) -> None:
        self.result_panel.show()
        effect = QGraphicsOpacityEffect(self.result_panel)
        self.result_panel.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(450)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start(QPropertyAnimation.DeleteWhenStopped)

    def _next_round(self) -> None:
        if self.round_index < ROUNDS_PER_GAME - 1:
            self.round_index += 1
            self._show_round()

    def _open_full_result_map(self) -> None:
        if not self.current_result_context:
            return
        ResultMapDialog(
            self.current_result_context["map_path"],
            self.current_result_context["markers"],
            self.current_result_context["lines"],
            self,
        ).exec()

    def _save_result(self) -> None:
        if self.result_saved:
            QMessageBox.information(self, "Сохранение", "Этот результат уже сохранён.")
            return
        result_id = database.save_game_result(
            self.user["id"],
            self.total_score,
            self.round_results,
            MAX_SCORE,
        )
        self.result_saved = True
        self.save_result_button.setEnabled(False)
        self.save_result_button.setText("Результат сохранён")
        QMessageBox.information(self, "Сохранение", f"Результат сохранён под номером {result_id}.")

from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app import database, paths
from app.scoring import FLOOR_PENALTY_METERS, calculate_distance_meters, points_for_distance
from app.theme import get_colors
from app.widgets.map_canvas import build_scaled_result_pixmap
from app.windows.map_dialogs import MapPickerDialog, ResultMapDialog

ROUNDS_PER_GAME = 6
MAX_SCORE = ROUNDS_PER_GAME * 5


class FinalScoreDialog(QDialog):
    def __init__(self, score: int, max_score: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(480, 320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(16)

        title = QLabel("BMSTUguessr")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)

        card = QWidget()
        card.setObjectName("ResultCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(12)

        score_label = QLabel(f"{score} / {max_score}")
        score_label.setObjectName("GameScoreLabel")
        score_label.setAlignment(Qt.AlignCenter)

        text = QLabel("Игра завершена")
        text.setAlignment(Qt.AlignCenter)
        text.setObjectName("SubtitleLabel")

        button = QPushButton("В главное меню")
        button.setMinimumHeight(48)
        button.clicked.connect(self.accept)

        card_layout.addWidget(score_label)
        card_layout.addWidget(text)

        layout.addWidget(title)
        layout.addWidget(card, 1)
        layout.addWidget(button)


class GameWindow(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(1000, 700)
        self.locations = database.get_locations()
        self.floors = database.get_floors()
        self.round_locations: list[dict] = []
        self.round_index = 0
        self.total_score = 0
        self.round_results: list[dict] = []
        self.current_result_context: dict | None = None
        self._showing_result = False
        self._current_photo_path: str | Path | None = None
        self._build_ui()
        self._prepare_game()

    def _build_ui(self) -> None:
        c = get_colors()
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(16)
        self.brand_title = QLabel("BMSTUguessr")
        self.brand_title.setObjectName("TitleLabel")
        self.round_title = QLabel("Раунд 1 / 6")
        self.round_title.setObjectName("SubtitleLabel")
        self.score_label = QLabel("0 / 30")
        self.score_label.setObjectName("GameScoreLabel")
        self.score_label.setAlignment(Qt.AlignCenter)
        top.addWidget(self.brand_title)
        top.addStretch(1)
        top.addWidget(self.round_title)
        top.addStretch(1)
        top.addWidget(self.score_label)

        body = QHBoxLayout()
        body.setSpacing(16)

        self.main_visual = QLabel("")
        self.main_visual.setAlignment(Qt.AlignCenter)
        self.main_visual.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_visual.setMinimumSize(400, 300)
        self.main_visual.setStyleSheet(
            f"background: {c.input_background}; border: 2px solid {c.border}; border-radius: 16px;"
        )

        side = QVBoxLayout()
        side.setSpacing(10)

        play_controls = QWidget()
        play_controls.setObjectName("GlassCard")
        play_layout = QVBoxLayout(play_controls)
        play_layout.setContentsMargins(16, 16, 16, 16)
        play_layout.setSpacing(10)
        self.floor_combo = QComboBox()
        self.map_button = QPushButton("Открыть карту")
        self.map_button.setMinimumHeight(44)
        play_layout.addWidget(QLabel("Этаж"))
        play_layout.addWidget(self.floor_combo)
        play_layout.addWidget(self.map_button)
        self.play_controls = play_controls

        self.result_panel = QWidget()
        self.result_panel.setObjectName("GlassCard")
        result_layout = QVBoxLayout(self.result_panel)
        result_layout.setContentsMargins(14, 14, 14, 14)
        result_layout.setSpacing(10)

        self.result_title = QLabel("Результат")
        self.result_title.setObjectName("EditorSectionTitle")
        self.round_points_label = QLabel("+0")
        self.round_points_label.setObjectName("GameRoundPoints")
        self.round_points_label.setAlignment(Qt.AlignCenter)

        points_row = QHBoxLayout()
        points_row.addStretch(1)
        points_row.addWidget(self.round_points_label)
        points_row.addStretch(1)

        self.legend_label = QLabel()
        self.legend_label.setAlignment(Qt.AlignCenter)
        self._update_legend()

        self.result_text = QLabel("")
        self.result_text.setWordWrap(True)
        self.result_text.setStyleSheet(f"font-size: 14px; color: {c.text}; line-height: 1.4;")

        self.open_full_result_button = QPushButton("Карта на весь экран")
        self.open_full_result_button.setObjectName("SecondaryButton")
        self.open_full_result_button.setMinimumHeight(40)

        self.next_button = QPushButton("Следующий раунд")
        self.next_button.setObjectName("GameNextButton")
        self.next_button.setMinimumHeight(54)

        result_layout.addWidget(self.result_title)
        result_layout.addLayout(points_row)
        result_layout.addWidget(self.legend_label)
        result_layout.addWidget(self.result_text)
        result_layout.addWidget(self.open_full_result_button)
        result_layout.addWidget(self.next_button)
        self.result_panel.hide()

        side.addWidget(self.play_controls)
        side.addWidget(self.result_panel, 1)

        body.addWidget(self.main_visual, 3)
        body.addLayout(side, 2)

        root.addLayout(top)
        root.addLayout(body, 1)

        self.map_button.clicked.connect(self._open_guess_map)
        self.open_full_result_button.clicked.connect(self._open_full_result_map)
        self.next_button.clicked.connect(self._next_round)

    def _update_legend(self) -> None:
        c = get_colors()
        self.legend_label.setText(
            f'<span style="color:{c.marker_guess}; font-size:16px; font-weight:bold;">●</span> ваш ответ &nbsp;&nbsp; '
            f'<span style="color:{c.marker_correct}; font-size:16px; font-weight:bold;">●</span> правильное место'
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._showing_result:
            self._update_result_map_pixmap()
        elif self._current_photo_path is not None:
            self._update_photo_pixmap()

    def _populate_floor_combo(self) -> None:
        self.floor_combo.clear()
        self.floor_combo.addItem("Выберите этаж", None)
        for floor in self.floors:
            self.floor_combo.addItem(f"{floor['floor_number']} этаж", int(floor["floor_number"]))
        self.floor_combo.setCurrentIndex(0)

    def _prepare_game(self) -> None:
        if len(self.floors) == 0:
            QMessageBox.warning(self, "BMSTUguessr", "Нет доступных этажей.")
            self.reject()
            return
        if len(self.locations) < ROUNDS_PER_GAME:
            QMessageBox.warning(
                self,
                "BMSTUguessr",
                f"Для игры требуется минимум {ROUNDS_PER_GAME} меток. Сейчас: {len(self.locations)}.",
            )
            self.reject()
            return
        self._populate_floor_combo()
        self.round_locations = random.sample(self.locations, ROUNDS_PER_GAME)
        self.round_index = 0
        self.total_score = 0
        self.round_results.clear()
        self._show_round()

    def _set_play_mode(self) -> None:
        self._showing_result = False
        self.current_result_context = None
        self.result_panel.hide()
        self.play_controls.show()
        c = get_colors()
        self.main_visual.setStyleSheet(
            f"background: {c.input_background}; border: 2px solid {c.border}; border-radius: 16px;"
        )

    def _set_result_mode(self) -> None:
        self._showing_result = True
        self.play_controls.hide()
        self.result_panel.show()
        c = get_colors()
        self.main_visual.setStyleSheet(
            f"background: {c.map_frame_background}; border: 2px solid {c.map_frame_border}; border-radius: 16px;"
        )

    def _update_score_display(self) -> None:
        self.score_label.setText(f"{self.total_score} / {MAX_SCORE}")

    def _show_round(self) -> None:
        self._set_play_mode()
        self.map_button.setEnabled(True)
        self.floor_combo.setEnabled(True)
        self.floor_combo.setCurrentIndex(0)
        location = self.round_locations[self.round_index]
        self.round_title.setText(f"Раунд {self.round_index + 1} / {ROUNDS_PER_GAME}")
        self._update_score_display()
        self._current_photo_path = location["image_path"]
        pixmap = QPixmap(str(paths.resolve_path(location["image_path"])))
        if pixmap.isNull():
            self.main_visual.setText("Фото не удалось открыть")
            self.main_visual.setPixmap(QPixmap())
            self._current_photo_path = None
        else:
            self.main_visual.setText("")
            self._update_photo_pixmap()

    def _update_photo_pixmap(self) -> None:
        if self._current_photo_path is None:
            return
        pixmap = QPixmap(str(paths.resolve_path(self._current_photo_path)))
        if pixmap.isNull():
            return
        margin = 16
        w = max(200, self.main_visual.width() - margin)
        h = max(200, self.main_visual.height() - margin)
        self.main_visual.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _update_result_map_pixmap(self) -> None:
        if not self.current_result_context:
            return
        ctx = self.current_result_context
        margin = 20
        w = max(280, self.main_visual.width() - margin)
        h = max(220, self.main_visual.height() - margin)
        pixmap = build_scaled_result_pixmap(
            ctx["map_path"],
            ctx["markers"],
            ctx["lines"],
            max_width=w,
            max_height=h,
        )
        self.main_visual.setText("")
        self.main_visual.setPixmap(pixmap)

    def _open_guess_map(self) -> None:
        guessed_floor = self.floor_combo.currentData()
        if guessed_floor is None:
            QMessageBox.warning(self, "BMSTUguessr", "Сначала выберите этаж.")
            return
        floor = database.get_floor(int(guessed_floor))
        if floor is None:
            QMessageBox.warning(self, "BMSTUguessr", "Схема выбранного этажа не найдена.")
            return
        dialog = MapPickerDialog(paths.resolve_path(floor["map_path"]), self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_point:
            self._process_guess(int(guessed_floor), dialog.selected_point[0], dialog.selected_point[1])

    def _process_guess(self, guessed_floor: int, guessed_x: int, guessed_y: int) -> None:
        location = self.round_locations[self.round_index]
        correct_floor = int(location["floor"])
        correct_floor_data = database.get_floor(correct_floor)
        if correct_floor_data is None:
            QMessageBox.warning(self, "BMSTUguessr", "Правильный этаж не найден.")
            return

        floor_difference = abs(correct_floor - guessed_floor)
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

        self.round_results.append(
            {
                "location_title": location.get("title") or "Без названия",
                "image_path": location["image_path"],
                "answer_x": int(location["answer_x"]),
                "answer_y": int(location["answer_y"]),
                "answer_floor": correct_floor,
                "guessed_x": guessed_x,
                "guessed_y": guessed_y,
                "guessed_floor": guessed_floor,
                "distance_meters": distance,
                "points": points,
            }
        )

        c = get_colors()
        markers = [
            (guessed_x, guessed_y, c.marker_guess, "Ваш ответ"),
            (int(location["answer_x"]), int(location["answer_y"]), c.marker_correct, "Верно"),
        ]
        lines = [
            (
                guessed_x,
                guessed_y,
                int(location["answer_x"]),
                int(location["answer_y"]),
                c.marker_line,
            )
        ]
        correct_map_path = paths.resolve_path(correct_floor_data["map_path"])
        self.current_result_context = {
            "map_path": correct_map_path,
            "markers": markers,
            "lines": lines,
        }

        floor_note = ""
        if floor_difference:
            penalty = FLOOR_PENALTY_METERS * floor_difference
            floor_note = (
                f"<br>Штраф за этаж: <b>{penalty:.0f} м</b>"
            )

        self.result_text.setText(
            f"Ваш этаж: <b>{guessed_floor}</b><br>"
            f"Правильный этаж: <b>{correct_floor}</b><br>"
            f"Расстояние: <b>{distance:.1f} м</b>{floor_note}"
        )
        self.round_points_label.setText(f"+{points}")
        self._set_result_mode()
        self._update_result_map_pixmap()
        self.map_button.setEnabled(False)
        self.floor_combo.setEnabled(False)
        self._update_score_display()
        self._fade_in_result_panel()

        if self.round_index == ROUNDS_PER_GAME - 1:
            database.save_game_result(self.total_score, self.round_results, MAX_SCORE)
            final_dialog = FinalScoreDialog(self.total_score, MAX_SCORE, self)
            final_dialog.exec()
            self.accept()
            return

    def _fade_in_result_panel(self) -> None:
        effect = QGraphicsOpacityEffect(self.result_panel)
        self.result_panel.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(250)
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

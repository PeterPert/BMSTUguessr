from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGraphicsDropShadowEffect,
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
from app.scoring import (
    FLOOR_PENALTY_METERS,
    calculate_distance_meters,
    points_for_distance,
)
from app.theme import get_colors
from app.widgets.map_canvas import build_scaled_result_pixmap
from app.widgets.logo_header import build_logo_header, make_logo_pixmap
from app.windows.map_dialogs import MapPickerDialog, ResultMapDialog

ROUNDS_PER_GAME = 6
MAX_SCORE = ROUNDS_PER_GAME * 5


def make_pin_pixmap(color: str, width: int = 30, height: int = 40) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    pin_color = QColor(color)

    tip_x = width / 2
    tip_y = height - 3
    head_radius = width * 0.34
    center_x = tip_x
    center_y = height * 0.34

    path = QPainterPath()
    path.moveTo(QPointF(tip_x, tip_y))
    path.cubicTo(
        QPointF(width * 0.05, height * 0.58),
        QPointF(width * 0.05, height * 0.10),
        QPointF(center_x, height * 0.06),
    )
    path.cubicTo(
        QPointF(width * 0.95, height * 0.10),
        QPointF(width * 0.95, height * 0.58),
        QPointF(tip_x, tip_y),
    )
    path.closeSubpath()

    painter.setPen(Qt.NoPen)
    painter.setBrush(pin_color)
    painter.drawPath(path)

    painter.setBrush(QColor("white"))
    painter.drawEllipse(
        QPointF(center_x, center_y),
        head_radius * 0.38,
        head_radius * 0.38,
    )

    painter.end()
    return pixmap


def make_stat_icon(kind: str, size: int = 30) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    blue = QColor("#176ed2")
    dark_blue = QColor("#0b3b66")
    bg = QColor("#eaf6ff")
    border = QColor("#b8daf4")
    green = QColor("#22a447")
    red = QColor("#ef4444")

    painter.setPen(QPen(border, 1.4))
    painter.setBrush(bg)
    painter.drawEllipse(QRectF(2, 2, size - 4, size - 4))

    painter.setPen(QPen(blue, 2.0))
    painter.setBrush(Qt.NoBrush)

    if kind == "guess_floor":
        painter.drawRoundedRect(QRectF(9, 8, 12, 15), 2, 2)
        painter.drawLine(QPointF(12, 12), QPointF(18, 12))
        painter.drawLine(QPointF(12, 16), QPointF(18, 16))
        painter.drawLine(QPointF(12, 20), QPointF(18, 20))

        painter.setPen(Qt.NoPen)
        painter.setBrush(red)
        painter.drawEllipse(QPointF(21, 9), 3.2, 3.2)

    elif kind == "correct_floor":
        painter.drawRoundedRect(QRectF(7, 8, 12, 15), 2, 2)
        painter.drawLine(QPointF(10, 12), QPointF(16, 12))
        painter.drawLine(QPointF(10, 16), QPointF(16, 16))
        painter.drawLine(QPointF(10, 20), QPointF(16, 20))

        painter.setPen(QPen(green, 2.4))
        painter.drawLine(QPointF(18, 18), QPointF(21, 21))
        painter.drawLine(QPointF(21, 21), QPointF(26, 14))

    elif kind == "distance":
        painter.setPen(QPen(blue, 2.0))
        painter.drawEllipse(QPointF(size / 2, size / 2), 8, 8)
        painter.drawEllipse(QPointF(size / 2, size / 2), 4, 4)

        painter.setPen(Qt.NoPen)
        painter.setBrush(dark_blue)
        painter.drawEllipse(QPointF(size / 2, size / 2), 2, 2)

    elif kind == "floor_penalty":
        painter.setPen(QPen(blue, 2.0))
        painter.drawLine(QPointF(8, 10), QPointF(22, 10))
        painter.drawLine(QPointF(8, 20), QPointF(22, 20))

        painter.drawLine(QPointF(15, 8), QPointF(15, 22))
        painter.drawLine(QPointF(15, 8), QPointF(11, 12))
        painter.drawLine(QPointF(15, 8), QPointF(19, 12))
        painter.drawLine(QPointF(15, 22), QPointF(11, 18))
        painter.drawLine(QPointF(15, 22), QPointF(19, 18))

    elif kind == "round":
        painter.setPen(QPen(blue, 2.0))
        painter.drawRoundedRect(QRectF(8, 7, 14, 16), 3, 3)
        painter.drawLine(QPointF(11, 12), QPointF(19, 12))
        painter.drawLine(QPointF(11, 17), QPointF(19, 17))

    elif kind == "map":
        painter.setPen(QPen(blue, 2.0))
        painter.drawRoundedRect(QRectF(7, 8, 16, 14), 3, 3)
        painter.drawLine(QPointF(12, 8), QPointF(12, 22))
        painter.drawLine(QPointF(18, 8), QPointF(18, 22))
        painter.setPen(Qt.NoPen)
        painter.setBrush(red)
        painter.drawEllipse(QPointF(17.5, 13), 2.7, 2.7)

    painter.end()
    return pixmap


class FinalScoreDialog(QDialog):
    def __init__(self, score: int, max_score: int, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(520, 360)

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eef8ff,
                    stop:1 #c9eafc
                );
            }
            """)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(18)

        title = build_logo_header(title_size=32, icon_size=72, spacing=10)

        card = QWidget()
        card.setObjectName("FinalCard")
        card.setStyleSheet("""
            QWidget#FinalCard {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid #a8d3f1;
                border-radius: 24px;
            }
            """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 26)
        card_layout.setSpacing(18)

        subtitle = QLabel("Игра завершена")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #355f82;
                font-size: 18px;
                font-weight: 800;
            }
            """)

        score_label = QLabel(f"{score} / {max_score}")
        score_label.setAlignment(Qt.AlignCenter)
        score_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fcff,
                    stop:1 #deefff
                );
                border: 1px solid #b7daf5;
                border-radius: 20px;
                color: #0a66b2;
                font-size: 46px;
                font-weight: 900;
                padding: 26px;
            }
            """)

        menu_button = QPushButton("В главное меню")
        menu_button.setMinimumHeight(52)
        menu_button.setStyleSheet("""
            QPushButton {
                background: #0b8fd8;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 900;
                padding: 14px;
            }
            QPushButton:hover {
                background: #0878b8;
            }
            """)
        menu_button.clicked.connect(self.accept)

        card_layout.addWidget(subtitle)
        card_layout.addWidget(score_label)

        root.addWidget(title)
        root.addWidget(card, 1)
        root.addWidget(menu_button)


class GameWindow(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(1220, 760)
        self.resize(1320, 800)

        # Разрешаем сворачивание/разворачивание
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        # Горячая клавиша F11 для перехода в полноэкранный режим
        from PySide6.QtGui import QKeySequence, QShortcut

        self.fs_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.fs_shortcut.activated.connect(self._toggle_fullscreen)

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

    def _apply_soft_shadow(self, widget: QWidget) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(120, 170, 210, 60))
        widget.setGraphicsEffect(shadow)

    def _build_ui(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eef8ff,
                    stop:1 #bfe7fb
                );
            }
            """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 20)
        root.setSpacing(16)

        header = self._build_header()

        body = QHBoxLayout()
        body.setSpacing(16)

        left_card = self._build_left_card()

        right_column = QVBoxLayout()
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.setSpacing(14)

        self.play_controls = self._build_play_controls()
        self.result_panel = self._build_result_panel()

        right_column.addWidget(self.play_controls, 0, Qt.AlignTop)
        right_column.addWidget(self.result_panel, 0, Qt.AlignTop)
        right_column.addStretch(1)

        body.addWidget(left_card, 7)
        body.addLayout(right_column, 3)

        root.addWidget(header)
        root.addLayout(body, 1)

        self.map_button.clicked.connect(self._open_guess_map)
        self.open_full_result_button.clicked.connect(self._open_full_result_map)
        self.next_button.clicked.connect(self._next_round)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("HeaderCard")
        header.setStyleSheet("""
            QWidget#HeaderCard {
                background: rgba(255, 255, 255, 0.62);
                border: 1px solid #c8e4f7;
                border-radius: 22px;
            }
            """)
        self._apply_soft_shadow(header)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 14, 22, 14)
        layout.setSpacing(18)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)

        pin_icon = QLabel()
        pin_icon.setPixmap(make_logo_pixmap(44))
        pin_icon.setFixedSize(48, 48)
        pin_icon.setAlignment(Qt.AlignCenter)
        pin_icon.setStyleSheet("background: transparent; border: none;")

        self.brand_title = QLabel("BMSTUguessr")
        self.brand_title.setStyleSheet("""
            QLabel {
                color: #0b3b66;
                font-size: 32px;
                font-weight: 900;
                background: transparent;
                border: none;
            }
            """)

        brand_row.addWidget(pin_icon)
        brand_row.addWidget(self.brand_title)

        self.round_title = QLabel("Раунд 1 из 6")
        self.round_title.setAlignment(Qt.AlignCenter)
        self.round_title.setMinimumWidth(168)
        self.round_title.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid #bdddf4;
                border-radius: 18px;
                color: #17486f;
                font-size: 16px;
                font-weight: 900;
                padding: 10px 18px;
            }
            """)

        self.score_label = QLabel("0 / 30")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setMinimumWidth(150)
        self.score_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2196f3,
                    stop:1 #176ed2
                );
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 30px;
                font-weight: 900;
                padding: 10px 22px;
            }
            """)

        layout.addLayout(brand_row, 1)
        layout.addStretch(1)
        layout.addWidget(self.round_title)
        layout.addStretch(1)
        layout.addWidget(self.score_label)

        return header

    def _build_left_card(self) -> QWidget:
        left_card = QWidget()
        left_card.setObjectName("MapCard")
        left_card.setStyleSheet("""
            QWidget#MapCard {
                background: rgba(255, 255, 255, 0.90);
                border: 1px solid #a9d4f1;
                border-radius: 22px;
            }
            """)
        self._apply_soft_shadow(left_card)

        layout = QVBoxLayout(left_card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)

        self.main_visual = QLabel("")
        self.main_visual.setAlignment(Qt.AlignCenter)
        self.main_visual.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_visual.setMinimumSize(760, 560)
        self.main_visual.setStyleSheet("""
            QLabel {
                background: #f9fcff;
                border: 1px solid #d6eaf8;
                border-radius: 18px;
                padding: 8px;
            }
            """)

        layout.addWidget(self.main_visual, 1)
        return left_card

    def _build_play_controls(self) -> QWidget:
        card = QWidget()
        card.setObjectName("PlayCard")
        card.setMinimumWidth(360)
        card.setMaximumWidth(395)
        card.setStyleSheet("""
            QWidget#PlayCard {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid #aad4f1;
                border-radius: 20px;
            }
            """)
        self._apply_soft_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        title = QLabel("Ваш ход")
        title.setStyleSheet("""
            QLabel {
                color: #0f3253;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
                border: none;
            }
            """)

        status_label = QLabel("Выберите этаж")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setMinimumHeight(72)
        status_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fcff,
                    stop:1 #e1f1ff
                );
                border: 1px solid #b7daf5;
                border-radius: 18px;
                color: #0b69b8;
                font-size: 22px;
                font-weight: 900;
            }
            """)

        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("""
            QWidget {
                background: #dcecf8;
                border: none;
            }
            """)

        details_card = QWidget()
        details_card.setObjectName("MoveDetailsCard")
        details_card.setStyleSheet("""
            QWidget#MoveDetailsCard {
                background: transparent;
                border: none;
            }
            """)

        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)

        floor_row = QWidget()
        floor_row.setStyleSheet("background: transparent; border: none;")
        floor_layout = QHBoxLayout(floor_row)
        floor_layout.setContentsMargins(0, 0, 0, 0)
        floor_layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setPixmap(make_stat_icon("round", 30))
        icon_label.setStyleSheet("background: transparent; border: none;")

        floor_label = QLabel("Этаж:")
        floor_label.setStyleSheet("""
            QLabel {
                color: #2d4056;
                font-size: 15px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            """)

        floor_layout.addWidget(icon_label)
        floor_layout.addWidget(floor_label)
        floor_layout.addStretch(1)

        self.floor_combo = QComboBox()
        self.floor_combo.setMinimumHeight(50)
        self.floor_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.98);
                border: 1px solid #8ec7ec;
                border-radius: 14px;
                padding: 10px 14px;
                color: #102b46;
                font-size: 15px;
                font-weight: 800;
            }
            QComboBox:hover {
                border: 1px solid #1493db;
            }
            QComboBox::drop-down {
                border: none;
                width: 34px;
            }
            """)

        details_layout.addWidget(floor_row)
        details_layout.addWidget(self.floor_combo)

        self.map_button = QPushButton("Открыть карту  →")
        self.map_button.setMinimumHeight(56)
        self.map_button.setStyleSheet("""
            QPushButton {
                background: #1493db;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 900;
                padding: 14px;
            }
            QPushButton:hover {
                background: #0d7ec0;
            }
            QPushButton:disabled {
                background: #8fc6e8;
            }
            """)

        layout.addWidget(title)
        layout.addWidget(status_label)
        layout.addWidget(line)
        layout.addWidget(details_card)
        layout.addWidget(self.map_button)

        return card

    def _build_result_panel(self) -> QWidget:
        card = QWidget()
        card.setObjectName("ResultCard")
        card.setMinimumWidth(360)
        card.setMaximumWidth(395)
        card.setStyleSheet("""
            QWidget#ResultCard {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid #aad4f1;
                border-radius: 20px;
            }
            """)
        self._apply_soft_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        self.result_title = QLabel("Результат раунда")
        self.result_title.setStyleSheet("""
            QLabel {
                color: #0f3253;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
                border: none;
            }
            """)

        self.round_points_label = QLabel("+0")
        self.round_points_label.setAlignment(Qt.AlignCenter)
        self.round_points_label.setMinimumHeight(88)
        self.round_points_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fcff,
                    stop:1 #e1f1ff
                );
                border: 1px solid #b7daf5;
                border-radius: 18px;
                color: #0b69b8;
                font-size: 38px;
                font-weight: 900;
            }
            """)

        legend = QWidget()
        legend.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
            """)

        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(14)
        legend_layout.setAlignment(Qt.AlignCenter)

        guess_pin = QLabel()
        guess_pin.setPixmap(make_pin_pixmap("#ef4444", 22, 30))
        guess_pin.setFixedSize(24, 32)
        guess_pin.setStyleSheet("background: transparent; border: none;")

        guess_text = QLabel("Ваш ответ")
        guess_text.setStyleSheet("""
            QLabel {
                color: #23384f;
                font-size: 15px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            """)

        correct_pin = QLabel()
        correct_pin.setPixmap(make_pin_pixmap("#22a447", 22, 30))
        correct_pin.setFixedSize(24, 32)
        correct_pin.setStyleSheet("background: transparent; border: none;")

        correct_text = QLabel("Правильное место")
        correct_text.setStyleSheet("""
            QLabel {
                color: #23384f;
                font-size: 15px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            """)

        legend_layout.addWidget(guess_pin)
        legend_layout.addWidget(guess_text)
        legend_layout.addSpacing(8)
        legend_layout.addWidget(correct_pin)
        legend_layout.addWidget(correct_text)

        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("""
            QWidget {
                background: #dcecf8;
                border: none;
            }
            """)

        details_card = QWidget()
        details_card.setObjectName("DetailsCard")
        details_card.setStyleSheet("""
            QWidget#DetailsCard {
                background: transparent;
                border: none;
            }
            """)

        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)

        self.guessed_floor_value = QLabel("—")
        self.correct_floor_value = QLabel("—")
        self.distance_value = QLabel("—")
        self.penalty_value = QLabel("—")

        details_layout.addWidget(
            self._make_result_row("guess_floor", "Ваш этаж:", self.guessed_floor_value)
        )
        details_layout.addWidget(
            self._make_result_row(
                "correct_floor", "Правильный этаж:", self.correct_floor_value
            )
        )
        details_layout.addWidget(
            self._make_result_row("distance", "Расстояние:", self.distance_value)
        )
        details_layout.addWidget(
            self._make_result_row("floor_penalty", "Штраф за этаж:", self.penalty_value)
        )

        self.open_full_result_button = QPushButton("⛶  Карта на весь экран")
        self.open_full_result_button.setMinimumHeight(50)
        self.open_full_result_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.96);
                color: #0d5f96;
                border: 1px solid #b5d8f2;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 900;
                padding: 12px;
            }
            QPushButton:hover {
                background: #eef8ff;
            }
            """)

        self.next_button = QPushButton("Следующий раунд  →")
        self.next_button.setMinimumHeight(56)
        self.next_button.setStyleSheet("""
            QPushButton {
                background: #1493db;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 900;
                padding: 14px;
            }
            QPushButton:hover {
                background: #0d7ec0;
            }
            """)

        layout.addWidget(self.result_title)
        layout.addWidget(self.round_points_label)
        layout.addWidget(legend)
        layout.addWidget(line)
        layout.addWidget(details_card)
        layout.addWidget(self.open_full_result_button)
        layout.addWidget(self.next_button)

        card.hide()
        return card

    def _make_result_row(
        self, icon_kind: str, title: str, value_label: QLabel
    ) -> QWidget:
        row = QWidget()
        row.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
            """)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setPixmap(make_stat_icon(icon_kind, 30))
        icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
            """)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #2d4056;
                font-size: 15px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            """)

        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_label.setStyleSheet("""
            QLabel {
                color: #102b5c;
                font-size: 15px;
                font-weight: 900;
                background: transparent;
                border: none;
            }
            """)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(value_label)

        return row

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
            self.floor_combo.addItem(
                f"{floor['floor_number']} этаж",
                int(floor["floor_number"]),
            )

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

    def _set_result_mode(self) -> None:
        self._showing_result = True

        self.play_controls.hide()
        self.result_panel.show()

    def _update_score_display(self) -> None:
        self.score_label.setText(f"{self.total_score} / {MAX_SCORE}")

    def _show_round(self) -> None:
        self._set_play_mode()

        self.map_button.setEnabled(True)
        self.floor_combo.setEnabled(True)
        self.floor_combo.setCurrentIndex(0)

        location = self.round_locations[self.round_index]

        self.round_title.setText(f"Раунд {self.round_index + 1} из {ROUNDS_PER_GAME}")
        self._update_score_display()

        self._current_photo_path = location["image_path"]

        pixmap = QPixmap(str(paths.resolve_path(location["image_path"])))
        if pixmap.isNull():
            self.main_visual.setText("Фото не удалось открыть")
            self.main_visual.setPixmap(QPixmap())
            self._current_photo_path = None
            return

        self.main_visual.setText("")
        self._update_photo_pixmap()

    def _update_photo_pixmap(self) -> None:
        if self._current_photo_path is None:
            return

        pixmap = QPixmap(str(paths.resolve_path(self._current_photo_path)))
        if pixmap.isNull():
            return

        width = max(520, self.main_visual.width() - 16)
        height = max(380, self.main_visual.height() - 16)

        self.main_visual.setPixmap(
            pixmap.scaled(
                width,
                height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def _update_result_map_pixmap(self) -> None:
        if not self.current_result_context:
            return

        ctx = self.current_result_context

        width = max(520, self.main_visual.width() - 16)
        height = max(380, self.main_visual.height() - 16)

        pixmap = build_scaled_result_pixmap(
            ctx["map_path"],
            ctx["markers"],
            ctx["lines"],
            max_width=width,
            max_height=height,
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
            QMessageBox.warning(
                self, "BMSTUguessr", "Схема выбранного этажа не найдена."
            )
            return

        dialog = MapPickerDialog(paths.resolve_path(floor["map_path"]), self)

        if dialog.exec() == QDialog.Accepted and dialog.selected_point:
            self._process_guess(
                int(guessed_floor),
                dialog.selected_point[0],
                dialog.selected_point[1],
            )

    def _process_guess(
        self, guessed_floor: int, guessed_x: int, guessed_y: int
    ) -> None:
        location = self.round_locations[self.round_index]

        correct_floor = int(location["floor"])
        correct_floor_data = database.get_floor(correct_floor)

        if correct_floor_data is None:
            QMessageBox.warning(self, "BMSTUguessr", "Правильный этаж не найден.")
            return

        answer_x = int(location["answer_x"])
        answer_y = int(location["answer_y"])
        floor_difference = abs(correct_floor - guessed_floor)

        distance = calculate_distance_meters(
            answer_x=answer_x,
            answer_y=answer_y,
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
                "answer_x": answer_x,
                "answer_y": answer_y,
                "answer_floor": correct_floor,
                "guessed_x": guessed_x,
                "guessed_y": guessed_y,
                "guessed_floor": guessed_floor,
                "distance_meters": distance,
                "points": points,
            }
        )

        colors = get_colors()

        markers = [
            (guessed_x, guessed_y, colors.marker_guess, ""),
            (answer_x, answer_y, colors.marker_correct, ""),
        ]

        lines = [
            (
                guessed_x,
                guessed_y,
                answer_x,
                answer_y,
                colors.marker_line,
            )
        ]

        correct_map_path = paths.resolve_path(correct_floor_data["map_path"])

        self.current_result_context = {
            "map_path": correct_map_path,
            "markers": markers,
            "lines": lines,
        }

        floor_penalty = FLOOR_PENALTY_METERS * floor_difference

        self.guessed_floor_value.setText(str(guessed_floor))
        self.correct_floor_value.setText(str(correct_floor))
        self.distance_value.setText(f"{distance:.1f} м")
        self.penalty_value.setText(f"{floor_penalty:.0f} м")

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

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

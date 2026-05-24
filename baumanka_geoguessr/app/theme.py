from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.paths import DATA_DIR

THEME_PATH = DATA_DIR / "theme.json"


@dataclass
class ThemeColors:
    background: str = "#fff7ef"
    text: str = "#3b2630"
    title: str = "#9b3754"
    subtitle: str = "#7a5962"
    user_accent: str = "#70404e"
    hint_text: str = "#7a5962"

    button_primary: str = "#c95b78"
    button_primary_hover: str = "#b84a68"
    button_disabled: str = "#d8b8c0"
    button_secondary: str = "#e9c79c"
    button_secondary_hover: str = "#ddb77f"
    button_secondary_text: str = "#5a3d23"

    input_background: str = "#ffffff"
    input_border: str = "#d6aab4"

    border: str = "#e3c2ca"
    card_background: str = "#fff0f4"
    panel_background: str = "#fffaf5"
    map_frame_background: str = "#f5eef2"
    map_frame_border: str = "#b87b8e"

    table_header_background: str = "#f4d4de"
    table_header_text: str = "#633141"
    table_grid: str = "#ead6dc"
    table_selected: str = "#f4d4de"

    tab_background: str = "#f4d4de"
    tab_text: str = "#633141"
    tab_selected_background: str = "#fffaf5"
    tab_selected_text: str = "#9b3754"

    status_ok: str = "#2d7a52"
    status_pending: str = "#7a5962"

    marker_guess: str = "#44B85C"
    marker_correct: str = "#E42313"
    marker_line: str = "#8B6B72"
    marker_label: str = "#4d2732"
    placeholder: str = "#f9d9e4"


COLOR_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Основное",
        [
            ("background", "Фон окон"),
            ("text", "Основной текст"),
            ("title", "Заголовки"),
            ("subtitle", "Подзаголовки"),
            ("user_accent", "Акцент имени игрока"),
            ("hint_text", "Подсказки"),
        ],
    ),
    (
        "Кнопки",
        [
            ("button_primary", "Основная кнопка"),
            ("button_primary_hover", "Основная — наведение"),
            ("button_disabled", "Недоступная кнопка"),
            ("button_secondary", "Вторичная кнопка"),
            ("button_secondary_hover", "Вторичная — наведение"),
            ("button_secondary_text", "Текст вторичной кнопки"),
        ],
    ),
    (
        "Поля и рамки",
        [
            ("input_background", "Фон полей ввода"),
            ("input_border", "Рамка полей"),
            ("border", "Общая рамка"),
            ("card_background", "Фон карточек"),
            ("panel_background", "Фон панелей"),
        ],
    ),
    (
        "Таблицы и вкладки",
        [
            ("table_header_background", "Шапка таблицы"),
            ("table_header_text", "Текст шапки"),
            ("table_grid", "Сетка таблицы"),
            ("table_selected", "Выбранная строка"),
            ("tab_background", "Вкладка"),
            ("tab_text", "Текст вкладки"),
            ("tab_selected_background", "Активная вкладка"),
            ("tab_selected_text", "Текст активной вкладки"),
        ],
    ),
    (
        "Игра и карта",
        [
            ("map_frame_background", "Фон карты"),
            ("map_frame_border", "Рамка карты"),
            ("status_ok", "Статус «готово»"),
            ("status_pending", "Статус «ожидание»"),
            ("marker_guess", "Метка — ваш ответ"),
            ("marker_correct", "Метка — правильно"),
            ("marker_line", "Линия между метками"),
            ("marker_label", "Подпись метки"),
            ("placeholder", "Заглушка карты"),
        ],
    ),
]

_current = ThemeColors()


def get_colors() -> ThemeColors:
    return _current


def set_colors(colors: ThemeColors) -> None:
    global _current
    _current = colors


def default_colors() -> ThemeColors:
    return ThemeColors()


def load_theme() -> ThemeColors:
    if not THEME_PATH.exists():
        set_colors(default_colors())
        return _current
    try:
        data = json.loads(THEME_PATH.read_text(encoding="utf-8"))
        base = asdict(default_colors())
        base.update({key: value for key, value in data.items() if key in base})
        colors = ThemeColors(**base)
    except (json.JSONDecodeError, TypeError, ValueError):
        colors = default_colors()
    set_colors(colors)
    return colors


def save_theme(colors: ThemeColors | None = None) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = colors or _current
    THEME_PATH.write_text(
        json.dumps(asdict(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    set_colors(payload)


def build_stylesheet(colors: ThemeColors | None = None) -> str:
    c = colors or _current
    return f"""
QWidget {{
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: {c.text};
}}
QMainWindow, QDialog {{
    background: {c.background};
}}
QLabel#TitleLabel {{
    font-size: 28px;
    font-weight: 700;
    color: {c.title};
}}
QLabel#SubtitleLabel {{
    font-size: 16px;
    color: {c.subtitle};
}}
QPushButton {{
    background: {c.button_primary};
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {c.button_primary_hover};
}}
QPushButton:disabled {{
    background: {c.button_disabled};
}}
QPushButton#SecondaryButton {{
    background: {c.button_secondary};
    color: {c.button_secondary_text};
}}
QPushButton#SecondaryButton:hover {{
    background: {c.button_secondary_hover};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {c.input_background};
    border: 1px solid {c.input_border};
    border-radius: 8px;
    padding: 7px;
}}
QGroupBox {{
    border: 1px solid {c.border};
    border-radius: 14px;
    margin-top: 10px;
    padding: 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}}
QTableWidget {{
    background: {c.input_background};
    border: 1px solid {c.border};
    border-radius: 10px;
    gridline-color: {c.table_grid};
}}
QHeaderView::section {{
    background: {c.table_header_background};
    color: {c.table_header_text};
    border: none;
    padding: 6px;
}}
QTabWidget::pane {{
    border: 1px solid {c.border};
    border-radius: 14px;
    background: {c.panel_background};
    top: -1px;
    padding: 8px;
}}
QTabBar::tab {{
    background: {c.tab_background};
    color: {c.tab_text};
    border: 1px solid {c.border};
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 10px 22px;
    margin-right: 4px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background: {c.tab_selected_background};
    color: {c.tab_selected_text};
}}
QWidget#EditorCard {{
    background: {c.card_background};
    border: 1px solid {c.border};
    border-radius: 16px;
}}
QLabel#EditorSectionTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {c.title};
}}
QLabel#EditorStatusOk {{
    color: {c.status_ok};
    font-weight: 600;
}}
QLabel#EditorStatusPending {{
    color: {c.status_pending};
}}
QLabel#EditorPreviewFrame {{
    background: {c.input_background};
    border: 1px solid {c.border};
    border-radius: 14px;
}}
QTableWidget::item:selected {{
    background: {c.table_selected};
    color: {c.text};
}}
QWidget#SettingsPreviewCard {{
    background: {c.card_background};
    border: 1px solid {c.border};
    border-radius: 16px;
}}
QScrollArea#SettingsScroll {{
    border: none;
    background: transparent;
}}
"""


def apply_theme(app: QApplication | None = None, colors: ThemeColors | None = None) -> None:
    stylesheet = build_stylesheet(colors)
    target = app or QApplication.instance()
    if target is not None:
        target.setStyleSheet(stylesheet)


def color_field_names() -> set[str]:
    return {field.name for field in fields(ThemeColors)}

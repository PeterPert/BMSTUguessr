from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QApplication


@dataclass
class ThemeColors:
    background_top: str = "#dff4ff"
    background_bottom: str = "#b9e3ff"
    text: str = "#0f2740"
    title: str = "#0b3b66"
    subtitle: str = "#335f83"
    user_accent: str = "#0d5fa6"
    hint_text: str = "#4d7496"

    button_primary: str = "#1485d1"
    button_primary_hover: str = "#0e70b3"
    button_disabled: str = "#8fc4e7"
    button_secondary: str = "#eef8ff"
    button_secondary_hover: str = "#d9efff"
    button_secondary_text: str = "#0f4a73"

    input_background: str = "rgba(255, 255, 255, 0.95)"
    input_border: str = "#86bde6"

    border: str = "#99c9ee"
    card_background: str = "rgba(255, 255, 255, 0.88)"
    panel_background: str = "rgba(255, 255, 255, 0.84)"
    map_frame_background: str = "rgba(241, 250, 255, 0.97)"
    map_frame_border: str = "#5fa7de"

    table_header_background: str = "#d9efff"
    table_header_text: str = "#0e3d63"
    table_grid: str = "#c7e3f8"
    table_selected: str = "#d6ecfd"

    tab_background: str = "#d8efff"
    tab_text: str = "#0d4d79"
    tab_selected_background: str = "rgba(255, 255, 255, 0.92)"
    tab_selected_text: str = "#0b3b66"

    status_ok: str = "#1c8a52"
    status_pending: str = "#5e7f97"

    marker_guess: str = "#ef4444"
    marker_correct: str = "#22c55e"
    marker_line: str = "#0e70b3"
    marker_label: str = "#0f2740"
    placeholder: str = "#eaf7ff"


_current = ThemeColors()


def get_colors() -> ThemeColors:
    return _current


def set_colors(colors: ThemeColors) -> None:
    global _current
    _current = colors


def default_colors() -> ThemeColors:
    return ThemeColors()


def load_theme() -> ThemeColors:
    set_colors(default_colors())
    return _current


def save_theme(colors: ThemeColors | None = None) -> None:
    set_colors(colors or default_colors())


def build_stylesheet(colors: ThemeColors | None = None) -> str:
    c = colors or _current
    return f"""
QWidget {{
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: {c.text};
}}
QMainWindow, QDialog {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {c.background_top},
        stop:1 {c.background_bottom}
    );
}}
QLabel#TitleLabel {{
    font-size: 30px;
    font-weight: 800;
    color: {c.title};
}}
QLabel#SubtitleLabel {{
    font-size: 15px;
    font-weight: 600;
    color: {c.subtitle};
}}
QPushButton {{
    background: {c.button_primary};
    color: white;
    border: none;
    border-radius: 14px;
    padding: 12px 18px;
    font-weight: 700;
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
    border: 1px solid {c.border};
}}
QPushButton#SecondaryButton:hover {{
    background: {c.button_secondary_hover};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {c.input_background};
    border: 1px solid {c.input_border};
    border-radius: 10px;
    padding: 8px;
}}
QGroupBox {{
    border: 1px solid {c.border};
    border-radius: 14px;
    margin-top: 10px;
    padding: 12px;
    font-weight: 700;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}}
QTableWidget {{
    background: {c.input_background};
    border: 1px solid {c.border};
    border-radius: 12px;
    gridline-color: {c.table_grid};
}}
QHeaderView::section {{
    background: {c.table_header_background};
    color: {c.table_header_text};
    border: none;
    padding: 8px;
    font-weight: 700;
}}
QTabWidget::pane {{
    border: 1px solid {c.border};
    border-radius: 16px;
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
    padding: 10px 18px;
    margin-right: 4px;
    font-weight: 700;
}}
QTabBar::tab:selected {{
    background: {c.tab_selected_background};
    color: {c.tab_selected_text};
}}
QWidget#EditorCard, QWidget#GlassCard, QWidget#ResultCard {{
    background: {c.card_background};
    border: 1px solid {c.border};
    border-radius: 18px;
}}
QLabel#EditorSectionTitle {{
    font-size: 16px;
    font-weight: 800;
    color: {c.title};
}}
QLabel#EditorStatusOk {{
    color: {c.status_ok};
    font-weight: 700;
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
QLabel#GameScoreLabel {{
    font-size: 28px;
    font-weight: 800;
    color: {c.title};
    background: rgba(255, 255, 255, 0.92);
    border: 2px solid {c.button_primary};
    border-radius: 16px;
    padding: 10px 20px;
}}
QLabel#GameRoundPoints {{
    font-size: 21px;
    font-weight: 800;
    color: {c.button_primary};
    background: rgba(255, 255, 255, 0.9);
    border: 2px solid {c.button_primary};
    border-radius: 14px;
    padding: 8px 14px;
}}
QPushButton#GameNextButton {{
    background: {c.button_primary};
    color: white;
    font-size: 16px;
    font-weight: 800;
    border-radius: 14px;
    padding: 14px 20px;
    min-height: 52px;
}}
QPushButton#GameNextButton:hover {{
    background: {c.button_primary_hover};
}}
"""


def apply_theme(
    app: QApplication | None = None, colors: ThemeColors | None = None
) -> None:
    stylesheet = build_stylesheet(colors)
    target = app or QApplication.instance()
    if target is not None:
        target.setStyleSheet(stylesheet)

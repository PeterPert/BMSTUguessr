from __future__ import annotations

from dataclasses import asdict, replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.theme import COLOR_GROUPS, ThemeColors, apply_theme, build_stylesheet, default_colors, get_colors, save_theme
from app.widgets.color_picker_row import ColorPickerRow


class SettingsWindow(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumSize(1080, 760)
        self.resize(1120, 800)
        self.draft = ThemeColors(**asdict(get_colors()))
        self._pickers: dict[str, ColorPickerRow] = {}
        self._build_ui()
        self._refresh_preview()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        title = QLabel("Настройки")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Настройте цвета интерфейса — изменения видны в превью справа.")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_appearance_tab(), "Оформление")
        root.addWidget(self.tabs, 1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        reset_button = QPushButton("Сбросить")
        reset_button.setObjectName("SecondaryButton")
        apply_button = QPushButton("Применить")
        close_button = QPushButton("Закрыть")
        close_button.setObjectName("SecondaryButton")
        reset_button.clicked.connect(self._reset_colors)
        apply_button.clicked.connect(self._apply_colors)
        close_button.clicked.connect(self.accept)
        footer.addWidget(reset_button)
        footer.addWidget(apply_button)
        footer.addWidget(close_button)
        root.addLayout(footer)

    def _build_appearance_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(18)

        scroll = QScrollArea()
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(14)

        for group_title, items in COLOR_GROUPS:
            card = QWidget()
            card.setObjectName("EditorCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            card_layout.setSpacing(10)
            card_layout.addWidget(self._section_title(group_title))

            for field_key, label in items:
                picker = ColorPickerRow(field_key, label, getattr(self.draft, field_key))
                picker.color_changed.connect(self._on_color_changed)
                self._pickers[field_key] = picker
                card_layout.addWidget(picker)

            scroll_layout.addWidget(card)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)

        self.preview_card = QWidget()
        self.preview_card.setObjectName("SettingsPreviewCard")
        preview_layout = QVBoxLayout(self.preview_card)
        preview_layout.setContentsMargins(20, 18, 20, 18)
        preview_layout.setSpacing(12)
        preview_layout.addWidget(self._section_title("Превью"))

        self.preview_title = QLabel("Baumanka GeoGuessr")
        self.preview_title.setObjectName("TitleLabel")
        self.preview_subtitle = QLabel("Пример подзаголовка")
        self.preview_subtitle.setObjectName("SubtitleLabel")

        buttons = QHBoxLayout()
        self.preview_primary = QPushButton("Основная")
        self.preview_secondary = QPushButton("Вторичная")
        self.preview_secondary.setObjectName("SecondaryButton")
        buttons.addWidget(self.preview_primary)
        buttons.addWidget(self.preview_secondary)

        self.preview_input = QLineEdit("Поле ввода")
        self.preview_input.setReadOnly(True)

        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.StyledPanel)
        table_grid = QGridLayout(table_frame)
        table_grid.setContentsMargins(8, 8, 8, 8)
        header_a = QLabel("Колонка A")
        header_b = QLabel("Колонка B")
        header_a.setAlignment(Qt.AlignCenter)
        header_b.setAlignment(Qt.AlignCenter)
        row_a = QLabel("Строка 1")
        row_b = QLabel("Значение")
        table_grid.addWidget(header_a, 0, 0)
        table_grid.addWidget(header_b, 0, 1)
        table_grid.addWidget(row_a, 1, 0)
        table_grid.addWidget(row_b, 1, 1)
        self.preview_table_headers = (header_a, header_b)
        self.preview_table_row = (row_a, row_b)
        self.preview_table_frame = table_frame

        self.preview_markers = QLabel()
        self.preview_markers.setAlignment(Qt.AlignCenter)

        preview_layout.addWidget(self.preview_title)
        preview_layout.addWidget(self.preview_subtitle)
        preview_layout.addLayout(buttons)
        preview_layout.addWidget(self.preview_input)
        preview_layout.addWidget(table_frame)
        preview_layout.addWidget(self.preview_markers)
        preview_layout.addStretch(1)

        layout.addWidget(scroll, 3)
        layout.addWidget(self.preview_card, 2)
        return tab

    @staticmethod
    def _section_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("EditorSectionTitle")
        return label

    def _on_color_changed(self, field_key: str, color: str) -> None:
        self.draft = replace(self.draft, **{field_key: color})
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        c = self.draft
        preview_style = build_stylesheet(c)
        self.preview_card.setStyleSheet(preview_style)
        self.preview_title.setStyleSheet(f"color: {c.title}; font-size: 22px; font-weight: 700;")
        self.preview_subtitle.setStyleSheet(f"color: {c.subtitle}; font-size: 14px;")
        self.preview_primary.setStyleSheet(
            f"background: {c.button_primary}; color: white; border: none; border-radius: 10px; padding: 8px 14px;"
        )
        self.preview_secondary.setStyleSheet(
            f"background: {c.button_secondary}; color: {c.button_secondary_text};"
            f"border: none; border-radius: 10px; padding: 8px 14px;"
        )
        self.preview_input.setStyleSheet(
            f"background: {c.input_background}; border: 1px solid {c.input_border}; border-radius: 8px; padding: 6px;"
        )
        self.preview_table_frame.setStyleSheet(
            f"background: {c.input_background}; border: 1px solid {c.border}; border-radius: 10px;"
        )
        for header in self.preview_table_headers:
            header.setStyleSheet(
                f"background: {c.table_header_background}; color: {c.table_header_text};"
                f"padding: 6px; border-radius: 6px; font-weight: 600;"
            )
        for cell in self.preview_table_row:
            cell.setStyleSheet(f"color: {c.text}; padding: 4px;")
        self.preview_markers.setText(
            f'<span style="color:{c.marker_guess}; font-size:18px; font-weight:bold;">●</span> ваш ответ &nbsp;&nbsp; '
            f'<span style="color:{c.marker_correct}; font-size:18px; font-weight:bold;">●</span> правильно'
        )

    def _reset_colors(self) -> None:
        self.draft = default_colors()
        for field_key, picker in self._pickers.items():
            picker.set_color(getattr(self.draft, field_key))
        self._refresh_preview()

    def _apply_colors(self) -> None:
        save_theme(self.draft)
        apply_theme(colors=self.draft)
        if self.parent() is not None:
            self._restyle_parent(self.parent())
        QMessageBox.information(self, "Оформление", "Цвета сохранены и применены ко всему приложению.")

    def _restyle_parent(self, widget) -> None:
        c = get_colors()
        if hasattr(widget, "user_label"):
            widget.user_label.setStyleSheet(f"font-weight: 700; color: {c.user_accent};")
        if hasattr(widget, "info_label"):
            widget.info_label.setStyleSheet(f"color: {c.hint_text}; font-size: 12px;")

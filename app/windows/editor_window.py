from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import database, paths
from app.theme import get_colors
from app.widgets.logo_header import build_logo_header
from app.windows.map_dialogs import MapPickerDialog, ResultMapDialog


def _editor_card(parent: QWidget | None = None) -> QWidget:
    card = QWidget(parent)
    card.setObjectName("EditorCard")
    return card


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("EditorSectionTitle")
    return label


def _status_label(text: str, ready: bool = False) -> QLabel:
    label = QLabel(text)
    label.setObjectName("EditorStatusOk" if ready else "EditorStatusPending")
    label.setWordWrap(True)
    return label


class EditorWindow(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("BMSTUguessr")
        self.setMinimumSize(1180, 820)
        self.resize(1240, 860)

        # Разрешаем сворачивание/разворачивание
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        # Горячая клавиша F11 для перехода в полноэкранный режим
        from PySide6.QtGui import QKeySequence, QShortcut
        self.fs_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.fs_shortcut.activated.connect(self._toggle_fullscreen)
        self.current_location_id: int | None = None
        self.selected_photo_path: str | None = None
        self.selected_map_path: str | None = None
        self.selected_point: tuple[int, int] | None = None
        self._build_ui()
        self._load_floors()
        self._load_locations()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = build_logo_header(title_size=28, icon_size=56, spacing=6)
        subtitle = QLabel("Панель администратора")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setWordWrap(True)
        header.addWidget(title)
        header.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_floors_tab(), "Этажи")
        self.tabs.addTab(self._build_locations_tab(), "Метки")

        footer = QHBoxLayout()
        footer.addStretch(1)
        close_button = QPushButton("Закрыть")
        close_button.setMinimumWidth(140)
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)

        root.addLayout(header)
        root.addWidget(self.tabs, 1)
        root.addLayout(footer)

    # ---------- Этажи ----------
    def _build_floors_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        card = _editor_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)
        card_layout.addWidget(_section_title("Параметры этажа"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)

        self.floor_number_spin = QSpinBox()
        self.floor_number_spin.setRange(1, 20)
        self.floor_number_spin.setValue(2)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setDecimals(3)
        self.scale_spin.setRange(0.010, 2.000)
        self.scale_spin.setSingleStep(0.010)
        self.scale_spin.setValue(0.100)
        self.map_status_label = _status_label("Схема не выбрана")

        grid.addWidget(QLabel("Номер этажа"), 0, 0)
        grid.addWidget(self.floor_number_spin, 0, 1)
        grid.addWidget(QLabel("Метров на пиксель"), 1, 0)
        grid.addWidget(self.scale_spin, 1, 1)
        grid.addWidget(QLabel("Схема 1100×700"), 2, 0)
        grid.addWidget(self.map_status_label, 2, 1)

        floor_actions = QHBoxLayout()
        floor_actions.setSpacing(10)
        choose_map_button = QPushButton("Выбрать схему")
        choose_map_button.setObjectName("SecondaryButton")
        save_floor_button = QPushButton("Сохранить этаж")
        floor_actions.addWidget(choose_map_button)
        floor_actions.addWidget(save_floor_button)
        floor_actions.addStretch(1)

        card_layout.addLayout(grid)
        card_layout.addLayout(floor_actions)

        self.floors_table = QTableWidget(0, 3)
        self.floors_table.setHorizontalHeaderLabels(["Этаж", "М/пикс", "Файл"])
        self.floors_table.horizontalHeader().setStretchLastSection(True)
        self.floors_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.floors_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.floors_table.setAlternatingRowColors(True)
        self.floors_table.verticalHeader().setVisible(False)
        self.floors_table.setShowGrid(False)

        layout.addWidget(card)
        layout.addWidget(_section_title("Сохранённые этажи"))
        layout.addWidget(self.floors_table, 1)

        choose_map_button.clicked.connect(self._choose_map)
        save_floor_button.clicked.connect(self._save_floor)
        self.floors_table.itemSelectionChanged.connect(self._load_selected_floor_into_form)
        return tab

    def _choose_map(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите схему этажа",
            str(paths.PROJECT_ROOT),
            "Изображения (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not file_path:
            return
        image = QImage(file_path)
        if image.isNull():
            QMessageBox.warning(self, "Схема", "Не получилось открыть изображение.")
            return
        if (image.width(), image.height()) != paths.MAP_SIZE:
            QMessageBox.warning(
                self,
                "Схема",
                "Схема должна быть строго 1100×700. Это защита от плавающих координат.",
            )
            return
        self.selected_map_path = file_path
        self._set_map_status(file_path)

    def _set_map_status(self, path: str) -> None:
        name = Path(path).name
        self.map_status_label.setText(f"✓ {name}")
        self.map_status_label.setObjectName("EditorStatusOk")

    def _save_floor(self) -> None:
        if not self.selected_map_path:
            QMessageBox.warning(self, "Этаж", "Выберите схему этажа.")
            return
        try:
            floor_number = int(self.floor_number_spin.value())
            stored_path = paths.copy_image_to_storage(
                self.selected_map_path,
                paths.MAPS_DIR,
                f"floor_{floor_number}",
            )
            database.upsert_floor(floor_number, stored_path, float(self.scale_spin.value()))
        except Exception as exc:  # noqa: BLE001 - показываем пользователю понятную ошибку
            QMessageBox.critical(self, "Этаж", f"Не удалось сохранить этаж:\n{exc}")
            return
        QMessageBox.information(self, "Этаж", "Этаж сохранён.")
        self._load_floors()

    def _load_floors(self) -> None:
        self.floors = database.get_floors()
        self.floors_table.setRowCount(len(self.floors))
        for row_index, row in enumerate(self.floors):
            self.floors_table.setItem(row_index, 0, QTableWidgetItem(str(row["floor_number"])))
            self.floors_table.setItem(row_index, 1, QTableWidgetItem(f"{row['meters_per_pixel']:.3f}"))
            self.floors_table.setItem(
                row_index, 2, QTableWidgetItem(Path(row["map_path"]).name)
            )
        self.floors_table.resizeColumnsToContents()
        self._refresh_floor_combo()

    def _load_selected_floor_into_form(self) -> None:
        selected = self.floors_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        item = self.floors[row]
        self.floor_number_spin.setValue(int(item["floor_number"]))
        self.scale_spin.setValue(float(item["meters_per_pixel"]))
        self.selected_map_path = str(paths.resolve_path(item["map_path"]))
        self._set_map_status(item["map_path"])

    # ---------- Метки ----------
    def _build_locations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        card = _editor_card()
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(20)

        self.preview_photo = QLabel()
        self.preview_photo.setObjectName("EditorPreviewFrame")
        self.preview_photo.setAlignment(Qt.AlignCenter)
        self.preview_photo.setMinimumSize(300, 280)
        self.preview_photo.setMaximumSize(340, 320)
        self.preview_photo.setText("")

        form_column = QVBoxLayout()
        form_column.setSpacing(12)
        form_column.addWidget(_section_title("Карточка метки"))

        self.title_edit = QLineEdit()
        self.floor_combo = QComboBox()
        self.photo_status_label = _status_label("Фото не выбрано")
        self.point_status_label = _status_label("Точка не поставлена")

        fields = QGridLayout()
        fields.setHorizontalSpacing(12)
        fields.setVerticalSpacing(10)
        fields.setColumnStretch(1, 1)
        fields.addWidget(QLabel("Название"), 0, 0)
        fields.addWidget(self.title_edit, 0, 1)
        fields.addWidget(QLabel("Этаж"), 1, 0)
        fields.addWidget(self.floor_combo, 1, 1)
        fields.addWidget(QLabel("Фото"), 2, 0)
        fields.addWidget(self.photo_status_label, 2, 1)
        fields.addWidget(QLabel("Точка"), 3, 0)
        fields.addWidget(self.point_status_label, 3, 1)
        form_column.addLayout(fields)

        pick_row = QHBoxLayout()
        pick_row.setSpacing(8)
        choose_photo_button = QPushButton("Фото")
        choose_photo_button.setObjectName("SecondaryButton")
        set_point_button = QPushButton("Точка на карте")
        preview_button = QPushButton("Проверить")
        preview_button.setObjectName("SecondaryButton")
        pick_row.addWidget(choose_photo_button)
        pick_row.addWidget(set_point_button)
        pick_row.addWidget(preview_button)
        form_column.addLayout(pick_row)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        save_location_button = QPushButton("Сохранить")
        new_location_button = QPushButton("Новая")
        new_location_button.setObjectName("SecondaryButton")
        delete_location_button = QPushButton("Удалить")
        delete_location_button.setObjectName("SecondaryButton")
        actions.addWidget(save_location_button)
        actions.addWidget(new_location_button)
        actions.addWidget(delete_location_button)
        actions.addStretch(1)
        form_column.addLayout(actions)
        form_column.addStretch(1)

        card_layout.addWidget(self.preview_photo)
        card_layout.addLayout(form_column, 1)

        self.locations_table = QTableWidget(0, 4)
        self.locations_table.setHorizontalHeaderLabels(["ID", "Название", "Этаж", "Точка"])
        self.locations_table.horizontalHeader().setStretchLastSection(True)
        self.locations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.locations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.locations_table.setAlternatingRowColors(True)
        self.locations_table.verticalHeader().setVisible(False)
        self.locations_table.setShowGrid(False)

        layout.addWidget(card)
        layout.addWidget(_section_title("Все метки"))
        layout.addWidget(self.locations_table, 1)

        choose_photo_button.clicked.connect(self._choose_photo)
        set_point_button.clicked.connect(self._set_location_point)
        preview_button.clicked.connect(self._preview_location)
        save_location_button.clicked.connect(self._save_location)
        new_location_button.clicked.connect(self._clear_location_form)
        delete_location_button.clicked.connect(self._delete_selected_location)
        self.locations_table.itemSelectionChanged.connect(self._load_selected_location_into_form)
        return tab

    def _set_photo_status(self, path: str | None) -> None:
        if path:
            self.photo_status_label.setText(f"✓ {Path(path).name}")
            self.photo_status_label.setObjectName("EditorStatusOk")
        else:
            self.photo_status_label.setText("Фото не выбрано")
            self.photo_status_label.setObjectName("EditorStatusPending")

    def _set_point_status(self, point: tuple[int, int] | None) -> None:
        if point:
            self.point_status_label.setText(f"✓ x={point[0]}, y={point[1]}")
            self.point_status_label.setObjectName("EditorStatusOk")
        else:
            self.point_status_label.setText("Точка не поставлена")
            self.point_status_label.setObjectName("EditorStatusPending")

    def _refresh_floor_combo(self) -> None:
        if not hasattr(self, "floor_combo"):
            return
        current = self.floor_combo.currentData()
        self.floor_combo.blockSignals(True)
        self.floor_combo.clear()
        for floor in database.get_floors():
            self.floor_combo.addItem(f"{floor['floor_number']} этаж", int(floor["floor_number"]))
        if current is not None:
            index = self.floor_combo.findData(current)
            if index >= 0:
                self.floor_combo.setCurrentIndex(index)
        self.floor_combo.blockSignals(False)

    def _choose_photo(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фотографию локации",
            str(paths.PROJECT_ROOT),
            "Изображения (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not file_path:
            return
        image = QImage(file_path)
        if image.isNull():
            QMessageBox.warning(self, "Фото", "Не получилось открыть изображение.")
            return
        self.selected_photo_path = file_path
        self._set_photo_status(file_path)
        self._show_photo_preview(file_path)

    def _set_location_point(self) -> None:
        floor_number = self.floor_combo.currentData()
        if floor_number is None:
            QMessageBox.warning(self, "Точка", "Сначала добавьте и выберите этаж.")
            return
        floor = database.get_floor(int(floor_number))
        if floor is None:
            QMessageBox.warning(self, "Точка", "Этаж не найден.")
            return
        existing = self.selected_point
        dialog = MapPickerDialog(paths.resolve_path(floor["map_path"]), self, existing_marker=existing)
        if dialog.exec() == QDialog.Accepted and dialog.selected_point:
            self.selected_point = dialog.selected_point
            self._set_point_status(self.selected_point)

    def _save_location(self) -> None:
        if not self.selected_photo_path:
            QMessageBox.warning(self, "Метка", "Выберите фотографию.")
            return
        if self.floor_combo.currentData() is None:
            QMessageBox.warning(self, "Метка", "Выберите этаж.")
            return
        if self.selected_point is None:
            QMessageBox.warning(self, "Метка", "Поставьте точку на схеме.")
            return
        try:
            stored_photo = paths.copy_image_to_storage(
                self.selected_photo_path,
                paths.PHOTOS_DIR,
                "location",
            )
            self.selected_photo_path = stored_photo
            location_id = database.save_location(
                title=self.title_edit.text(),
                image_path=stored_photo,
                floor=int(self.floor_combo.currentData()),
                answer_x=int(self.selected_point[0]),
                answer_y=int(self.selected_point[1]),
                location_id=self.current_location_id,
            )
            self.current_location_id = location_id
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Метка", f"Не удалось сохранить метку:\n{exc}")
            return
        QMessageBox.information(self, "Метка", "Метка сохранена.")
        self._set_photo_status(self.selected_photo_path)
        self._load_locations()

    def _load_locations(self) -> None:
        self.locations = database.get_locations()
        self.locations_table.setRowCount(len(self.locations))
        for row_index, row in enumerate(self.locations):
            point = f"{row['answer_x']}, {row['answer_y']}"
            values = [
                row["id"],
                row["title"] or "Без названия",
                row["floor"],
                point,
            ]
            for column, value in enumerate(values):
                self.locations_table.setItem(row_index, column, QTableWidgetItem(str(value)))
        self.locations_table.resizeColumnsToContents()

    def _load_selected_location_into_form(self) -> None:
        selected = self.locations_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        item = self.locations[row]
        self.current_location_id = int(item["id"])
        self.title_edit.setText(item["title"] or "")
        self.selected_photo_path = item["image_path"]
        self._set_photo_status(item["image_path"])
        index = self.floor_combo.findData(int(item["floor"]))
        if index >= 0:
            self.floor_combo.setCurrentIndex(index)
        self.selected_point = (int(item["answer_x"]), int(item["answer_y"]))
        self._set_point_status(self.selected_point)
        self._show_photo_preview(paths.resolve_path(item["image_path"]))

    def _clear_location_form(self) -> None:
        self.current_location_id = None
        self.selected_photo_path = None
        self.selected_point = None
        self.title_edit.clear()
        self._set_photo_status(None)
        self._set_point_status(None)
        self.preview_photo.setText("")
        self.preview_photo.setPixmap(QPixmap())
        self.locations_table.clearSelection()

    def _delete_selected_location(self) -> None:
        if self.current_location_id is None:
            QMessageBox.warning(self, "Удаление", "Выберите метку в таблице.")
            return
        answer = QMessageBox.question(
            self,
            "Удаление",
            "Удалить выбранную метку?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        database.delete_location(self.current_location_id)
        self._clear_location_form()
        self._load_locations()

    def _preview_location(self) -> None:
        if not self.selected_photo_path or self.floor_combo.currentData() is None or self.selected_point is None:
            QMessageBox.warning(self, "Проверка", "Нужно выбрать фото, этаж и точку.")
            return
        floor = database.get_floor(int(self.floor_combo.currentData()))
        if floor is None:
            QMessageBox.warning(self, "Проверка", "Этаж не найден.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Проверка метки")
        dialog.setMinimumSize(920, 640)
        layout = QHBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        photo = QLabel()
        photo.setObjectName("EditorPreviewFrame")
        photo.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(str(paths.resolve_path(self.selected_photo_path)))
        if not pixmap.isNull():
            photo.setPixmap(pixmap.scaled(440, 540, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            photo.setText("Фото не открылось")

        info_card = _editor_card()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)
        info_layout.addWidget(_section_title("Как в игре"))
        title = self.title_edit.text().strip() or "Без названия"
        info_layout.addWidget(QLabel(f"<b>{title}</b>"))
        info_layout.addWidget(QLabel(f"Этаж: {self.floor_combo.currentData()}"))
        info_layout.addWidget(
            QLabel(f"Точка: x={self.selected_point[0]}, y={self.selected_point[1]}")
        )
        map_button = QPushButton("Карта с ответом")
        map_button.clicked.connect(
            lambda: ResultMapDialog(
                paths.resolve_path(floor["map_path"]),
                [(self.selected_point[0], self.selected_point[1], get_colors().marker_correct, "")],
                [],
                dialog,
            ).exec()
        )
        info_layout.addWidget(map_button)
        info_layout.addStretch(1)

        layout.addWidget(photo, 2)
        layout.addWidget(info_card, 1)
        dialog.exec()

    def _show_photo_preview(self, path: str | Path) -> None:
        pixmap = QPixmap(str(paths.resolve_path(path)))
        if pixmap.isNull():
            self.preview_photo.setText("Фото не открылось")
            self.preview_photo.setPixmap(QPixmap())
            return
        self.preview_photo.setText("")
        frame = self.preview_photo.size()
        target_w = max(260, frame.width() - 16)
        target_h = max(240, frame.height() - 16)
        self.preview_photo.setPixmap(
            pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

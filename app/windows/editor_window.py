from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import database, paths
from app.windows.map_dialogs import MapPickerDialog, ResultMapDialog


class EditorWindow(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редактор карт и меток")
        self.setMinimumSize(1050, 720)
        self.current_location_id: int | None = None
        self.selected_photo_path: str | None = None
        self.selected_map_path: str | None = None
        self.selected_point: tuple[int, int] | None = None
        self._build_ui()
        self._load_floors()
        self._load_locations()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("Редактор")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Добавляйте этажи, фотографии и правильные точки без SQL-заклинаний.")
        subtitle.setObjectName("SubtitleLabel")

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_floors_tab(), "Этажи")
        self.tabs.addTab(self._build_locations_tab(), "Метки")

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self.tabs, 1)
        root.addWidget(close_button)

    # ---------- Этажи ----------
    def _build_floors_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)

        form_group = QGroupBox("Добавить или изменить этаж")
        form = QFormLayout(form_group)
        self.floor_number_spin = QSpinBox()
        self.floor_number_spin.setRange(1, 20)
        self.floor_number_spin.setValue(2)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setDecimals(3)
        self.scale_spin.setRange(0.010, 2.000)
        self.scale_spin.setSingleStep(0.010)
        self.scale_spin.setValue(0.100)
        self.map_label = QLabel("Схема не выбрана")
        self.map_label.setWordWrap(True)
        choose_map_button = QPushButton("Выбрать схему 1100×700")
        save_floor_button = QPushButton("Сохранить этаж")
        save_floor_button.setObjectName("SecondaryButton")

        form.addRow("Номер этажа:", self.floor_number_spin)
        form.addRow("Метров на пиксель:", self.scale_spin)
        form.addRow("Файл схемы:", self.map_label)
        form.addRow(choose_map_button)
        form.addRow(save_floor_button)

        self.floors_table = QTableWidget(0, 3)
        self.floors_table.setHorizontalHeaderLabels(["Этаж", "М/пикс", "Схема"])
        self.floors_table.horizontalHeader().setStretchLastSection(True)
        self.floors_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.floors_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(form_group, 0)
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
        self.map_label.setText(file_path)

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
            self.floors_table.setItem(row_index, 2, QTableWidgetItem(row["map_path"]))
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
        self.map_label.setText(item["map_path"])

    # ---------- Метки ----------
    def _build_locations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        form_group = QGroupBox("Карточка метки")
        form = QFormLayout(form_group)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Например: переход у столовой")
        self.photo_label = QLabel("Фото не выбрано")
        self.photo_label.setWordWrap(True)
        self.floor_combo = QComboBox()
        self.point_label = QLabel("Точка не поставлена")

        choose_photo_button = QPushButton("Выбрать фотографию")
        choose_photo_button.setObjectName("SecondaryButton")
        set_point_button = QPushButton("Поставить точку на схеме")
        preview_button = QPushButton("Проверить как раунд")
        preview_button.setObjectName("SecondaryButton")
        save_location_button = QPushButton("Сохранить метку")
        new_location_button = QPushButton("Новая метка")
        delete_location_button = QPushButton("Удалить выбранную")
        delete_location_button.setObjectName("SecondaryButton")

        form.addRow("Название:", self.title_edit)
        form.addRow("Фото:", self.photo_label)
        form.addRow(choose_photo_button)
        form.addRow("Этаж:", self.floor_combo)
        form.addRow("Координаты:", self.point_label)
        form.addRow(set_point_button)
        form.addRow(preview_button)

        buttons = QHBoxLayout()
        buttons.addWidget(save_location_button)
        buttons.addWidget(new_location_button)
        buttons.addWidget(delete_location_button)

        self.preview_photo = QLabel("Предпросмотр фото")
        self.preview_photo.setAlignment(Qt.AlignCenter)
        self.preview_photo.setMinimumHeight(220)
        self.preview_photo.setStyleSheet("background: white; border: 1px solid #e3c2ca; border-radius: 12px;")

        left_layout.addWidget(form_group)
        left_layout.addLayout(buttons)
        left_layout.addWidget(self.preview_photo, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.locations_table = QTableWidget(0, 6)
        self.locations_table.setHorizontalHeaderLabels(["ID", "Название", "Этаж", "X", "Y", "Фото"])
        self.locations_table.horizontalHeader().setStretchLastSection(True)
        self.locations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.locations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.locations_table)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([420, 620])
        layout.addWidget(splitter)

        choose_photo_button.clicked.connect(self._choose_photo)
        set_point_button.clicked.connect(self._set_location_point)
        preview_button.clicked.connect(self._preview_location)
        save_location_button.clicked.connect(self._save_location)
        new_location_button.clicked.connect(self._clear_location_form)
        delete_location_button.clicked.connect(self._delete_selected_location)
        self.locations_table.itemSelectionChanged.connect(self._load_selected_location_into_form)
        return tab

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
        self.photo_label.setText(file_path)
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
            self.point_label.setText(f"x={self.selected_point[0]}, y={self.selected_point[1]}")

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
        self._load_locations()

    def _load_locations(self) -> None:
        self.locations = database.get_locations()
        self.locations_table.setRowCount(len(self.locations))
        for row_index, row in enumerate(self.locations):
            values = [
                row["id"],
                row["title"] or "Без названия",
                row["floor"],
                row["answer_x"],
                row["answer_y"],
                row["image_path"],
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
        self.photo_label.setText(item["image_path"])
        index = self.floor_combo.findData(int(item["floor"]))
        if index >= 0:
            self.floor_combo.setCurrentIndex(index)
        self.selected_point = (int(item["answer_x"]), int(item["answer_y"]))
        self.point_label.setText(f"x={self.selected_point[0]}, y={self.selected_point[1]}")
        self._show_photo_preview(paths.resolve_path(item["image_path"]))

    def _clear_location_form(self) -> None:
        self.current_location_id = None
        self.selected_photo_path = None
        self.selected_point = None
        self.title_edit.clear()
        self.photo_label.setText("Фото не выбрано")
        self.point_label.setText("Точка не поставлена")
        self.preview_photo.setText("Предпросмотр фото")
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
        dialog.setWindowTitle("Проверка метки как раунда")
        dialog.setMinimumSize(900, 620)
        layout = QHBoxLayout(dialog)
        photo = QLabel()
        photo.setAlignment(Qt.AlignCenter)
        photo.setStyleSheet("background: white; border: 1px solid #e3c2ca; border-radius: 12px;")
        pixmap = QPixmap(str(paths.resolve_path(self.selected_photo_path)))
        if not pixmap.isNull():
            photo.setPixmap(pixmap.scaled(420, 520, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            photo.setText("Фото не открылось")
        map_button = QPushButton("Открыть карту с правильной точкой")
        map_button.clicked.connect(lambda: ResultMapDialog(
            paths.resolve_path(floor["map_path"]),
            [(self.selected_point[0], self.selected_point[1], "#dd3344", "ответ")],
            [],
            dialog,
        ).exec())
        right = QVBoxLayout()
        right.addWidget(QLabel(f"Этаж: {self.floor_combo.currentData()}"))
        right.addWidget(QLabel(f"Координаты: x={self.selected_point[0]}, y={self.selected_point[1]}"))
        right.addWidget(map_button)
        right.addStretch(1)
        layout.addWidget(photo, 1)
        layout.addLayout(right)
        dialog.exec()

    def _show_photo_preview(self, path: str | Path) -> None:
        pixmap = QPixmap(str(paths.resolve_path(path)))
        if pixmap.isNull():
            self.preview_photo.setText("Фото не открылось")
            self.preview_photo.setPixmap(QPixmap())
            return
        self.preview_photo.setText("")
        self.preview_photo.setPixmap(
            pixmap.scaled(380, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

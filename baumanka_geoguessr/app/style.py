APP_STYLE = """
QWidget {
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: #3b2630;
}
QMainWindow, QDialog {
    background: #fff7ef;
}
QLabel#TitleLabel {
    font-size: 28px;
    font-weight: 700;
    color: #9b3754;
}
QLabel#SubtitleLabel {
    font-size: 16px;
    color: #7a5962;
}
QPushButton {
    background: #c95b78;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background: #b84a68;
}
QPushButton:disabled {
    background: #d8b8c0;
}
QPushButton#SecondaryButton {
    background: #e9c79c;
    color: #5a3d23;
}
QPushButton#SecondaryButton:hover {
    background: #ddb77f;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: white;
    border: 1px solid #d6aab4;
    border-radius: 8px;
    padding: 7px;
}
QGroupBox {
    border: 1px solid #e3c2ca;
    border-radius: 14px;
    margin-top: 10px;
    padding: 12px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}
QTableWidget {
    background: white;
    border: 1px solid #e3c2ca;
    border-radius: 10px;
    gridline-color: #ead6dc;
}
QHeaderView::section {
    background: #f4d4de;
    color: #633141;
    border: none;
    padding: 6px;
}
QTabWidget::pane {
    border: 1px solid #e3c2ca;
    border-radius: 14px;
    background: #fffaf5;
    top: -1px;
    padding: 8px;
}
QTabBar::tab {
    background: #f4d4de;
    color: #633141;
    border: 1px solid #e3c2ca;
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 10px 22px;
    margin-right: 4px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #fffaf5;
    color: #9b3754;
}
QWidget#EditorCard {
    background: #fff0f4;
    border: 1px solid #e3c2ca;
    border-radius: 16px;
}
QLabel#EditorSectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: #9b3754;
}
QLabel#EditorStatusOk {
    color: #2d7a52;
    font-weight: 600;
}
QLabel#EditorStatusPending {
    color: #7a5962;
}
QLabel#EditorPreviewFrame {
    background: white;
    border: 1px solid #e3c2ca;
    border-radius: 14px;
}
QTableWidget::item:selected {
    background: #f4d4de;
    color: #3b2630;
}
"""

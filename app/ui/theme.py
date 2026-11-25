from __future__ import annotations

PRIMARY = "#70B2AF"
PRIMARY_DARK = "#5E9C99"
SECONDARY = "#D2F6E7"
LOW_STOCK = "#FF8080"
TEXT = "#263238"
MUTED = "#607D8B"
BORDER = "#B7CFC8"


def build_stylesheet() -> str:
    return f"""
    QWidget {{
        font-family: "Calibri";
        font-size: 11pt;
        color: {TEXT};
    }}
    QMainWindow, QWidget#pageRoot {{
        background-color: #FFFFFF;
    }}
    QLabel {{
        background-color: transparent;
    }}
    QFrame#header {{
        background-color: {SECONDARY};
        border: none;
    }}
    QLabel#brandTitle {{
        font-size: 19pt;
        font-weight: 700;
        color: #2F4F4F;
    }}
    QLabel#pageTitle {{
        font-size: 17pt;
        font-weight: 600;
        color: #2F4F4F;
    }}
    QLabel#sectionTitle {{
        font-size: 13pt;
        font-weight: 600;
        color: #2F4F4F;
    }}
    QLabel#priceLabel {{
        font-size: 17pt;
        font-weight: 700;
        color: #1F3B3A;
    }}
    QLabel#totalLabel {{
        font-size: 15pt;
        font-weight: 700;
        color: #1F3B3A;
    }}
    QLabel#mutedLabel {{
        color: {MUTED};
    }}
    QLabel#errorLabel {{
        color: #B71C1C;
        font-weight: 600;
    }}
    QLabel#discountLabel {{
        color: #C62828;
        font-weight: 600;
    }}
    QPushButton {{
        background-color: {PRIMARY};
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 7px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_DARK};
    }}
    QPushButton:pressed {{
        background-color: #4F8885;
    }}
    QPushButton:disabled {{
        background-color: #C7D8D4;
        color: #7A8B87;
    }}
    QPushButton#secondaryButton {{
        background-color: #FFFFFF;
        color: #2F4F4F;
        border: 1px solid {PRIMARY};
    }}
    QPushButton#secondaryButton:hover {{
        background-color: {SECONDARY};
    }}
    QPushButton#dangerButton {{
        background-color: #E57373;
        color: #FFFFFF;
    }}
    QPushButton#dangerButton:hover {{
        background-color: #D65C5C;
    }}
    QPushButton#linkButton {{
        background-color: transparent;
        color: #2F4F4F;
        border: none;
        text-decoration: underline;
        padding: 4px 6px;
    }}
    QPushButton#linkButton:hover {{
        color: {PRIMARY_DARK};
    }}
    QLineEdit, QComboBox, QSpinBox, QDateTimeEdit, QTextEdit {{
        background-color: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 5px 8px;
        selection-background-color: {PRIMARY};
        selection-color: #FFFFFF;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateTimeEdit:focus, QTextEdit:focus {{
        border: 1px solid {PRIMARY};
    }}
    QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDateTimeEdit:disabled {{
        background-color: #F2F5F4;
        color: #8A9A96;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #FFFFFF;
        border: 1px solid {BORDER};
        selection-background-color: {SECONDARY};
        selection-color: {TEXT};
        outline: none;
    }}
    QTableWidget {{
        background-color: #FFFFFF;
        border: 1px solid #D5E3DF;
        border-radius: 6px;
        gridline-color: #E0EAE7;
        alternate-background-color: #F6FBF9;
        selection-background-color: {SECONDARY};
        selection-color: {TEXT};
    }}
    QTableWidget::item {{
        padding: 4px 6px;
    }}
    QListWidget {{
        background-color: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 5px 8px;
    }}
    QListWidget::item:selected {{
        background-color: {SECONDARY};
        color: {TEXT};
    }}
    QHeaderView::section {{
        background-color: {SECONDARY};
        color: #2F4F4F;
        border: none;
        border-right: 1px solid #C5E2D8;
        border-bottom: 1px solid #C5E2D8;
        padding: 6px;
        font-weight: 600;
    }}
    QScrollArea {{
        border: none;
        background-color: #FFFFFF;
    }}
    QScrollBar:vertical {{
        background: #F2F7F5;
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: #B7CFC8;
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QFrame#card {{
        background-color: #F7FCFA;
        border: 1px solid #D5E3DF;
        border-radius: 8px;
    }}
    QFrame#productRow {{
        background-color: #FFFFFF;
        border: 1px solid #D5E3DF;
        border-radius: 8px;
    }}
    QFrame#productRow:hover {{
        border: 1px solid {PRIMARY};
    }}
    QFrame#productRowLow {{
        background-color: {LOW_STOCK};
        border: 1px solid #E57373;
        border-radius: 8px;
    }}
    QFrame#productRowLow QLabel {{
        background-color: transparent;
    }}
    QGroupBox {{
        font-weight: 600;
        border: 1px solid #D5E3DF;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 8px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
    }}
    QMessageBox {{
        background-color: #FFFFFF;
    }}
    QToolTip {{
        background-color: #2F4F4F;
        color: #FFFFFF;
        border: none;
        padding: 4px 8px;
    }}
    """

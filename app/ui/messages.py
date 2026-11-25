from __future__ import annotations
from PySide6.QtWidgets import QMessageBox, QWidget

def _show(parent: QWidget | None, icon: QMessageBox.Icon, title: str, text: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.button(QMessageBox.StandardButton.Ok).setText("Понятно")
    box.exec()


def show_info(parent: QWidget | None, title: str, text: str) -> None:
    _show(parent, QMessageBox.Icon.Information, title, text)


def show_warning(parent: QWidget | None, title: str, text: str) -> None:
    _show(parent, QMessageBox.Icon.Warning, title, text)


def show_error(parent: QWidget | None, title: str, text: str) -> None:
    _show(parent, QMessageBox.Icon.Critical, title, text)


def ask_confirmation(parent: QWidget | None, title: str, text: str) -> bool:
    """Предупреждение перед необратимой операцией."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    box.button(QMessageBox.StandardButton.Yes).setText("Да")
    box.button(QMessageBox.StandardButton.No).setText("Отмена")
    box.setDefaultButton(QMessageBox.StandardButton.No)
    return box.exec() == QMessageBox.StandardButton.Yes

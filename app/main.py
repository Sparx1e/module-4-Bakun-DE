"""Точка входа приложения «ФормаДесерт»."""

from __future__ import annotations

import sys
import traceback

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import APP_NAME, ICON_PATH
from app.db.connection import Database
from app.config import DbSettings
from app.errors import AppError
from app.ui.main_window import MainWindow
from app.ui.theme import build_stylesheet


def _install_exception_hook() -> None:
    """Не даёт необработанному исключению аварийно закрыть приложение."""

    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        QMessageBox.critical(
            None,
            "Непредвиденная ошибка",
            "Операция не выполнена, но приложение продолжает работу.\n\n"
            "Повторите действие. Если ошибка повторяется, проверьте подключение "
            "к базе данных и журнал приложения.\n\n"
            f"Техническая информация: {exc_value}",
        )

    sys.excepthook = handle_exception


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    app.setFont(QFont("Calibri", 11))
    app.setStyleSheet(build_stylesheet())
    _install_exception_hook()

    database = Database(DbSettings.from_env())
    try:
        database.connect()
        window = MainWindow(database)
    except AppError as exc:
        QMessageBox.critical(None, exc.title, str(exc))
        database.close()
        return 1

    window.show()
    exit_code = app.exec()
    database.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

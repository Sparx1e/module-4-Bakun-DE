"""Верхняя строка приложения с логотипом, заголовком и сведениями о пользователе."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from app.config import LOGO_PATH
from app.models.entities import User


class HeaderBar(QFrame):
    """Единая шапка: логотип слева, заголовок страницы, ФИО и действие справа."""

    logout_requested = Signal()
    login_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("header")
        self.setFixedHeight(78)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(16)

        logo = QLabel()
        logo.setFixedSize(190, 52)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(LOGO_PATH))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    190,
                    52,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo.setText("ФормаДесерт")
        layout.addWidget(logo)

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")
        layout.addWidget(self._title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)

        self._user_label = QLabel()
        self._user_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._user_label)

        self._action_button = QPushButton()
        self._action_button.setObjectName("secondaryButton")
        self._action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_button.clicked.connect(self._on_action_clicked)
        layout.addWidget(self._action_button)

        self._action_mode = "hidden"
        self.show_login_state()

    def set_page_title(self, title: str) -> None:
        self._title_label.setText(title)

    def show_login_state(self) -> None:
        """Шапка страницы входа: без пользователя и кнопки действия."""
        self._user_label.setText("")
        self._action_button.hide()
        self._action_mode = "hidden"

    def show_guest_state(self) -> None:
        """Гостевой режим: виден вход, фильтры каталога отключены."""
        self._user_label.setText("Гость")
        self._action_button.setText("Войти")
        self._action_button.show()
        self._action_mode = "login"

    def show_user(self, user: User) -> None:
        self._user_label.setText(f"{user.full_name} · {user.role_name}")
        self._action_button.setText("Выход")
        self._action_button.show()
        self._action_mode = "logout"

    def _on_action_clicked(self) -> None:
        if self._action_mode == "login":
            self.login_requested.emit()
        elif self._action_mode == "logout":
            self.logout_requested.emit()

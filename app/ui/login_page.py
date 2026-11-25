"""Страница входа по логину без пароля."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.messages import show_warning


class LoginPage(QWidget):
    """Вход в систему: только логин из списка пользователей."""

    login_submitted = Signal(str)
    guest_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageRoot")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addStretch(1)

        card = QFrame()
        card.setObjectName("card")
        card.setMaximumWidth(520)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 32, 36, 32)
        card_layout.setSpacing(12)

        title = QLabel("Вход в систему")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel(
            "Введите логин пользователя «ФормаДесерт». Пароль не требуется."
        )
        subtitle.setObjectName("mutedLabel")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(8)

        self._login_edit = QLineEdit()
        self._login_edit.setPlaceholderText("Логин, например admin или client1")
        self._login_edit.setClearButtonEnabled(True)
        self._login_edit.returnPressed.connect(self._submit)
        card_layout.addWidget(self._login_edit)

        login_button = QPushButton("Войти")
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.clicked.connect(self._submit)
        card_layout.addWidget(login_button)

        guest_button = QPushButton("Продолжить как гость")
        guest_button.setObjectName("secondaryButton")
        guest_button.setCursor(Qt.CursorShape.PointingHandCursor)
        guest_button.clicked.connect(self.guest_requested.emit)
        card_layout.addWidget(guest_button)

        hint = QLabel(
            "Гостю доступен просмотр каталога без поиска, фильтрации и сортировки. "
            "Оформление заказа доступно после входа."
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(hint)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)

    def reset(self) -> None:
        self._login_edit.clear()
        self._login_edit.setFocus()

    def _submit(self) -> None:
        login = self._login_edit.text().strip()
        if not login:
            show_warning(
                self,
                "Ошибка входа",
                "Поле логина не заполнено. Введите логин пользователя, "
                "например admin, manager или client1, и повторите вход.",
            )
            self._login_edit.setFocus()
            return
        self.login_submitted.emit(login)

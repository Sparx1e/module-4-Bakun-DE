"""Страница просмотра состава выбранного заказа."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import OrderDetail, User
from app.ui.formatting import format_date_time, format_money


class OrderDetailPage(QWidget):
    """Шапка заказа, строки состава и итоговая сумма."""

    back_requested = Signal()
    edit_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._order_id: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        back_button = QPushButton("← Назад к списку заказов")
        back_button.setObjectName("secondaryButton")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        top.addWidget(back_button)
        top.addStretch(1)
        self._edit_button = QPushButton("Изменить заказ")
        self._edit_button.setObjectName("secondaryButton")
        self._edit_button.clicked.connect(self._edit)
        top.addWidget(self._edit_button)
        layout.addLayout(top)

        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 14, 20, 14)
        header_layout.setSpacing(4)

        self._number_label = QLabel()
        self._number_label.setStyleSheet("font-size: 15pt; font-weight: 700;")
        header_layout.addWidget(self._number_label)
        self._date_label = QLabel()
        header_layout.addWidget(self._date_label)
        self._client_label = QLabel()
        header_layout.addWidget(self._client_label)
        layout.addWidget(header_card)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["Модель", "Производство", "Вариант", "Кол-во", "Цена", "Сумма"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in (1, 2, 3, 4, 5):
            self._table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        layout.addWidget(self._table, 1)

        total_row = QHBoxLayout()
        total_row.addStretch(1)
        self._total_label = QLabel()
        self._total_label.setObjectName("totalLabel")
        total_row.addWidget(self._total_label)
        layout.addLayout(total_row)

    def load_order(self, order: OrderDetail, user: User) -> None:
        self._order_id = order.order_id
        self._number_label.setText(f"Заказ №{order.order_id}")
        self._date_label.setText(f"Дата заказа: {format_date_time(order.order_date)}")
        self._client_label.setText(f"Клиент: {order.client_name}")
        self._edit_button.setVisible(user.is_admin)

        self._table.setRowCount(0)
        for item in order.items:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(item.product_name))
            self._table.setItem(row, 1, QTableWidgetItem(item.manufacturer))
            self._table.setItem(row, 2, QTableWidgetItem(item.variant_name))
            self._table.setItem(row, 3, QTableWidgetItem(f"{item.quantity} шт."))
            self._table.setItem(row, 4, QTableWidgetItem(format_money(item.unit_price)))
            self._table.setItem(row, 5, QTableWidgetItem(format_money(item.line_total)))
            self._table.setRowHeight(row, 34)

        self._total_label.setText(f"Итого по заказу: {format_money(order.total)}")

    def _edit(self) -> None:
        if self._order_id is not None:
            self.edit_requested.emit(self._order_id)

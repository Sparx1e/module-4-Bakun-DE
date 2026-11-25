"""Редактирование заказа администратором: дата и удаление позиций."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateTimeEdit,
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

from app.models.entities import OrderDetail
from app.ui.formatting import format_date_time, format_money
from app.ui.messages import ask_confirmation, show_warning


class OrderEditPage(QWidget):
    """Форма администратора: изменить дату и удалить отдельные позиции."""

    save_requested = Signal(int, object, object)  # order_id, datetime, list[int]
    cancel_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._order: OrderDetail | None = None
        self._pending_delete: set[int] = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        cancel_top = QPushButton("← Назад к заказам")
        cancel_top.setObjectName("secondaryButton")
        cancel_top.clicked.connect(self._cancel)
        top.addWidget(cancel_top)
        top.addStretch(1)
        layout.addLayout(top)

        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 14, 20, 14)
        header_layout.setSpacing(6)

        self._number_label = QLabel()
        self._number_label.setStyleSheet("font-size: 15pt; font-weight: 700;")
        header_layout.addWidget(self._number_label)
        self._client_label = QLabel()
        header_layout.addWidget(self._client_label)

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Дата заказа:"))
        self._date_edit = QDateTimeEdit()
        self._date_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self._date_edit.setCalendarPopup(True)
        date_row.addWidget(self._date_edit)
        date_row.addStretch(1)
        header_layout.addLayout(date_row)
        layout.addWidget(header_card)

        hint = QLabel(
            "Удалённые позиции исчезнут из заказа после нажатия «Сохранить». "
            "Их количество будет возвращено на склад."
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["Модель", "Производство", "Вариант", "Кол-во", "Цена", "Сумма"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in (1, 2, 3, 4, 5):
            self._table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        layout.addWidget(self._table, 1)

        bottom = QHBoxLayout()
        self._delete_button = QPushButton("Удалить выбранную позицию")
        self._delete_button.setObjectName("dangerButton")
        self._delete_button.clicked.connect(self._delete_selected)
        bottom.addWidget(self._delete_button)
        bottom.addStretch(1)
        self._total_label = QLabel()
        self._total_label.setObjectName("totalLabel")
        bottom.addWidget(self._total_label)
        layout.addLayout(bottom)

        actions = QHBoxLayout()
        actions.addStretch(1)
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self._save)
        actions.addWidget(save_button)
        cancel_button = QPushButton("Отмена")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self._cancel)
        actions.addWidget(cancel_button)
        layout.addLayout(actions)

    def load_order(self, order: OrderDetail) -> None:
        self._order = order
        self._pending_delete.clear()
        self._number_label.setText(f"Редактирование заказа №{order.order_id}")
        self._client_label.setText(f"Клиент: {order.client_name}")
        date_value = QDateTime.fromString(
            order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "yyyy-MM-dd HH:mm:ss",
        )
        self._date_edit.setDateTime(date_value)
        self._refresh_table()

    def _refresh_table(self) -> None:
        self._table.setRowCount(0)
        total = Decimal("0.00")
        if self._order is not None:
            for item in self._order.items:
                if item.order_item_id in self._pending_delete:
                    continue
                row = self._table.rowCount()
                self._table.insertRow(row)
                id_item = QTableWidgetItem(item.product_name)
                id_item.setData(Qt.ItemDataRole.UserRole, item.order_item_id)
                self._table.setItem(row, 0, id_item)
                self._table.setItem(row, 1, QTableWidgetItem(item.manufacturer))
                self._table.setItem(row, 2, QTableWidgetItem(item.variant_name))
                self._table.setItem(row, 3, QTableWidgetItem(f"{item.quantity} шт."))
                self._table.setItem(row, 4, QTableWidgetItem(format_money(item.unit_price)))
                self._table.setItem(row, 5, QTableWidgetItem(format_money(item.line_total)))
                self._table.setRowHeight(row, 32)
                total += item.line_total

        self._total_label.setText(f"Итого после сохранения: {format_money(total)}")
        self._delete_button.setEnabled(self._table.rowCount() > 0)

    def _delete_selected(self) -> None:
        selected = self._table.selectionModel().selectedRows()
        if not selected:
            show_warning(
                self,
                "Позиция не выбрана",
                "Выберите строку состава заказа, которую нужно удалить.",
            )
            return
        item = self._table.item(selected[0].row(), 0)
        if item is None:
            return
        self._pending_delete.add(item.data(Qt.ItemDataRole.UserRole))
        self._refresh_table()

    def _save(self) -> None:
        if self._order is None:
            return
        remaining = len(self._order.items) - len(self._pending_delete)
        if remaining == 0 and not ask_confirmation(
            self,
            "Пустой заказ",
            "После сохранения в заказе не останется ни одной позиции. "
            "Сохранить пустой заказ?",
        ):
            return
        self.save_requested.emit(
            self._order.order_id,
            self._date_edit.dateTime().toPython(),
            list(self._pending_delete),
        )

    def _cancel(self) -> None:
        if self._pending_delete and not ask_confirmation(
            self,
            "Отмена редактирования",
            "Отменить изменения заказа? Удалённые позиции будут восстановлены в форме.",
        ):
            return
        self.cancel_requested.emit()

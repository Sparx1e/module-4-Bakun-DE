from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from app.models.entities import OrderSummary, User
from app.ui.formatting import format_date_time, format_money
from app.ui.messages import ask_confirmation, show_warning

class OrdersPage(QWidget):
    """Общий список заказов с доступом по ролям."""

    open_requested = Signal(int)
    add_requested = Signal()
    delete_requested = Signal(int)
    edit_requested = Signal(int)
    back_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._orders: list[OrderSummary] = []
        self._user: User | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        back_button = QPushButton("<-- Назад в каталог")
        back_button.setObjectName("secondaryButton")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        top.addWidget(back_button)
        top.addStretch(1)
        layout.addLayout(top)

        self._empty_label = QLabel(
            "Заказы отсутствуют. Нажмите «Добавить», чтобы оформить первый заказ."
        )
        self._empty_label.setObjectName("mutedLabel")
        layout.addWidget(self._empty_label)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["№", "Дата заказа", "Клиент", "Сумма"])
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        for column in (0, 1, 3):
            self._table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self._table.itemSelectionChanged.connect(self._update_buttons)
        self._table.doubleClicked.connect(self._open_selected)
        layout.addWidget(self._table, 1)

        buttons = QHBoxLayout()
        self._open_button = QPushButton("Открыть")
        self._open_button.clicked.connect(self._open_selected)
        buttons.addWidget(self._open_button)

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_requested.emit)
        buttons.addWidget(add_button)

        self._delete_button = QPushButton("Удалить")
        self._delete_button.setObjectName("dangerButton")
        self._delete_button.clicked.connect(self._delete_selected)
        buttons.addWidget(self._delete_button)

        self._edit_button = QPushButton("Изменить")
        self._edit_button.setObjectName("secondaryButton")
        self._edit_button.clicked.connect(self._edit_selected)
        buttons.addWidget(self._edit_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self._update_buttons()

    def load_orders(self, orders: list[OrderSummary], user: User) -> None:
        self._user = user
        self._orders = orders
        self._table.setRowCount(0)
        for order in orders:
            row = self._table.rowCount()
            self._table.insertRow(row)
            id_item = QTableWidgetItem(str(order.order_id))
            id_item.setData(Qt.ItemDataRole.UserRole, order.order_id)
            self._table.setItem(row, 0, id_item)
            self._table.setItem(row, 1, QTableWidgetItem(format_date_time(order.order_date)))
            self._table.setItem(row, 2, QTableWidgetItem(order.client_name))
            self._table.setItem(row, 3, QTableWidgetItem(format_money(order.total)))
            self._table.setRowHeight(row, 34)

        self._empty_label.setVisible(not orders)
        self._table.setVisible(bool(orders))
        self._edit_button.setVisible(user.is_admin)

        if orders:
            self._table.selectRow(0)
        self._update_buttons()

    def _selected_order_id(self) -> int | None:
        selected = self._table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self._table.item(selected[0].row(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_buttons(self) -> None:
        has_selection = self._selected_order_id() is not None
        self._open_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        self._edit_button.setEnabled(has_selection and bool(self._user and self._user.is_admin))

    def _open_selected(self) -> None:
        order_id = self._selected_order_id()
        if order_id is None:
            show_warning(
                self,
                "Заказ не выбран",
                "Выберите заказ в таблице, затем нажмите «Открыть».",
            )
            return
        self.open_requested.emit(order_id)

    def _edit_selected(self) -> None:
        if not self._user or not self._user.is_admin:
            show_warning(
                self,
                "Доступ запрещён",
                "Редактирование заказов доступно только администратору.",
            )
            return
        order_id = self._selected_order_id()
        if order_id is None:
            show_warning(
                self,
                "Заказ не выбран",
                "Выберите заказ в таблице, затем нажмите «Изменить».",
            )
            return
        self.edit_requested.emit(order_id)

    def _delete_selected(self) -> None:
        order_id = self._selected_order_id()
        if order_id is None:
            show_warning(
                self,
                "Заказ не выбран",
                "Выберите заказ в таблице, который нужно удалить.",
            )
            return
        if not ask_confirmation(
            self,
            "Удаление заказа",
            f"Удалить заказ №{order_id} вместе со всем составом?\n\n"
            "Товары из удалённого заказа будут возвращены на склад. "
            "Отмена не изменит данные.",
        ):
            return
        self.delete_requested.emit(order_id)

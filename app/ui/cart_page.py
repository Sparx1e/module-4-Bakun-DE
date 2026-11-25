"""Страница корзины клиента перед подтверждением заказа."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.order_service import Cart
from app.ui.formatting import format_money, format_quantity
from app.ui.messages import ask_confirmation, show_warning


class CartPage(QWidget):
    """Состав формируемого заказа: изменение количества, удаление, подтверждение."""

    back_requested = Signal()
    confirm_requested = Signal()
    quantity_changed = Signal(int, int)  # stock_item_id, quantity
    remove_requested = Signal(int)  # stock_item_id

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._cart = Cart()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        back_button = QPushButton("← Назад в каталог")
        back_button.setObjectName("secondaryButton")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        top.addWidget(back_button)
        top.addStretch(1)
        layout.addLayout(top)

        self._empty_label = QLabel(
            "Заказ пока пуст. Вернитесь в каталог, выберите модель, "
            "вариант исполнения и количество, затем добавьте позицию в заказ."
        )
        self._empty_label.setObjectName("mutedLabel")
        self._empty_label.setWordWrap(True)
        layout.addWidget(self._empty_label)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Товар", "Вариант", "Цена", "Количество", "Сумма"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in range(1, 5):
            self._table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table, 1)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(QLabel("Количество для выбранной позиции:"))
        self._quantity_spin = QSpinBox()
        self._quantity_spin.setMinimum(1)
        self._quantity_spin.setMaximum(1)
        controls.addWidget(self._quantity_spin)

        change_button = QPushButton("Изменить количество")
        change_button.setObjectName("secondaryButton")
        change_button.clicked.connect(self._on_change_quantity)
        controls.addWidget(change_button)

        remove_button = QPushButton("Удалить позицию")
        remove_button.setObjectName("dangerButton")
        remove_button.clicked.connect(self._on_remove)
        controls.addWidget(remove_button)
        controls.addStretch(1)

        self._total_label = QLabel("Итого: 0,00 ₽")
        self._total_label.setObjectName("totalLabel")
        controls.addWidget(self._total_label)
        layout.addLayout(controls)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self._confirm_button = QPushButton("Подтвердить заказ")
        self._confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_button.clicked.connect(self.confirm_requested.emit)
        actions.addWidget(self._confirm_button)
        layout.addLayout(actions)

    def load_cart(self, cart: Cart) -> None:
        self._cart = cart
        selected_stock_item_id = self._selected_stock_item_id()
        self._table.setRowCount(0)
        target_row = 0
        for item in cart.items:
            row = self._table.rowCount()
            self._table.insertRow(row)
            product_item = QTableWidgetItem(item.product_name)
            product_item.setData(Qt.ItemDataRole.UserRole, item.stock_item_id)
            product_item.setToolTip(f"{item.manufacturer} · {item.product_name}")
            self._table.setItem(row, 0, product_item)
            self._table.setItem(row, 1, QTableWidgetItem(item.variant_name))
            self._table.setItem(row, 2, QTableWidgetItem(format_money(item.unit_price)))
            self._table.setItem(
                row, 3, QTableWidgetItem(format_quantity(item.quantity))
            )
            self._table.setItem(row, 4, QTableWidgetItem(format_money(item.line_total)))
            self._table.setRowHeight(row, 34)
            if item.stock_item_id == selected_stock_item_id:
                target_row = row

        is_empty = cart.is_empty()
        self._table.setVisible(not is_empty)
        self._empty_label.setVisible(is_empty)
        self._confirm_button.setEnabled(not is_empty)
        self._total_label.setText(f"Итого: {format_money(cart.total)}")

        if not is_empty:
            self._table.selectRow(target_row)
        else:
            self._quantity_spin.setMaximum(1)

    def _selected_stock_item_id(self) -> int | None:
        selected = self._table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self._table.item(selected[0].row(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_selection_changed(self) -> None:
        stock_item_id = self._selected_stock_item_id()
        if stock_item_id is None:
            return
        for item in self._cart.items:
            if item.stock_item_id == stock_item_id:
                self._quantity_spin.setMaximum(max(1, item.available))
                self._quantity_spin.setValue(item.quantity)
                return

    def _on_change_quantity(self) -> None:
        stock_item_id = self._selected_stock_item_id()
        if stock_item_id is None:
            show_warning(
                self,
                "Позиция не выбрана",
                "Выберите строку заказа в таблице, затем измените количество.",
            )
            return
        self.quantity_changed.emit(stock_item_id, self._quantity_spin.value())

    def _on_remove(self) -> None:
        stock_item_id = self._selected_stock_item_id()
        if stock_item_id is None:
            show_warning(
                self,
                "Позиция не выбрана",
                "Выберите строку заказа в таблице, которую нужно удалить.",
            )
            return
        if not ask_confirmation(
            self,
            "Удаление позиции",
            "Удалить выбранную позицию из заказа? "
            "До подтверждения заказа изменения не сохраняются в базе данных.",
        ):
            return
        self.remove_requested.emit(stock_item_id)

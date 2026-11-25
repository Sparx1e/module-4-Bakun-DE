"""Форма создания нового заказа менеджером или администратором."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.errors import AppError
from app.models.entities import CatalogProduct, User, VariantStock
from app.services.order_service import Cart
from app.ui.formatting import format_money, format_quantity
from app.ui.messages import ask_confirmation, show_warning


class OrderFormPage(QWidget):
    """Выбор клиента, товаров из каталога и подтверждение нового заказа."""

    confirm_requested = Signal(int, object)  # client_id, Cart
    cancel_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._cart = Cart()
        self._products: list[CatalogProduct] = []
        self._clients: list[User] = []
        self._user: User | None = None
        self._current_product: CatalogProduct | None = None
        self._current_variants: list[VariantStock] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        cancel_top = QPushButton("← Отмена")
        cancel_top.setObjectName("secondaryButton")
        cancel_top.clicked.connect(self._cancel)
        top.addWidget(cancel_top)
        top.addStretch(1)
        layout.addLayout(top)

        client_row = QHBoxLayout()
        client_row.addWidget(QLabel("Клиент:"))
        self._client_combo = QComboBox()
        client_row.addWidget(self._client_combo, 1)
        self._client_label = QLabel()
        self._client_label.setStyleSheet("font-weight: 600;")
        client_row.addWidget(self._client_label, 1)
        layout.addLayout(client_row)

        selection_card = QFrame()
        selection_card.setObjectName("card")
        selection_card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        selection_layout = QVBoxLayout(selection_card)
        selection_layout.setContentsMargins(16, 12, 16, 12)
        selection_layout.setSpacing(8)

        selection_title = QLabel("Товар из каталога")
        selection_title.setObjectName("sectionTitle")
        selection_layout.addWidget(selection_title)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Поиск товара по наименованию")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._fill_products)
        selection_layout.addWidget(self._search_edit)

        self._product_list = QListWidget()
        self._product_list.setMaximumHeight(150)
        self._product_list.currentItemChanged.connect(self._on_product_changed)
        selection_layout.addWidget(self._product_list)

        self._product_details_label = QLabel()
        self._product_details_label.setObjectName("mutedLabel")
        self._product_details_label.setWordWrap(True)
        selection_layout.addWidget(self._product_details_label)

        variant_row = QHBoxLayout()
        variant_row.setSpacing(10)

        variant_box = QVBoxLayout()
        variant_box.addWidget(QLabel("Вариант исполнения"))
        self._variant_combo = QComboBox()
        self._variant_combo.currentIndexChanged.connect(self._on_variant_changed)
        variant_box.addWidget(self._variant_combo)
        variant_row.addLayout(variant_box, 2)

        quantity_box = QVBoxLayout()
        quantity_box.addWidget(QLabel("Количество"))
        self._quantity_spin = QSpinBox()
        self._quantity_spin.setMinimum(1)
        self._quantity_spin.setMaximum(1)
        quantity_box.addWidget(self._quantity_spin)
        variant_row.addLayout(quantity_box, 1)

        self._add_button = QPushButton("Добавить позицию")
        self._add_button.clicked.connect(self._add_item)
        variant_row.addWidget(self._add_button, 0, Qt.AlignmentFlag.AlignBottom)
        selection_layout.addLayout(variant_row)

        self._availability_label = QLabel()
        self._availability_label.setObjectName("mutedLabel")
        selection_layout.addWidget(self._availability_label)
        layout.addWidget(selection_card)

        cart_title = QLabel("Позиции заказа")
        cart_title.setObjectName("sectionTitle")
        layout.addWidget(cart_title)

        self._empty_label = QLabel(
            "Позиции ещё не добавлены. Выберите товар, вариант и количество выше."
        )
        self._empty_label.setObjectName("mutedLabel")
        layout.addWidget(self._empty_label)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Товар", "Вариант", "Кол-во", "Цена", "Сумма"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in (1, 2, 3, 4):
            self._table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        layout.addWidget(self._table, 1)

        bottom = QHBoxLayout()
        self._remove_button = QPushButton("Удалить позицию")
        self._remove_button.setObjectName("dangerButton")
        self._remove_button.clicked.connect(self._remove_item)
        bottom.addWidget(self._remove_button)
        bottom.addStretch(1)
        self._total_label = QLabel("Итого: 0,00 ₽")
        self._total_label.setObjectName("totalLabel")
        bottom.addWidget(self._total_label)
        layout.addLayout(bottom)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self._confirm_button = QPushButton("Подтвердить заказ")
        self._confirm_button.clicked.connect(self._confirm)
        actions.addWidget(self._confirm_button)
        cancel_button = QPushButton("Отмена")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self._cancel)
        actions.addWidget(cancel_button)
        layout.addLayout(actions)

    def load(self, clients: list[User], products: list[CatalogProduct], user: User) -> None:
        self._clients = clients
        self._products = products
        self._user = user
        self._cart = Cart()

        self._client_combo.blockSignals(True)
        self._client_combo.clear()
        if user.is_staff:
            self._client_combo.addItem("Выберите клиента", None)
            for client in clients:
                self._client_combo.addItem(client.full_name, client.user_id)
            self._client_combo.setVisible(True)
            self._client_label.setVisible(False)
        else:
            self._client_combo.setVisible(False)
            self._client_label.setVisible(True)
            self._client_label.setText(user.full_name)
        self._client_combo.blockSignals(False)

        self._search_edit.blockSignals(True)
        self._search_edit.clear()
        self._search_edit.blockSignals(False)
        self._fill_products()
        self._refresh_cart()

    def _fill_products(self) -> None:
        query = self._search_edit.text().strip().casefold()
        self._product_list.blockSignals(True)
        self._product_list.clear()
        for product in self._products:
            if query and query not in product.name.casefold():
                continue
            item = QListWidgetItem(
                f"{product.name} — {product.manufacturer} · "
                f"{format_money(product.final_price)} · остаток {product.total_quantity} шт."
            )
            item.setData(Qt.ItemDataRole.UserRole, product.product_id)
            self._product_list.addItem(item)
        self._product_list.blockSignals(False)

        if self._product_list.count():
            first_available = 0
            for index in range(self._product_list.count()):
                product_id = self._product_list.item(index).data(Qt.ItemDataRole.UserRole)
                product = next(
                    (item for item in self._products if item.product_id == product_id),
                    None,
                )
                if product is not None and product.total_quantity > 0:
                    first_available = index
                    break
            self._product_list.setCurrentRow(first_available)
        else:
            self._current_product = None
            self._variant_combo.clear()
            self._add_button.setEnabled(False)
            self._product_details_label.setText("")
            self._availability_label.setText(
                "Товар не найден. Измените поисковый запрос."
            )

    def _on_product_changed(self) -> None:
        item = self._product_list.currentItem()
        if item is None:
            self._current_product = None
            self._product_details_label.setText("")
            return
        product_id = item.data(Qt.ItemDataRole.UserRole)
        self._current_product = next(
            (product for product in self._products if product.product_id == product_id),
            None,
        )
        if self._current_product is None:
            self._product_details_label.setText("")
            return

        product = self._current_product
        description = product.description
        if len(description) > 220:
            description = description[:217].rstrip() + "…"
        self._product_details_label.setText(
            f"Категория: {product.category} · {product.subcategory}\n"
            f"Состав: {product.material}\n"
            f"Цена: {format_money(product.final_price)}\n"
            f"Описание: {description}"
        )

        self._current_variants = [
            variant for variant in self._current_product.variants if variant.quantity > 0
        ]
        self._variant_combo.blockSignals(True)
        self._variant_combo.clear()
        for variant in self._current_variants:
            self._variant_combo.addItem(
                f"{variant.variant_name} — доступно {variant.quantity} шт."
            )
        self._variant_combo.blockSignals(False)

        has_variants = bool(self._current_variants)
        self._variant_combo.setEnabled(has_variants)
        self._quantity_spin.setEnabled(has_variants)
        self._add_button.setEnabled(has_variants)
        if has_variants:
            self._on_variant_changed()
        else:
            self._quantity_spin.setMaximum(1)
            self._availability_label.setText(
                "У выбранной модели нет доступных вариантов исполнения."
            )

    def _on_variant_changed(self) -> None:
        index = self._variant_combo.currentIndex()
        if index < 0 or index >= len(self._current_variants):
            return
        variant = self._current_variants[index]
        self._quantity_spin.setMaximum(max(1, variant.quantity))
        self._quantity_spin.setValue(1)
        self._availability_label.setText(
            f"Доступно: {variant.quantity} шт. варианта «{variant.variant_name}»."
        )

    def _add_item(self) -> None:
        if self._current_product is None:
            return
        index = self._variant_combo.currentIndex()
        if index < 0 or index >= len(self._current_variants):
            show_warning(
                self,
                "Вариант не выбран",
                "Выберите доступный вариант исполнения товара.",
            )
            return
        variant = self._current_variants[index]
        try:
            self._cart.add(self._current_product, variant, self._quantity_spin.value())
        except AppError as exc:
            show_warning(self, exc.title, str(exc))
            return
        self._refresh_cart()

    def _refresh_cart(self) -> None:
        self._table.setRowCount(0)
        for item in self._cart.items:
            row = self._table.rowCount()
            self._table.insertRow(row)
            name_item = QTableWidgetItem(item.product_name)
            name_item.setData(Qt.ItemDataRole.UserRole, item.stock_item_id)
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, QTableWidgetItem(item.variant_name))
            self._table.setItem(row, 2, QTableWidgetItem(format_quantity(item.quantity)))
            self._table.setItem(row, 3, QTableWidgetItem(format_money(item.unit_price)))
            self._table.setItem(row, 4, QTableWidgetItem(format_money(item.line_total)))
            self._table.setRowHeight(row, 32)

        is_empty = self._cart.is_empty()
        self._table.setVisible(not is_empty)
        self._empty_label.setVisible(is_empty)
        self._remove_button.setEnabled(not is_empty)
        self._total_label.setText(f"Итого: {format_money(self._cart.total)}")

        if not is_empty:
            self._table.selectRow(self._table.rowCount() - 1)

    def _remove_item(self) -> None:
        selected = self._table.selectionModel().selectedRows()
        if not selected:
            show_warning(
                self,
                "Позиция не выбрана",
                "Выберите строку заказа, которую нужно удалить.",
            )
            return
        item = self._table.item(selected[0].row(), 0)
        if item is None:
            return
        self._cart.remove(item.data(Qt.ItemDataRole.UserRole))
        self._refresh_cart()

    def _confirm(self) -> None:
        if self._cart.is_empty():
            show_warning(
                self,
                "Пустой заказ",
                "Нельзя подтвердить заказ без товарных позиций. "
                "Добавьте хотя бы один товар.",
            )
            return
        if self._user is None:
            return
        if self._user.is_staff:
            client_id = self._client_combo.currentData()
            if client_id is None:
                show_warning(
                    self,
                    "Клиент не выбран",
                    "Выберите клиента, для которого оформляется заказ.",
                )
                return
            if not any(client.user_id == int(client_id) for client in self._clients):
                show_warning(
                    self,
                    "Клиент не найден",
                    "Выбранный клиент отсутствует в списке. Обновите форму и повторите выбор.",
                )
                return
        else:
            client_id = self._user.user_id
        self.confirm_requested.emit(int(client_id), self._cart)

    def _cancel(self) -> None:
        if not self._cart.is_empty() and not ask_confirmation(
            self,
            "Отмена оформления",
            "Отменить создание заказа? Добавленные позиции не будут сохранены.",
        ):
            return
        self.cancel_requested.emit()

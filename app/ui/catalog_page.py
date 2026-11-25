"""Главная страница каталога моделей товаров."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import CatalogProduct, User
from app.services.catalog_service import (
    ALL_CATEGORIES,
    SORT_DEFAULT,
    SORT_PRICE_ASC,
    SORT_PRICE_DESC,
    CatalogService,
)
from app.ui.widgets import ProductRow


class CatalogPage(QWidget):
    """Каталог с поиском, фильтром по категории и сортировкой по цене."""

    product_selected = Signal(int)
    cart_requested = Signal()
    orders_requested = Signal()

    def __init__(self, categories: list[str]) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._products: list[CatalogProduct] = []
        self._user: User | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 16)
        layout.setSpacing(12)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Поиск по наименованию и описанию")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._apply_filters)
        controls.addWidget(self._search_edit, 2)

        self._category_combo = QComboBox()
        self._category_combo.addItem(ALL_CATEGORIES)
        for category in categories:
            self._category_combo.addItem(category)
        self._category_combo.currentIndexChanged.connect(self._apply_filters)
        controls.addWidget(self._category_combo, 1)

        self._sort_combo = QComboBox()
        self._sort_combo.addItem("Без сортировки", SORT_DEFAULT)
        self._sort_combo.addItem("Цена: по возрастанию", SORT_PRICE_ASC)
        self._sort_combo.addItem("Цена: по убыванию", SORT_PRICE_DESC)
        self._sort_combo.currentIndexChanged.connect(self._apply_filters)
        controls.addWidget(self._sort_combo, 1)

        layout.addLayout(controls)

        info_row = QHBoxLayout()
        self._count_label = QLabel()
        self._count_label.setObjectName("mutedLabel")
        info_row.addWidget(self._count_label)
        info_row.addStretch(1)

        self._orders_button = QPushButton("Заказы")
        self._orders_button.setObjectName("secondaryButton")
        self._orders_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._orders_button.clicked.connect(self.orders_requested.emit)
        info_row.addWidget(self._orders_button)

        self._cart_button = QPushButton("Корзина (0)")
        self._cart_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cart_button.clicked.connect(self.cart_requested.emit)
        info_row.addWidget(self._cart_button)

        layout.addLayout(info_row)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background-color: #FFFFFF;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(10)
        self._rows_layout.addStretch(1)
        self._scroll.setWidget(self._rows_container)
        layout.addWidget(self._scroll, 1)

        self.set_user(None)

    def set_user(self, user: User | None) -> None:
        """Гость видит каталог без поиска, фильтрации и сортировки."""
        self._user = user
        is_authorized = user is not None
        for widget in (self._search_edit, self._category_combo, self._sort_combo):
            widget.setEnabled(is_authorized)
        if is_authorized:
            for widget in (self._search_edit, self._category_combo, self._sort_combo):
                widget.setToolTip("")
        else:
            hint = "Поиск, фильтрация и сортировка доступны после входа."
            for widget in (self._search_edit, self._category_combo, self._sort_combo):
                widget.setToolTip(hint)

        self._orders_button.setVisible(bool(user and user.is_staff))
        self._cart_button.setVisible(bool(user and user.is_client))

    def set_cart_count(self, count: int) -> None:
        self._cart_button.setText(f"Корзина ({count})")

    def load_products(self, products: list[CatalogProduct]) -> None:
        self._products = products
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self._search_edit.text() if self._search_edit.isEnabled() else ""
        category = (
            self._category_combo.currentText()
            if self._category_combo.isEnabled()
            else ALL_CATEGORIES
        )
        sort_mode = (
            self._sort_combo.currentData()
            if self._sort_combo.isEnabled()
            else SORT_DEFAULT
        )

        visible = CatalogService.filter_products(
            self._products,
            query=query,
            category=category,
            sort_mode=sort_mode,
        )
        self._render_rows(visible)
        self._count_label.setText(
            f"Найдено моделей: {len(visible)} из {len(self._products)}"
        )

    def _render_rows(self, products: list[CatalogProduct]) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # Убираем строку из контейнера сразу, иначе при быстрой
                # перерисовке старые строки остаются видимыми до deleteLater().
                widget.setParent(None)
                widget.deleteLater()

        if not products:
            empty = QLabel(
                "Товары не найдены. Измените поисковый запрос или выберите другую категорию."
            )
            empty.setObjectName("mutedLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._rows_layout.addWidget(empty)
        else:
            for product in products:
                row = ProductRow(product)
                row.clicked.connect(self.product_selected.emit)
                self._rows_layout.addWidget(row)

        self._rows_layout.addStretch(1)

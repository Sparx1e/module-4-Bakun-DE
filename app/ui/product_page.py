"""Страница просмотра модели товара и добавления позиции в заказ."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import CatalogProduct, User, VariantStock
from app.ui.formatting import format_money
from app.ui.images import load_product_pixmap
from app.ui.messages import show_warning


class ProductPage(QWidget):
    """Данные выбранной модели, выбор варианта и количества."""

    back_requested = Signal()
    add_requested = Signal(int, int, int)  # product_id, stock_item_id, quantity
    login_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._product: CatalogProduct | None = None
        self._variants: list[VariantStock] = []

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

        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(26)

        self._image_label = QLabel()
        self._image_label.setFixedSize(340, 270)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self._image_label, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)

        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 17pt; font-weight: 700;")
        self._title_label.setWordWrap(True)
        info.addWidget(self._title_label)

        self._category_label = QLabel()
        self._category_label.setObjectName("mutedLabel")
        info.addWidget(self._category_label)

        self._material_label = QLabel()
        info.addWidget(self._material_label)

        self._variants_label = QLabel()
        self._variants_label.setWordWrap(True)
        info.addWidget(self._variants_label)

        description_caption = QLabel("Описание")
        description_caption.setObjectName("sectionTitle")
        info.addWidget(description_caption)

        self._description_label = QLabel()
        self._description_label.setWordWrap(True)
        self._description_label.setMinimumHeight(56)
        info.addWidget(self._description_label)

        price_row = QHBoxLayout()
        self._price_label = QLabel()
        self._price_label.setObjectName("priceLabel")
        price_row.addWidget(self._price_label)
        self._discount_label = QLabel()
        self._discount_label.setObjectName("discountLabel")
        price_row.addWidget(self._discount_label)
        price_row.addStretch(1)
        info.addLayout(price_row)

        order_caption = QLabel("Оформление позиции")
        order_caption.setObjectName("sectionTitle")
        info.addWidget(order_caption)

        form_row = QHBoxLayout()
        form_row.setSpacing(10)

        variant_box = QVBoxLayout()
        variant_box.addWidget(QLabel("Вариант исполнения"))
        self._variant_combo = QComboBox()
        self._variant_combo.currentIndexChanged.connect(self._on_variant_changed)
        variant_box.addWidget(self._variant_combo)
        form_row.addLayout(variant_box, 2)

        quantity_box = QVBoxLayout()
        quantity_box.addWidget(QLabel("Количество"))
        self._quantity_spin = QSpinBox()
        self._quantity_spin.setMinimum(1)
        self._quantity_spin.setMaximum(1)
        quantity_box.addWidget(self._quantity_spin)
        form_row.addLayout(quantity_box, 1)
        info.addLayout(form_row)

        self._availability_label = QLabel()
        self._availability_label.setObjectName("mutedLabel")
        info.addWidget(self._availability_label)

        self._add_button = QPushButton("Добавить в заказ")
        self._add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_button.clicked.connect(self._on_add_clicked)
        info.addWidget(self._add_button)

        self._login_button = QPushButton("Войти, чтобы оформить заказ")
        self._login_button.setObjectName("secondaryButton")
        self._login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._login_button.clicked.connect(self.login_requested.emit)
        self._login_button.hide()
        info.addWidget(self._login_button)

        self._staff_hint = QLabel(
            "Вы вошли как сотрудник. Для оформления заказа используйте раздел "
            "«Заказы» → «Добавить»."
        )
        self._staff_hint.setObjectName("mutedLabel")
        self._staff_hint.setWordWrap(True)
        self._staff_hint.hide()
        info.addWidget(self._staff_hint)

        info.addStretch(1)
        card_layout.addLayout(info, 1)
        layout.addWidget(card, 0)
        layout.addStretch(1)

    def load_product(self, product: CatalogProduct, user: User | None) -> None:
        self._product = product
        self._image_label.setPixmap(load_product_pixmap(product.image_path, 340, 270))
        self._title_label.setText(f"{product.manufacturer} | {product.name}")
        self._category_label.setText(
            f"Категория: {product.category} · {product.subcategory}"
        )
        self._material_label.setText(f"Состав: {product.material}")
        self._variants_label.setText(
            "Варианты исполнения: "
            + ", ".join(
                f"{variant.variant_name} ({variant.quantity} шт.)"
                for variant in product.variants
            )
        )
        self._description_label.setText(product.description)
        self._price_label.setText(format_money(product.final_price))
        if product.is_discounted:
            self._discount_label.setText(
                f"скидка {product.discount_percent}% (без заказов в предыдущем месяце)"
            )
        else:
            self._discount_label.setText("")

        available_variants = [
            variant for variant in product.variants if variant.quantity > 0
        ]
        self._variants = available_variants
        self._variant_combo.blockSignals(True)
        self._variant_combo.clear()
        for variant in available_variants:
            self._variant_combo.addItem(
                f"{variant.variant_name} — доступно {variant.quantity} шт."
            )
        self._variant_combo.blockSignals(False)

        is_authorized = user is not None
        is_client = bool(user and user.is_client)
        self._login_button.setVisible(not is_authorized)
        self._add_button.setVisible(is_client)
        self._staff_hint.setVisible(bool(user and user.is_staff))

        if not available_variants:
            self._variant_combo.setEnabled(False)
            self._quantity_spin.setEnabled(False)
            self._add_button.setEnabled(False)
            self._availability_label.setText(
                "Все варианты исполнения отсутствуют на складе. "
                "Выберите другую модель или вернитесь позже."
            )
            self._quantity_spin.setMaximum(1)
            return

        self._variant_combo.setEnabled(True)
        self._quantity_spin.setEnabled(True)
        self._add_button.setEnabled(True)
        self._on_variant_changed()

    def _on_variant_changed(self) -> None:
        index = self._variant_combo.currentIndex()
        if index < 0 or index >= len(self._variants):
            self._quantity_spin.setMaximum(1)
            self._availability_label.setText("")
            return
        variant = self._variants[index]
        self._quantity_spin.setMaximum(max(1, variant.quantity))
        self._quantity_spin.setValue(1)
        self._availability_label.setText(
            f"Доступно для заказа: {variant.quantity} шт. варианта «{variant.variant_name}»."
        )

    def _on_add_clicked(self) -> None:
        if self._product is None:
            return
        index = self._variant_combo.currentIndex()
        if index < 0 or index >= len(self._variants):
            show_warning(
                self,
                "Товар недоступен",
                "Не выбран доступный вариант исполнения. Выберите вариант из списка.",
            )
            return
        variant = self._variants[index]
        quantity = self._quantity_spin.value()
        self.add_requested.emit(
            self._product.product_id,
            variant.stock_item_id,
            quantity,
        )

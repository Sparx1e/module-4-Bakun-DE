"""Повторно используемые элементы интерфейса."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.models.entities import CatalogProduct
from app.ui.formatting import format_money, format_quantity
from app.ui.images import load_product_pixmap


def make_transparent(widget: QWidget) -> None:
    """Мышь должна доходить до строки каталога, а не теряться на подписях."""
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)


class ProductRow(QFrame):
    """Строка каталога по макету: изображение, сведения и цена."""

    clicked = Signal(int)

    def __init__(self, product: CatalogProduct) -> None:
        super().__init__()
        self._product_id = product.product_id
        self.setObjectName("productRowLow" if product.is_low_stock else "productRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(126)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 16, 12)
        layout.setSpacing(18)

        image_label = QLabel()
        image_label.setFixedSize(132, 100)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setPixmap(load_product_pixmap(product.image_path, 132, 100))
        make_transparent(image_label)
        layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignVCenter)

        center = QVBoxLayout()
        center.setSpacing(4)

        title = QLabel(f"{product.manufacturer} | {product.name}")
        title.setStyleSheet("font-size: 13pt; font-weight: 600;")
        title.setWordWrap(True)
        center.addWidget(title)

        category = QLabel(f"Категория: {product.category}")
        quantity = QLabel(f"Количество: {format_quantity(product.total_quantity)}")
        material = QLabel(f"Состав: {product.material}")
        for label in (title, category, quantity, material):
            make_transparent(label)
        center.addWidget(category)
        center.addWidget(quantity)
        center.addWidget(material)
        center.addStretch(1)
        layout.addLayout(center, 1)

        right = QVBoxLayout()
        right.setSpacing(2)
        right.addStretch(1)
        price = QLabel(format_money(product.final_price))
        price.setObjectName("priceLabel")
        price.setAlignment(Qt.AlignmentFlag.AlignRight)
        make_transparent(price)
        right.addWidget(price)
        if product.is_discounted:
            discount = QLabel(f"скидка {product.discount_percent}%")
            discount.setObjectName("discountLabel")
            discount.setAlignment(Qt.AlignmentFlag.AlignRight)
            make_transparent(discount)
            right.addWidget(discount)
        right.addStretch(1)
        layout.addLayout(right, 0)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._product_id)
        super().mouseReleaseEvent(event)

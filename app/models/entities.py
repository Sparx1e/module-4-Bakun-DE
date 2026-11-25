"""Доменные модели приложения «ФормаДесерт»."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class User:
    """Пользователь системы с ролью из справочника."""

    user_id: int
    login: str
    last_name: str
    first_name: str
    middle_name: str
    role_code: str
    role_name: str

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part).strip()

    @property
    def is_admin(self) -> bool:
        return self.role_code == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role_code == "manager"

    @property
    def is_staff(self) -> bool:
        return self.role_code in {"admin", "manager"}

    @property
    def is_client(self) -> bool:
        return self.role_code == "client"


@dataclass(frozen=True)
class VariantStock:
    """Вариант исполнения модели и его доступный остаток."""

    stock_item_id: int
    variant_id: int
    variant_name: str
    quantity: int


@dataclass(frozen=True)
class CatalogProduct:
    """Модель товара для каталога с рассчитанной ценой и остатком."""

    product_id: int
    article: str
    name: str
    category: str
    subcategory: str
    manufacturer: str
    image_path: str | None
    material: str
    description: str
    base_price: Decimal
    total_quantity: int
    has_orders_previous_month: bool
    variants: tuple[VariantStock, ...]
    discount_percent: int = 0
    final_price: Decimal = Decimal("0.00")

    @property
    def is_low_stock(self) -> bool:
        """Модель подсвечивается при суммарном остатке не более трёх."""
        return self.total_quantity <= 3

    @property
    def is_discounted(self) -> bool:
        return self.discount_percent > 0


@dataclass(frozen=True)
class CartItem:
    """Позиция формируемого заказа."""

    stock_item_id: int
    product_id: int
    product_name: str
    manufacturer: str
    variant_name: str
    quantity: int
    unit_price: Decimal
    available: int

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class OrderSummary:
    """Краткие сведения о заказе для списка заказов."""

    order_id: int
    order_date: datetime
    client_name: str
    total: Decimal


@dataclass(frozen=True)
class OrderItem:
    """Строка сохранённого состава заказа."""

    order_item_id: int
    stock_item_id: int
    product_id: int
    product_name: str
    manufacturer: str
    variant_name: str
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class OrderDetail:
    """Заказ с полным составом."""

    order_id: int
    order_date: datetime
    client_name: str
    items: tuple[OrderItem, ...]

    @property
    def total(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0.00"))

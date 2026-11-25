"""Бизнес-логика формирования и сохранения заказов."""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from app.db.order_repository import OrderRepository
from app.errors import NotFoundError, StockError, ValidationError
from app.models.entities import CartItem, CatalogProduct, OrderDetail, OrderSummary, VariantStock


class Cart:
    """Корзина текущего заказа с проверкой доступного количества."""

    def __init__(self) -> None:
        self._items: dict[int, CartItem] = {}

    @property
    def items(self) -> list[CartItem]:
        return list(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    @property
    def total(self) -> Decimal:
        total = sum((item.line_total for item in self._items.values()), Decimal("0.00"))
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def add(self, product: CatalogProduct, variant: VariantStock, quantity: int) -> None:
        if quantity <= 0:
            raise ValidationError(
                "Количество должно быть положительным целым числом. "
                "Введите значение от 1 до доступного остатка."
            )
        if quantity > variant.quantity:
            raise StockError(
                f"Для варианта «{variant.variant_name}» доступно {variant.quantity} шт. "
                "Уменьшите количество и повторите добавление."
            )

        existing = self._items.get(variant.stock_item_id)
        total_quantity = quantity + (existing.quantity if existing else 0)
        if total_quantity > variant.quantity:
            already = existing.quantity if existing else 0
            raise StockError(
                f"В заказе уже {already} шт. варианта «{variant.variant_name}». "
                f"Всего доступно {variant.quantity} шт., поэтому можно добавить "
                f"не более {variant.quantity - already} шт."
            )

        self._items[variant.stock_item_id] = CartItem(
            stock_item_id=variant.stock_item_id,
            product_id=product.product_id,
            product_name=product.name,
            manufacturer=product.manufacturer,
            variant_name=variant.variant_name,
            quantity=total_quantity,
            unit_price=product.final_price,
            available=variant.quantity,
        )

    def set_quantity(self, stock_item_id: int, quantity: int) -> None:
        item = self._items.get(stock_item_id)
        if item is None:
            raise NotFoundError(
                "Позиция не найдена в заказе. Обновите форму и повторите действие."
            )
        if quantity <= 0:
            raise ValidationError(
                "Количество должно быть положительным целым числом. "
                "Для удаления позиции используйте кнопку «Удалить позицию»."
            )
        if quantity > item.available:
            raise StockError(
                f"Для варианта «{item.variant_name}» доступно {item.available} шт. "
                f"Нельзя указать {quantity} шт."
            )
        self._items[stock_item_id] = CartItem(
            stock_item_id=item.stock_item_id,
            product_id=item.product_id,
            product_name=item.product_name,
            manufacturer=item.manufacturer,
            variant_name=item.variant_name,
            quantity=quantity,
            unit_price=item.unit_price,
            available=item.available,
        )

    def remove(self, stock_item_id: int) -> None:
        self._items.pop(stock_item_id, None)

    def clear(self) -> None:
        self._items.clear()


class OrderService:
    """Операции с заказами для клиента, менеджера и администратора."""

    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def list_orders(self) -> list[OrderSummary]:
        return self._repository.list_orders()

    def get_order(self, order_id: int) -> OrderDetail:
        return self._repository.get_order(order_id)

    def create_order(
        self,
        user_id: int,
        cart: Cart,
        order_date: datetime | None = None,
    ) -> int:
        if cart.is_empty():
            raise ValidationError(
                "Заказ не содержит товарных позиций. Добавьте хотя бы один товар "
                "из каталога и повторите подтверждение."
            )
        items = [
            (item.stock_item_id, item.quantity, item.unit_price)
            for item in cart.items
        ]
        return self._repository.create_order(
            user_id=user_id,
            order_date=order_date or datetime.now(),
            items=items,
        )

    def delete_order(self, order_id: int) -> None:
        self._repository.delete_order(order_id)

    def update_order(
        self,
        order_id: int,
        order_date: datetime,
        delete_item_ids: list[int],
    ) -> None:
        self._repository.update_order(order_id, order_date, delete_item_ids)

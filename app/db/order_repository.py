from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from app.db.connection import Database
from app.errors import NotFoundError, StockError, ValidationError
from app.models.entities import OrderDetail, OrderItem, OrderSummary

_LIST_ORDERS_SQL = """
SELECT o.order_id,
       o.order_date,
       trim(concat_ws(' ', u.last_name, u.first_name, u.middle_name)) AS client_name,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0)::numeric(12, 2) AS total
FROM orders o
JOIN users u ON u.user_id = o.user_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_date, u.last_name, u.first_name, u.middle_name
ORDER BY o.order_date DESC, o.order_id DESC
"""

_ORDER_HEADER_SQL = """
SELECT o.order_id,
       o.order_date,
       trim(concat_ws(' ', u.last_name, u.first_name, u.middle_name)) AS client_name
FROM orders o
JOIN users u ON u.user_id = o.user_id
WHERE o.order_id = %s
"""

_ORDER_ITEMS_SQL = """
SELECT oi.order_item_id,
       oi.stock_item_id,
       oi.quantity,
       oi.unit_price,
       p.product_id,
       p.name AS product_name,
       mf.manufacturer_name,
       v.variant_name
FROM order_items oi
JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
JOIN products p ON p.product_id = si.product_id
JOIN manufacturers mf ON mf.manufacturer_id = p.manufacturer_id
JOIN variants v ON v.variant_id = si.variant_id
WHERE oi.order_id = %s
ORDER BY oi.order_item_id
"""


class OrderRepository:
    """Сохранение и выборка заказов с контролем остатков."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def list_orders(self) -> list[OrderSummary]:
        with self._database.cursor() as cursor:
            cursor.execute(_LIST_ORDERS_SQL)
            rows = cursor.fetchall()
        return [
            OrderSummary(
                order_id=row["order_id"], # type: ignore
                order_date=row["order_date"], # type: ignore
                client_name=row["client_name"], # type: ignore
                total=Decimal(row["total"]), # type: ignore
            )
            for row in rows
        ]

    def get_order(self, order_id: int) -> OrderDetail:
        with self._database.cursor() as cursor:
            cursor.execute(_ORDER_HEADER_SQL, (order_id,))
            header = cursor.fetchone()
            if header is None:
                raise NotFoundError(
                    f"Заказ №{order_id} не найден. Возможно, он уже удалён. "
                    "Обновите список заказов."
                )
            cursor.execute(_ORDER_ITEMS_SQL, (order_id,))
            item_rows = cursor.fetchall()

        items = tuple(
            OrderItem(
                order_item_id=row["order_item_id"], # type: ignore
                stock_item_id=row["stock_item_id"], # type: ignore
                product_id=row["product_id"], # type: ignore
                product_name=row["product_name"], # type: ignore
                manufacturer=row["manufacturer_name"], # type: ignore
                variant_name=row["variant_name"], # type: ignore
                quantity=row["quantity"], # type: ignore
                unit_price=Decimal(row["unit_price"]), # type: ignore
            )
            for row in item_rows
        )
        return OrderDetail(
            order_id=header["order_id"], # type: ignore
            order_date=header["order_date"], # type: ignore
            client_name=header["client_name"], # type: ignore
            items=items,
        )

    def create_order(
        self,
        user_id: int,
        order_date: datetime,
        items: list[tuple[int, int, Decimal]],
    ) -> int:
        """Создаёт заказ и списывает остатки в одной транзакции.

        items: список кортежей (stock_item_id, quantity, unit_price).
        """
        if not items:
            raise ValidationError(
                "Нельзя оформить пустой заказ. Добавьте хотя бы одну товарную позицию."
            )

        with self._database.transaction() as cursor:
            stock_item_ids = [item[0] for item in items]
            cursor.execute(
                """
                SELECT stock_item_id, quantity
                FROM stock_items
                WHERE stock_item_id = ANY(%s)
                FOR UPDATE
                """,
                (stock_item_ids,),
            )
            stock_rows = {row["stock_item_id"]: row["quantity"] for row in cursor.fetchall()} # type: ignore

            for stock_item_id, quantity, _price in items:
                if quantity <= 0:
                    raise ValidationError(
                        "Количество товара в заказе должно быть положительным целым числом."
                    )
                if stock_item_id not in stock_rows:
                    raise NotFoundError(
                        "Товарная позиция не найдена в каталоге. Обновите каталог и повторите заказ."
                    )
                available = stock_rows[stock_item_id]
                if quantity > available:
                    raise StockError(
                        "Недостаточно товара на складе: запрошено "
                        f"{quantity} шт., доступно {available} шт. "
                        "Уменьшите количество и повторите оформление."
                    )

            cursor.execute(
                "INSERT INTO orders (order_date, user_id) VALUES (%s, %s) RETURNING order_id",
                (order_date, user_id),
            )
            order_id = cursor.fetchone()["order_id"] # type: ignore

            for stock_item_id, quantity, unit_price in items:
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, stock_item_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, stock_item_id, quantity, unit_price),
                )
                cursor.execute(
                    "UPDATE stock_items SET quantity = quantity - %s WHERE stock_item_id = %s",
                    (quantity, stock_item_id),
                )

        return order_id

    def delete_order(self, order_id: int) -> None:
        """Удаляет заказ и возвращает товары на склад."""
        with self._database.transaction() as cursor:
            cursor.execute(
                "SELECT order_id FROM orders WHERE order_id = %s FOR UPDATE",
                (order_id,),
            )
            if cursor.fetchone() is None:
                raise NotFoundError(
                    f"Заказ №{order_id} не найден. Возможно, он уже удалён."
                )

            cursor.execute(
                "SELECT stock_item_id, quantity FROM order_items WHERE order_id = %s",
                (order_id,),
            )
            for row in cursor.fetchall():
                cursor.execute(
                    "UPDATE stock_items SET quantity = quantity + %s WHERE stock_item_id = %s",
                    (row["quantity"], row["stock_item_id"]), # type: ignore
                )

            cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))

    def update_order(
        self,
        order_id: int,
        order_date: datetime,
        delete_item_ids: list[int],
    ) -> None:
        """Меняет дату заказа и удаляет выбранные позиции с возвратом остатков."""
        with self._database.transaction() as cursor:
            cursor.execute(
                "SELECT order_id FROM orders WHERE order_id = %s FOR UPDATE",
                (order_id,),
            )
            if cursor.fetchone() is None:
                raise NotFoundError(
                    f"Заказ №{order_id} не найден. Возможно, он уже удалён."
                )

            if delete_item_ids:
                cursor.execute(
                    """
                    SELECT order_item_id, stock_item_id, quantity
                    FROM order_items
                    WHERE order_id = %s AND order_item_id = ANY(%s)
                    FOR UPDATE
                    """,
                    (order_id, delete_item_ids),
                )
                rows = cursor.fetchall()
                if len(rows) != len(set(delete_item_ids)):
                    raise ValidationError(
                        "Часть выбранных позиций уже удалена. Закройте форму без сохранения "
                        "и откройте заказ заново."
                    )

                for row in rows:
                    cursor.execute(
                        "UPDATE stock_items SET quantity = quantity + %s WHERE stock_item_id = %s",
                        (row["quantity"], row["stock_item_id"]), # type: ignore
                    )
                    cursor.execute(
                        "DELETE FROM order_items WHERE order_item_id = %s",
                        (row["order_item_id"],), # type: ignore
                    )

            cursor.execute(
                "UPDATE orders SET order_date = %s WHERE order_id = %s",
                (order_date, order_id),
            )

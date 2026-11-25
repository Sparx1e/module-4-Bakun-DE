"""Чтение каталога товаров из PostgreSQL."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.db.connection import Database
from app.models.entities import CatalogProduct, VariantStock

# Для каждой модели считаем суммарный остаток и проверяем, были ли заказы
# в предыдущем календарном месяце относительно переданной даты расчёта.
_CATALOG_SQL = """
SELECT p.product_id,
       p.article,
       p.name,
       p.image_path,
       p.material,
       p.description,
       p.price,
       c.category_name,
       sc.subcategory_name,
       mf.manufacturer_name,
       COALESCE(st.total_quantity, 0) AS total_quantity,
       EXISTS (
           SELECT 1
           FROM order_items oi
           JOIN orders o ON o.order_id = oi.order_id
           JOIN stock_items si2 ON si2.stock_item_id = oi.stock_item_id
           WHERE si2.product_id = p.product_id
             AND o.order_date >= date_trunc('month', %s::date) - INTERVAL '1 month'
             AND o.order_date < date_trunc('month', %s::date)
       ) AS has_orders_previous_month
FROM products p
JOIN categories c ON c.category_id = p.category_id
JOIN subcategories sc ON sc.subcategory_id = p.subcategory_id
JOIN manufacturers mf ON mf.manufacturer_id = p.manufacturer_id
LEFT JOIN (
    SELECT product_id, SUM(quantity) AS total_quantity
    FROM stock_items
    GROUP BY product_id
) st ON st.product_id = p.product_id
ORDER BY p.product_id
"""

_STOCK_VARIANTS_SQL = """
SELECT si.stock_item_id,
       si.product_id,
       si.variant_id,
       v.variant_name,
       si.quantity
FROM stock_items si
JOIN variants v ON v.variant_id = si.variant_id
ORDER BY si.product_id, si.variant_id
"""

_CATEGORIES_SQL = """
SELECT category_name
FROM categories
ORDER BY category_name
"""


class CatalogRepository:
    """Запросы каталога: модели, варианты, остатки и категории."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def fetch_products(self, reference_date: date) -> list[CatalogProduct]:
        with self._database.cursor() as cursor:
            cursor.execute(_CATALOG_SQL, (reference_date, reference_date))
            product_rows = cursor.fetchall()
            cursor.execute(_STOCK_VARIANTS_SQL)
            variant_rows = cursor.fetchall()

        variants_by_product: dict[int, list[VariantStock]] = defaultdict(list)
        for row in variant_rows:
            variants_by_product[row["product_id"]].append(
                VariantStock(
                    stock_item_id=row["stock_item_id"],
                    variant_id=row["variant_id"],
                    variant_name=row["variant_name"],
                    quantity=row["quantity"],
                )
            )

        products: list[CatalogProduct] = []
        for row in product_rows:
            products.append(
                CatalogProduct(
                    product_id=row["product_id"],
                    article=row["article"],
                    name=row["name"],
                    category=row["category_name"],
                    subcategory=row["subcategory_name"],
                    manufacturer=row["manufacturer_name"],
                    image_path=row["image_path"],
                    material=row["material"],
                    description=row["description"],
                    base_price=Decimal(row["price"]),
                    total_quantity=row["total_quantity"],
                    has_orders_previous_month=row["has_orders_previous_month"],
                    variants=tuple(variants_by_product.get(row["product_id"], [])),
                )
            )
        return products

    def fetch_categories(self) -> list[str]:
        with self._database.cursor() as cursor:
            cursor.execute(_CATEGORIES_SQL)
            rows = cursor.fetchall()
        return [row["category_name"] for row in rows]

from __future__ import annotations
from dataclasses import replace
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from app.config import DISCOUNT_PERCENT, DISCOUNT_REFERENCE_DATE
from app.db.catalog_repository import CatalogRepository
from app.models.entities import CatalogProduct

SORT_DEFAULT = "default"
SORT_PRICE_ASC = "price_asc"
SORT_PRICE_DESC = "price_desc"

ALL_CATEGORIES = "Все категории"


class CatalogService:
    """Готовит каталог для интерфейса и применяет правила скидки."""

    def __init__(
        self,
        repository: CatalogRepository,
        reference_date: date = DISCOUNT_REFERENCE_DATE,
        discount_percent: int = DISCOUNT_PERCENT,
    ) -> None:
        self._repository = repository
        self._reference_date = reference_date
        self._discount_percent = discount_percent

    @property
    def reference_date(self) -> date:
        return self._reference_date

    def load_products(self) -> list[CatalogProduct]:
        products = self._repository.fetch_products(self._reference_date)
        return [self._apply_discount(product) for product in products]

    def get_product(self, product_id: int) -> CatalogProduct | None:
        for product in self.load_products():
            if product.product_id == product_id:
                return product
        return None

    def load_categories(self) -> list[str]:
        return self._repository.fetch_categories()

    def _apply_discount(self, product: CatalogProduct) -> CatalogProduct:
        """Скидка 25 % положена модели без заказов в предыдущем месяце.

        Предыдущий календарный месяц определяется относительно проверочной
        даты 20.10.2026, поэтому в расчёт попадает сентябрь 2026 года.
        Базовая цена в базе данных не изменяется: скидка вычисляется при показе.
        """
        discount = 0 if product.has_orders_previous_month else self._discount_percent
        multiplier = Decimal(100 - discount) / Decimal(100)
        final_price = (product.base_price * multiplier).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return replace(
            product,
            discount_percent=discount,
            final_price=final_price,
        )

    @staticmethod
    def filter_products(
        products: list[CatalogProduct],
        query: str = "",
        category: str = ALL_CATEGORIES,
        sort_mode: str = SORT_DEFAULT,
    ) -> list[CatalogProduct]:
        """Совместно применяет поиск, фильтр категории и сортировку."""
        needle = query.strip().casefold()
        result = products

        if category and category != ALL_CATEGORIES:
            result = [item for item in result if item.category == category]

        if needle:
            result = [
                item
                for item in result
                if needle in item.name.casefold() or needle in item.description.casefold()
            ]

        if sort_mode == SORT_PRICE_ASC:
            result = sorted(result, key=lambda item: (item.final_price, item.name))
        elif sort_mode == SORT_PRICE_DESC:
            result = sorted(result, key=lambda item: (item.final_price, item.name), reverse=True)
        else:
            result = sorted(result, key=lambda item: item.product_id)

        return result

from __future__ import annotations
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

NBSP = "\u00a0"


def to_decimal(value: Decimal | int | float | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def format_money(value: Decimal | int | float | str) -> str:
    """Рубли с двумя знаками, пробелом между разрядами и запятой."""
    amount = to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    formatted = f"{amount:,.2f}".replace(",", NBSP).replace(".", ",")
    return f"{formatted}{NBSP}₽"


def format_quantity(value: int) -> str:
    return f"{value}{NBSP}шт."


def format_date_time(value: datetime) -> str:
    return value.strftime("%d.%m.%Y %H:%M")


def format_date(value: datetime) -> str:
    return value.strftime("%d.%m.%Y")

"""Генерация ER-диаграммы базы данных «ФормаДесерт» в формате PDF.

Скрипт использует только PySide6 (QPdfWriter/QPainter), поэтому не требует
дополнительных библиотек. Запуск из корня проекта:

    python docs/build_er_diagram.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QMarginsF, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QPageLayout,
    QPageSize,
    QPainter,
    QPen,
    QPdfWriter,
)

OUTPUT_PATH = Path(__file__).resolve().parent / "ER_diagram.pdf"

PAGE_WIDTH = 1191.0
PAGE_HEIGHT = 842.0

PRIMARY = QColor("#70B2AF")
SECONDARY = QColor("#D2F6E7")
TEXT = QColor("#1F2A2E")
MUTED = QColor("#5C6B70")
BORDER = QColor("#4F8F8C")


@dataclass(frozen=True)
class Field:
    name: str
    data_type: str
    key: str = ""


@dataclass(frozen=True)
class Entity:
    title: str
    x: float
    y: float
    fields: tuple[Field, ...]
    width: float = 300.0

    @property
    def height(self) -> float:
        return 24.0 + len(self.fields) * 13.5 + 8.0

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2


ENTITIES = {
    "categories": Entity(
        "categories",
        50,
        80,
        (
            Field("category_id", "INTEGER", "PK"),
            Field("category_name", "VARCHAR(100)"),
        ),
    ),
    "subcategories": Entity(
        "subcategories",
        50,
        165,
        (
            Field("subcategory_id", "INTEGER", "PK"),
            Field("subcategory_name", "VARCHAR(100)"),
        ),
    ),
    "manufacturers": Entity(
        "manufacturers",
        50,
        250,
        (
            Field("manufacturer_id", "INTEGER", "PK"),
            Field("manufacturer_name", "VARCHAR(100)"),
        ),
    ),
    "roles": Entity(
        "roles",
        50,
        340,
        (
            Field("role_id", "INTEGER", "PK"),
            Field("role_code", "VARCHAR(20)"),
            Field("role_name", "VARCHAR(50)"),
        ),
    ),
    "users": Entity(
        "users",
        50,
        445,
        (
            Field("user_id", "INTEGER", "PK"),
            Field("login", "VARCHAR(50)"),
            Field("last_name", "VARCHAR(100)"),
            Field("first_name", "VARCHAR(100)"),
            Field("middle_name", "VARCHAR(100)"),
            Field("role_id", "INTEGER", "FK"),
        ),
    ),
    "orders": Entity(
        "orders",
        50,
        590,
        (
            Field("order_id", "INTEGER", "PK"),
            Field("order_date", "TIMESTAMP"),
            Field("user_id", "INTEGER", "FK"),
        ),
    ),
    "order_items": Entity(
        "order_items",
        50,
        695,
        (
            Field("order_item_id", "INTEGER", "PK"),
            Field("order_id", "INTEGER", "FK"),
            Field("stock_item_id", "INTEGER", "FK"),
            Field("quantity", "INTEGER"),
            Field("unit_price", "NUMERIC(12,2)"),
        ),
    ),
    "products": Entity(
        "products",
        430,
        80,
        (
            Field("product_id", "INTEGER", "PK"),
            Field("article", "VARCHAR(20)"),
            Field("category_id", "INTEGER", "FK"),
            Field("subcategory_id", "INTEGER", "FK"),
            Field("manufacturer_id", "INTEGER", "FK"),
            Field("name", "VARCHAR(200)"),
            Field("image_path", "VARCHAR(300)"),
            Field("material", "VARCHAR(200)"),
            Field("description", "TEXT"),
            Field("price", "NUMERIC(12,2)"),
        ),
        width=320.0,
    ),
    "variants": Entity(
        "variants",
        430,
        300,
        (
            Field("variant_id", "INTEGER", "PK"),
            Field("variant_name", "VARCHAR(100)"),
        ),
        width=320.0,
    ),
    "stock_items": Entity(
        "stock_items",
        430,
        395,
        (
            Field("stock_item_id", "INTEGER", "PK"),
            Field("product_id", "INTEGER", "FK"),
            Field("variant_id", "INTEGER", "FK"),
            Field("quantity", "INTEGER"),
        ),
        width=320.0,
    ),
}


def draw_entity(painter: QPainter, entity: Entity) -> None:
    header = QRectF(entity.left, entity.top, entity.width, 24.0)
    body = QRectF(
        entity.left, entity.top + 24.0, entity.width, entity.height - 24.0
    )

    painter.setPen(QPen(BORDER, 1.0))
    painter.setBrush(PRIMARY)
    painter.drawRect(header)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRect(body)

    title_font = QFont("Calibri", 9)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(
        header.adjusted(6, 0, -6, 0),
        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
        entity.title,
    )

    field_font = QFont("Calibri", 7.5)
    painter.setFont(field_font)
    for index, field in enumerate(entity.fields):
        row_top = body.top() + 3.0 + index * 13.5
        row = QRectF(entity.left + 6.0, row_top, entity.width - 12.0, 13.5)
        painter.setPen(TEXT)
        prefix = f"{field.key} " if field.key else ""
        painter.drawText(
            row,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f"{prefix}{field.name}",
        )
        painter.setPen(MUTED)
        painter.drawText(
            row,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            field.data_type,
        )


def draw_label(painter: QPainter, point: QPointF, text: str) -> None:
    font = QFont("Calibri", 7.5)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(MUTED)
    painter.drawText(
        QRectF(point.x() - 10.0, point.y() - 7.0, 20.0, 14.0),
        Qt.AlignmentFlag.AlignCenter,
        text,
    )


def _point_at_fraction(
    points: list[QPointF], fraction: float
) -> tuple[QPointF, QPointF]:
    """Возвращает точку на ломаной и направление сегмента в этой точке."""
    lengths: list[float] = []
    total = 0.0
    for start, end in zip(points, points[1:]):
        length = ((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2) ** 0.5
        lengths.append(length)
        total += length
    if total == 0.0:
        return points[0], QPointF(1, 0)

    target = total * fraction
    passed = 0.0
    for (start, end), length in zip(zip(points, points[1:]), lengths):
        if passed + length >= target or length == 0.0:
            local = 0.0 if length == 0.0 else (target - passed) / length
            point = QPointF(
                start.x() + (end.x() - start.x()) * local,
                start.y() + (end.y() - start.y()) * local,
            )
            return point, QPointF(end.x() - start.x(), end.y() - start.y())
        passed += length
    return points[-1], QPointF(1, 0)


def draw_path_label(
    painter: QPainter, points: list[QPointF], fraction: float, text: str
) -> None:
    point, direction = _point_at_fraction(points, fraction)
    length = max((direction.x() ** 2 + direction.y() ** 2) ** 0.5, 1.0)
    perp_x = -direction.y() / length
    perp_y = direction.x() / length
    draw_label(
        painter,
        QPointF(point.x() + perp_x * 9.0, point.y() + perp_y * 9.0),
        text,
    )


def draw_line(
    painter: QPainter, points: list[QPointF], start_label: str = "", end_label: str = ""
) -> None:
    painter.setPen(QPen(BORDER, 1.2))
    for start, end in zip(points, points[1:]):
        painter.drawLine(start, end)
    if start_label and len(points) >= 2:
        draw_path_label(painter, points, 0.3, start_label)
    if end_label and len(points) >= 2:
        draw_path_label(painter, points, 0.7, end_label)


def draw_legend(painter: QPainter) -> None:
    box = QRectF(820, 80, 330, 235)
    painter.setPen(QPen(BORDER, 1.0))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRect(box)

    font = QFont("Calibri", 9)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(TEXT)
    painter.drawText(
        QRectF(box.left() + 12, box.top() + 8, box.width() - 24, 20),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "Условные обозначения",
    )

    body_font = QFont("Calibri", 8)
    painter.setFont(body_font)
    lines = (
        "PK — первичный ключ",
        "FK — внешний ключ",
        "1 — одна запись",
        "N — много записей",
        "Связи реализованы внешними ключами",
        "с ограничениями ON DELETE RESTRICT/CASCADE.",
    )
    y = box.top() + 38
    for line in lines:
        painter.setPen(MUTED)
        painter.drawText(
            QRectF(box.left() + 12, y, box.width() - 24, 16),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            line,
        )
        y += 18

    # Пример связи 1:N.
    painter.setPen(QPen(BORDER, 1.2))
    painter.drawLine(QPointF(box.left() + 20, y + 18), QPointF(box.left() + 110, y + 18))
    draw_label(painter, QPointF(box.left() + 20, y + 18), "1")
    draw_label(painter, QPointF(box.left() + 110, y + 18), "N")
    painter.setFont(body_font)
    painter.setPen(MUTED)
    painter.drawText(
        QRectF(box.left() + 122, y + 8, 190, 20),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "направление «один ко многим»",
    )


def draw_notes(painter: QPainter) -> None:
    box = QRectF(820, 335, 330, 250)
    painter.setPen(QPen(BORDER, 1.0))
    painter.setBrush(SECONDARY)
    painter.drawRect(box)

    title_font = QFont("Calibri", 9)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(TEXT)
    painter.drawText(
        QRectF(box.left() + 12, box.top() + 8, box.width() - 24, 20),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "Ограничения целостности",
    )

    body_font = QFont("Calibri", 8)
    painter.setFont(body_font)
    notes = (
        "• login, article, названия справочников — UNIQUE;",
        "• quantity >= 0 в stock_items;",
        "• quantity > 0 и unit_price >= 0 в order_items;",
        "• price >= 0 в products;",
        "• удаление заказа каскадно удаляет его позиции;",
        "• удаление справочников и товаров, на которые",
        "  ссылаются заказы, запрещено (RESTRICT);",
        "• сумма заказа вычисляется как сумма",
        "  quantity × unit_price по позициям.",
    )
    y = box.top() + 38
    for note in notes:
        painter.setPen(TEXT)
        painter.drawText(
            QRectF(box.left() + 12, y, box.width() - 24, 16),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            note,
        )
        y += 17


def draw_relationships(painter: QPainter) -> None:
    box = QRectF(820, 600, 330, 185)
    painter.setPen(QPen(BORDER, 1.0))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRect(box)

    title_font = QFont("Calibri", 9)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(TEXT)
    painter.drawText(
        QRectF(box.left() + 12, box.top() + 8, box.width() - 24, 20),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "Основные связи",
    )

    body_font = QFont("Calibri", 8)
    painter.setFont(body_font)
    relations = (
        "roles 1 — N users",
        "users 1 — N orders",
        "orders 1 — N order_items",
        "products 1 — N stock_items",
        "variants 1 — N stock_items",
        "stock_items 1 — N order_items",
        "categories / subcategories / manufacturers 1 — N products",
    )
    y = box.top() + 38
    for relation in relations:
        painter.setPen(MUTED)
        painter.drawText(
            QRectF(box.left() + 12, y, box.width() - 24, 17),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            relation,
        )
        y += 19


def build_pdf() -> Path:
    writer = QPdfWriter(str(OUTPUT_PATH))
    writer.setResolution(72)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A3))
    writer.setPageOrientation(QPageLayout.Orientation.Landscape)
    writer.setPageMargins(QMarginsF(0, 0, 0, 0))

    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.fillRect(
        QRectF(0, 0, PAGE_WIDTH, PAGE_HEIGHT), QColor("#FFFFFF")
    )

    title_font = QFont("Calibri", 16)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(TEXT)
    painter.drawText(
        QRectF(50, 22, 800, 28),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "ER-диаграмма базы данных «ФормаДесерт»",
    )

    subtitle_font = QFont("Calibri", 9)
    painter.setFont(subtitle_font)
    painter.setPen(MUTED)
    painter.drawText(
        QRectF(50, 50, 800, 20),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "PostgreSQL 18 · схема public · 3-я нормальная форма",
    )

    for entity in ENTITIES.values():
        draw_entity(painter, entity)

    categories = ENTITIES["categories"]
    subcategories = ENTITIES["subcategories"]
    manufacturers = ENTITIES["manufacturers"]
    roles = ENTITIES["roles"]
    users = ENTITIES["users"]
    orders = ENTITIES["orders"]
    order_items = ENTITIES["order_items"]
    products = ENTITIES["products"]
    variants = ENTITIES["variants"]
    stock_items = ENTITIES["stock_items"]

    # Справочники → products.
    draw_line(
        painter,
        [
            QPointF(categories.right, categories.center_y),
            QPointF(products.left, categories.center_y),
        ],
        "1",
        "N",
    )
    draw_line(
        painter,
        [
            QPointF(subcategories.right, subcategories.center_y),
            QPointF(385, subcategories.center_y),
            QPointF(385, products.top + 90),
            QPointF(products.left, products.top + 90),
        ],
        "1",
        "N",
    )
    draw_line(
        painter,
        [
            QPointF(manufacturers.right, manufacturers.center_y),
            QPointF(400, manufacturers.center_y),
            QPointF(400, products.top + 125),
            QPointF(products.left, products.top + 125),
        ],
        "1",
        "N",
    )

    # Роли → пользователи → заказы → позиции заказов.
    draw_line(
        painter,
        [
            QPointF(roles.left + 70, roles.bottom),
            QPointF(roles.left + 70, users.top),
        ],
        "1",
        "N",
    )
    draw_line(
        painter,
        [
            QPointF(users.left + 70, users.bottom),
            QPointF(users.left + 70, orders.top),
        ],
        "1",
        "N",
    )
    draw_line(
        painter,
        [
            QPointF(orders.left + 70, orders.bottom),
            QPointF(orders.left + 70, order_items.top),
        ],
        "1",
        "N",
    )

    # products и variants → stock_items. Линия от products обходит variants
    # слева, чтобы не пересекать её прямоугольник.
    draw_line(
        painter,
        [
            QPointF(products.left, products.bottom - 10),
            QPointF(415, products.bottom - 10),
            QPointF(415, stock_items.top + 18),
            QPointF(stock_items.left, stock_items.top + 18),
        ],
        "1",
        "N",
    )
    draw_line(
        painter,
        [
            QPointF(variants.left + 220, variants.bottom),
            QPointF(variants.left + 220, stock_items.top),
        ],
        "1",
        "N",
    )

    # stock_items → order_items: обход снизу, вне прямоугольников.
    draw_line(
        painter,
        [
            QPointF(stock_items.left + 40, stock_items.bottom),
            QPointF(stock_items.left + 40, order_items.center_y),
            QPointF(order_items.right, order_items.center_y),
        ],
        "1",
        "N",
    )

    draw_legend(painter)
    draw_notes(painter)
    draw_relationships(painter)

    footer_font = QFont("Calibri", 8)
    painter.setFont(footer_font)
    painter.setPen(MUTED)
    painter.drawText(
        QRectF(50, PAGE_HEIGHT - 30, 800, 16),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        "ФормаДесерт · схема создана в рамках модуля 1, используется приложением "
        "модулей 2–4",
    )

    painter.end()
    return OUTPUT_PATH


def main() -> None:
    app = QGuiApplication([])
    for font_file in ("calibri.ttf", "calibrib.ttf"):
        font_path = Path("C:/Windows/Fonts") / font_file
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))
    app.setFont(QFont("Calibri", 9))
    path = build_pdf()
    print(f"ER-диаграмма сохранена: {path}")


if __name__ == "__main__":
    main()

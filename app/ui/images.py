"""Загрузка изображений товаров с подстановкой заглушки."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from app.config import IMAGES_DIR, PLACEHOLDER_PATH


def resolve_image_path(image_path: str | None) -> Path:
    """Возвращает существующий файл изображения или picture.png."""
    if image_path:
        raw = Path(image_path)
        candidate = raw if raw.is_absolute() else IMAGES_DIR / raw.name
        if candidate.is_file():
            return candidate
    return PLACEHOLDER_PATH


def load_product_pixmap(image_path: str | None, width: int, height: int) -> QPixmap:
    """Загружает изображение и вписывает его в заданную область без искажений."""
    pixmap = QPixmap(str(resolve_image_path(image_path)))
    if pixmap.isNull():
        pixmap = QPixmap(str(PLACEHOLDER_PATH))
    return pixmap.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

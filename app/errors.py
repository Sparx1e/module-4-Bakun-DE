"""Исключения приложения.

Все ожидаемые ошибки наследуются от AppError, поэтому интерфейс может
показывать пользователю понятное сообщение вместо аварийного завершения.
"""

from __future__ import annotations


class AppError(Exception):
    """Базовая ожидаемая ошибка приложения."""

    title = "Ошибка"


class ValidationError(AppError):
    """Некорректные данные, введённые пользователем."""

    title = "Ошибка ввода"


class AuthenticationError(AppError):
    """Неудачная попытка входа в систему."""

    title = "Ошибка авторизации"


class AccessDeniedError(AppError):
    """Действие запрещено для роли пользователя."""

    title = "Доступ запрещён"


class NotFoundError(AppError):
    """Запрошенная запись отсутствует в базе данных."""

    title = "Запись не найдена"


class StockError(AppError):
    """Недостаточно товара на складе."""

    title = "Недостаточно товара"


class DatabaseError(AppError):
    """Ошибка подключения или выполнения запроса к PostgreSQL."""

    title = "Ошибка базы данных"


class DatabaseUnavailableError(DatabaseError):
    """Не удалось установить соединение с PostgreSQL."""

    title = "Нет подключения к базе данных"

from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
import psycopg
from psycopg import Cursor
from psycopg.rows import dict_row
from app.config import DbSettings
from app.errors import DatabaseError, DatabaseUnavailableError


class Database:
    """Небольшая обёртка над соединением psycopg.

    Соединение создаётся один раз и переиспользуется. Если оно потеряно,
    следующий запрос попытается подключиться заново.
    """

    def __init__(self, settings: DbSettings) -> None:
        self._settings = settings
        self._connection: psycopg.Connection | None = None

    @property
    def settings(self) -> DbSettings:
        return self._settings

    def connect(self) -> None:
        """Устанавливает соединение или сообщает понятную ошибку."""
        try:
            self._connection = psycopg.connect(
                host=self._settings.host,
                port=self._settings.port,
                dbname=self._settings.dbname,
                user=self._settings.user,
                password=self._settings.password,
                connect_timeout=5,
                row_factory=dict_row, # type: ignore
            )
        except psycopg.Error as exc:
            raise DatabaseUnavailableError(
                "Не удалось подключиться к базе данных PostgreSQL.\n\n"
                f"Параметры подключения: {self._settings.describe()}\n"
                "Проверьте, что сервер PostgreSQL запущен, база данных создана, "
                "а значения PGHOST, PGPORT, PGDATABASE, PGUSER и PGPASSWORD заданы верно.\n\n"
                f"Техническая информация: {exc}"
            ) from exc

    def close(self) -> None:
        if self._connection is not None and not self._connection.closed:
            self._connection.close()
        self._connection = None

    def _ensure_connection(self) -> psycopg.Connection:
        if self._connection is None or self._connection.closed:
            self.connect()
        assert self._connection is not None
        return self._connection

    def _handle_error(self, exc: psycopg.Error) -> DatabaseError:
        if isinstance(exc, psycopg.OperationalError):
            self.close()
            return DatabaseUnavailableError(
                "Соединение с базой данных потеряно. Проверьте работу сервера PostgreSQL "
                "и повторите операцию.\n\n"
                f"Техническая информация: {exc}"
            )
        return DatabaseError(
            "Не удалось выполнить операцию с базой данных. Изменения не сохранены.\n\n"
            f"Техническая информация: {exc}"
        )

    @contextmanager
    def cursor(self) -> Iterator[Cursor]:
        """Курсор для чтения; фиксирует изменения при успешном выходе."""
        connection = self._ensure_connection()
        try:
            with connection.cursor() as cursor:
                yield cursor
            connection.commit()
        except psycopg.Error as exc:
            connection.rollback()
            raise self._handle_error(exc) from exc

    @contextmanager
    def transaction(self) -> Iterator[Cursor]:
        """Единая транзакция: либо сохраняются все изменения, либо ни одного."""
        connection = self._ensure_connection()
        try:
            with connection.transaction():
                with connection.cursor() as cursor:
                    yield cursor
        except psycopg.Error as exc:
            raise self._handle_error(exc) from exc

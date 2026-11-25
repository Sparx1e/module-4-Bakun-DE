"""Доступ к пользователям и ролям."""

from __future__ import annotations

from app.db.connection import Database
from app.models.entities import User

_FIND_USER_SQL = """
SELECT u.user_id,
       u.login,
       u.last_name,
       u.first_name,
       u.middle_name,
       r.role_code,
       r.role_name
FROM users u
JOIN roles r ON r.role_id = u.role_id
WHERE lower(u.login) = lower(%s)
"""

_LIST_CLIENTS_SQL = """
SELECT u.user_id,
       u.login,
       u.last_name,
       u.first_name,
       u.middle_name,
       r.role_code,
       r.role_name
FROM users u
JOIN roles r ON r.role_id = u.role_id
WHERE r.role_code = 'client'
ORDER BY u.last_name, u.first_name, u.middle_name
"""


class AuthRepository:
    """Поиск пользователя по логину без пароля (требование задания)."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def find_by_login(self, login: str) -> User | None:
        with self._database.cursor() as cursor:
            cursor.execute(_FIND_USER_SQL, (login,))
            row = cursor.fetchone()
        return self._to_user(row) if row else None

    def list_clients(self) -> list[User]:
        with self._database.cursor() as cursor:
            cursor.execute(_LIST_CLIENTS_SQL)
            rows = cursor.fetchall()
        return [self._to_user(row) for row in rows]

    @staticmethod
    def _to_user(row: dict) -> User:
        return User(
            user_id=row["user_id"],
            login=row["login"],
            last_name=row["last_name"],
            first_name=row["first_name"],
            middle_name=row["middle_name"],
            role_code=row["role_code"],
            role_name=row["role_name"],
        )

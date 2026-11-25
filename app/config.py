from __future__ import annotations
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    APP_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    APP_DIR = BASE_DIR

RESOURCES_DIR = BASE_DIR / "resources"
IMAGES_DIR = RESOURCES_DIR / "images"
LOGO_PATH = RESOURCES_DIR / "logo.png"
ICON_PATH = RESOURCES_DIR / "app.ico"
PLACEHOLDER_PATH = IMAGES_DIR / "picture.png"

APP_NAME = "ФормаДесерт"
APP_TITLE = "ФормаДесерт — магазин кондитерских принадлежностей"

DISCOUNT_REFERENCE_DATE = date(2026, 10, 20)
DISCOUNT_PERCENT = 25


def _load_dotenv() -> None:
    env_path = APP_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class DbSettings:
    """Параметры подключения к PostgreSQL (без паролей в коде)."""

    host: str
    port: int
    dbname: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DbSettings":
        _load_dotenv()
        return cls(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            dbname=os.getenv("PGDATABASE", "formadessert"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", "123"),
        )

    def describe(self) -> str:
        """Безопасное описание подключения для сообщений об ошибке."""
        return f"{self.user}@{self.host}:{self.port}/{self.dbname}"

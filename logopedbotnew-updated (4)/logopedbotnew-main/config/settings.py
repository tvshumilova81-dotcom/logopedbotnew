from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Централизованная конфигурация проекта. Значения читаются из .env"""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str
    ADMIN_IDS: str = ""

    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'bot.db'}"

    INSTAGRAM_URL: str = "https://instagram.com/"
    TELEGRAM_CHANNEL_URL: str = "https://t.me/"

    TIMEZONE: str = "Europe/Moscow"
    LOG_LEVEL: str = "INFO"
    THROTTLE_RATE_LIMIT: float = 0.7

    # === Webhook (для деплоя на Render и т.п.) ===
    # Если WEBHOOK_URL не задан — бот работает через polling (локальная разработка).
    # Если задан — бот поднимает aiohttp-сервер и слушает вебхуки от Telegram.
    WEBHOOK_URL: str = ""  # например: https://logoped-bot.onrender.com
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_SECRET: str = ""  # произвольная строка для проверки запросов от Telegram
    PORT: int = 8000  # Render сам подставит свой PORT через переменную окружения

    # === Мини-приложение (Telegram Mini App) ===
    # Публичный адрес мини-аппа, например: https://logoped-bot.onrender.com/webapp/
    # Если не задан — кнопка мини-приложения не показывается.
    WEBAPP_URL: str = ""

    @property
    def use_webhook(self) -> bool:
        return bool(self.WEBHOOK_URL)

    @property
    def admin_ids(self) -> list[int]:
        result: list[int] = []
        for chunk in self.ADMIN_IDS.split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                result.append(int(chunk))
        return result


settings = Settings()

ARTICLES_DIR = BASE_DIR / "articles"
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = BASE_DIR / "media"
MATERIALS_DIR = MEDIA_DIR / "materials"
COVERS_DIR = MEDIA_DIR / "covers"
LOGS_DIR = BASE_DIR / "logs"
FAQ_FILE = DATA_DIR / "faq.json"

for path in (DATA_DIR, MEDIA_DIR, MATERIALS_DIR, COVERS_DIR, LOGS_DIR):
    path.mkdir(parents=True, exist_ok=True)

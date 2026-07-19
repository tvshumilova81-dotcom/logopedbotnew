from __future__ import annotations

import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config.settings import settings
from database.engine import init_db
from handlers import about, booking, contacts, faq, materials, price_guard, profile, purchases, questionnaire, start
from handlers.admin import admin_router
from middlewares.db import DbSessionMiddleware
from middlewares.logging import ErrorLoggingMiddleware
from middlewares.throttling import ThrottlingMiddleware
from services.seed import seed_default_materials
from utils.logger import setup_logging

logger = logging.getLogger("bot.main")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares (порядок важен: логирование ошибок -> антиспам -> сессия БД)
    dp.update.middleware(ErrorLoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.update.middleware(DbSessionMiddleware())

    # Роутеры. Админский роутер регистрируем первым, чтобы админ-команды
    # (например /stats, /broadcast) не перехватывались общими хендлерами.
    dp.include_router(admin_router)
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(questionnaire.router)
    dp.include_router(about.router)
    dp.include_router(materials.router)
    dp.include_router(purchases.router)
    dp.include_router(faq.router)
    dp.include_router(profile.router)
    dp.include_router(contacts.router)
    dp.include_router(price_guard.router)  # держим последним — это "поймай всё" фильтр

    return dp


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущен в режиме polling")
    await dp.start_polling(bot)


async def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    webhook_url = settings.WEBHOOK_URL.rstrip("/") + settings.WEBHOOK_PATH

    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )
    logger.info("Бот запущен в режиме webhook: %s", webhook_url)

    app = web.Application()

    async def health(_request: web.Request) -> web.Response:
        # Render дёргает "/", чтобы понять, что сервис жив
        return web.Response(text="ok")

    app.router.add_get("/", health)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET or None,
    ).register(app, path=settings.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    port = int(os.environ.get("PORT", settings.PORT))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

    logger.info("HTTP-сервер слушает порт %s", port)

    # Держим процесс живым
    await asyncio.Event().wait()


async def main() -> None:
    setup_logging()
    logger.info("Запуск бота...")

    await init_db()
    await seed_default_materials()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    if settings.use_webhook:
        await run_webhook(bot, dp)
    else:
        await run_polling(bot, dp)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger("bot.main").info("Бот остановлен")

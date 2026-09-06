from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import BASE_DIR
from filters.admin import IsAdmin
from services.export_service import export_all

router = Router(name="admin_export")
router.message.filter(IsAdmin())

EXPORT_DIR = BASE_DIR / "data" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@router.message(Command("export"))
async def export_data(message: Message, session: AsyncSession) -> None:
    await message.answer("⏳ Формирую Excel-файл со всеми данными...")
    filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = EXPORT_DIR / filename
    await export_all(session, path)
    await message.answer_document(
        FSInputFile(path), caption="📄 Экспорт: пользователи, заявки, анкеты, покупки."
    )

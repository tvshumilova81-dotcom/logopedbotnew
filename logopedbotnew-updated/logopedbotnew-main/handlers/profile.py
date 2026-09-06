from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.main_menu import MENU_PROFILE
from services.booking_service import latest_booking_for_user
from services.material_service import user_purchased_material_ids
from services.questionnaire_service import latest_questionnaire_for_user
from services.user_service import get_user_by_telegram_id

router = Router(name="profile")

STATUS_LABELS = {
    "new": "🆕 Новая",
    "accepted": "✅ Принята",
    "cancelled": "❌ Отменена",
}


@router.message(F.text == MENU_PROFILE)
async def show_profile(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Профиль не найден. Отправьте /start")
        return

    booking = await latest_booking_for_user(session, user.id)
    questionnaire = await latest_questionnaire_for_user(session, user.id)
    purchases_count = len(await user_purchased_material_ids(session, user.id))

    text = (
        "👤 <b>Мой профиль</b>\n\n"
        f"Имя родителя: {user.parent_name or '—'}\n"
        f"Имя ребёнка: {user.child_name or '—'}\n"
        f"Возраст ребёнка: {user.child_age or '—'}\n"
        f"Страна: {user.country or '—'}\n"
        f"Часовой пояс: {user.timezone or '—'}\n"
        f"Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}\n"
        f"Дата записи: {booking.created_at.strftime('%d.%m.%Y') if booking else '—'}\n"
        f"Статус заявки: {STATUS_LABELS.get(booking.status.value, '—') if booking else '—'}\n"
        f"Анкета заполнена: {'✅ Да' if questionnaire else '❌ Нет'}\n"
        f"Куплено материалов: {purchases_count}"
    )
    await message.answer(text)

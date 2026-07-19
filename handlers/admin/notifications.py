from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.booking import BookingStatus
from filters.admin import IsAdmin
from services.booking_service import delete_booking, get_booking, set_booking_status
from services.notify_admin import format_questionnaire
from services.questionnaire_service import get_questionnaire, latest_questionnaire_for_user
from services.user_service import get_user_by_id

router = Router(name="admin_notifications")
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data.startswith("booking_accept:"))
async def accept_booking(callback: CallbackQuery, session: AsyncSession) -> None:
    booking_id = int(callback.data.split(":", 1)[1])
    await set_booking_status(session, booking_id, BookingStatus.ACCEPTED)
    await callback.message.edit_text(callback.message.text + "\n\n✅ <b>Принято</b>")
    await callback.answer("Заявка отмечена как принятая")


@router.callback_query(F.data.startswith("booking_delete:"))
async def delete_booking_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    booking_id = int(callback.data.split(":", 1)[1])
    await delete_booking(session, booking_id)
    await callback.message.edit_text(callback.message.text + "\n\n🗑 <b>Заявка удалена</b>")
    await callback.answer("Заявка удалена")


@router.callback_query(F.data.startswith("booking_open_q:"))
async def open_questionnaire_from_booking(callback: CallbackQuery, session: AsyncSession) -> None:
    booking_id = int(callback.data.split(":", 1)[1])
    booking = await get_booking(session, booking_id)
    if not booking:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    questionnaire = await latest_questionnaire_for_user(session, booking.user_id)
    if not questionnaire:
        await callback.answer("Анкета ещё не заполнена", show_alert=True)
        return
    user = await get_user_by_id(session, booking.user_id)
    await callback.message.answer(format_questionnaire(user, questionnaire))
    await callback.answer()


@router.callback_query(F.data.startswith("booking_profile:"))
async def open_profile_from_booking(callback: CallbackQuery, session: AsyncSession) -> None:
    booking_id = int(callback.data.split(":", 1)[1])
    booking = await get_booking(session, booking_id)
    if not booking:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    user = await get_user_by_id(session, booking.user_id)
    text = (
        f"👤 <b>Профиль пользователя</b>\n\n"
        f"Родитель: {user.parent_name or '—'}\n"
        f"Ребёнок: {user.child_name or '—'}\n"
        f"Страна: {user.country or '—'}\n"
        f"Telegram ID: {user.telegram_id}\n"
        f"Username: @{user.username if user.username else '—'}\n"
        f"Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}"
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("q_view:"))
async def view_questionnaire(callback: CallbackQuery, session: AsyncSession) -> None:
    questionnaire_id = int(callback.data.split(":", 1)[1])
    questionnaire = await get_questionnaire(session, questionnaire_id)
    if not questionnaire:
        await callback.answer("Анкета не найдена", show_alert=True)
        return
    user = await get_user_by_id(session, questionnaire.user_id)
    await callback.message.answer(format_questionnaire(user, questionnaire))
    await callback.answer()

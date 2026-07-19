import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from filters.admin import IsAdmin
from keyboards.admin import broadcast_confirm_keyboard
from services.user_service import all_users
from states.admin import BroadcastForm

router = Router(name="admin_broadcast")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BroadcastForm.waiting_content)
    await message.answer(
        "📢 Введите сообщение для рассылки.\n\n"
        "Можно отправить текст, фото, видео или документ (с подписью). "
        "Поддерживаются кнопки — просто добавьте ссылки в текст."
    )


@router.message(BroadcastForm.waiting_content)
async def receive_broadcast_content(message: Message, state: FSMContext) -> None:
    await state.update_data(message_id=message.message_id, chat_id=message.chat.id)
    await state.set_state(BroadcastForm.confirm)
    await message.answer(
        "Отправить это сообщение всем зарегистрированным пользователям?",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(BroadcastForm.confirm, F.data == "broadcast:confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    users = await all_users(session)
    await callback.message.edit_reply_markup()
    await callback.message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")

    sent, failed = 0, 0
    for user in users:
        try:
            await callback.bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=data["chat_id"],
                message_id=data["message_id"],
            )
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # мягкое ограничение скорости отправки

    await callback.message.answer(f"✅ Рассылка завершена.\nДоставлено: {sent}\nОшибок: {failed}")
    await state.clear()
    await callback.answer()


@router.callback_query(BroadcastForm.confirm, F.data == "broadcast:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup()
    await callback.message.answer("❌ Рассылка отменена.")
    await callback.answer()

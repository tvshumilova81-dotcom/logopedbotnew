from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.booking import booking_confirm_keyboard, gender_keyboard
from keyboards.countries import countries_keyboard, country_by_index, OTHER_COUNTRY
from keyboards.main_menu import MENU_BOOKING, main_menu_keyboard
from services.booking_service import create_booking
from services.notify_admin import notify_new_booking
from services.user_service import get_user_by_telegram_id
from states.booking import BookingForm

router = Router(name="booking")


@router.message(F.text == MENU_BOOKING)
@router.message(F.text == "/book")
async def start_booking(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BookingForm.parent_name)
    await message.answer(
        "📝 Начинаем запись на занятие.\n\nКак вас зовут? (имя родителя)"
    )


@router.message(BookingForm.parent_name)
async def process_parent_name(message: Message, state: FSMContext) -> None:
    await state.update_data(parent_name=message.text)
    await state.set_state(BookingForm.child_name)
    await message.answer("Как зовут ребёнка?")


@router.message(BookingForm.child_name)
async def process_child_name(message: Message, state: FSMContext) -> None:
    await state.update_data(child_name=message.text)
    await state.set_state(BookingForm.child_age)
    await message.answer("Сколько лет ребёнку?")


@router.message(BookingForm.child_age)
async def process_child_age(message: Message, state: FSMContext) -> None:
    await state.update_data(child_age=message.text)
    await state.set_state(BookingForm.child_gender)
    await message.answer("Пол ребёнка?", reply_markup=gender_keyboard())


@router.callback_query(BookingForm.child_gender, F.data.startswith("gender:"))
async def process_child_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = "Мальчик" if callback.data.endswith("boy") else "Девочка"
    await state.update_data(child_gender=gender)
    await state.set_state(BookingForm.country)
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "Из какой страны вы будете заниматься?", reply_markup=countries_keyboard()
    )
    await callback.answer()


@router.callback_query(BookingForm.country, F.data.startswith("country:"))
async def process_country(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    await callback.message.edit_reply_markup()
    if value == "other":
        await state.set_state(BookingForm.country_manual)
        await callback.message.answer("Напишите название вашей страны:")
        await callback.answer()
        return
    country = country_by_index(int(value)) or OTHER_COUNTRY
    await state.update_data(country=country)
    await state.set_state(BookingForm.timezone)
    await callback.message.answer("Какой у вас часовой пояс? (например, UTC+2)")
    await callback.answer()


@router.message(BookingForm.country_manual)
async def process_country_manual(message: Message, state: FSMContext) -> None:
    await state.update_data(country=message.text)
    await state.set_state(BookingForm.timezone)
    await message.answer("Какой у вас часовой пояс? (например, UTC+2)")


@router.message(BookingForm.timezone)
async def process_timezone(message: Message, state: FSMContext) -> None:
    await state.update_data(timezone=message.text)
    await state.set_state(BookingForm.problem)
    await message.answer("Какая проблема с речью у ребёнка?")


@router.message(BookingForm.problem)
async def process_problem(message: Message, state: FSMContext) -> None:
    await state.update_data(problem=message.text)
    await state.set_state(BookingForm.concern)
    await message.answer("Что вас беспокоит больше всего?")


@router.message(BookingForm.concern)
async def process_concern(message: Message, state: FSMContext) -> None:
    await state.update_data(concern=message.text)
    await state.set_state(BookingForm.noticed_since)
    await message.answer("Когда вы впервые заметили трудности?")


@router.message(BookingForm.noticed_since)
async def process_noticed_since(message: Message, state: FSMContext) -> None:
    await state.update_data(noticed_since=message.text)
    await state.set_state(BookingForm.saw_speech_therapist)
    await message.answer("Был ли ребёнок у логопеда? (напишите да/нет и подробности)")


@router.message(BookingForm.saw_speech_therapist)
async def process_saw_speech_therapist(message: Message, state: FSMContext) -> None:
    await state.update_data(saw_speech_therapist=message.text)
    await state.set_state(BookingForm.specialists_reports)
    await message.answer("Есть ли заключения других специалистов? Если да — какие.")


@router.message(BookingForm.specialists_reports)
async def process_specialists_reports(message: Message, state: FSMContext) -> None:
    await state.update_data(specialists_reports=message.text)
    await state.set_state(BookingForm.convenient_days)
    await message.answer("В какие дни вам удобно заниматься?")


@router.message(BookingForm.convenient_days)
async def process_convenient_days(message: Message, state: FSMContext) -> None:
    await state.update_data(convenient_days=message.text)
    await state.set_state(BookingForm.convenient_time)
    await message.answer("В какое время вам удобно заниматься?")


@router.message(BookingForm.convenient_time)
async def process_convenient_time(message: Message, state: FSMContext) -> None:
    await state.update_data(convenient_time=message.text)
    data = await state.get_data()

    card = (
        "🧾 <b>Проверьте данные заявки</b>\n\n"
        f"👤 Родитель: {data.get('parent_name')}\n"
        f"👶 Ребёнок: {data.get('child_name')}\n"
        f"🎂 Возраст: {data.get('child_age')}\n"
        f"⚧️ Пол: {data.get('child_gender')}\n"
        f"🌍 Страна: {data.get('country')}\n"
        f"🕒 Часовой пояс: {data.get('timezone')}\n"
        f"🗣 Проблема: {data.get('problem')}\n"
        f"😟 Беспокоит: {data.get('concern')}\n"
        f"🗓 Заметили с: {data.get('noticed_since')}\n"
        f"📚 Был у логопеда: {data.get('saw_speech_therapist')}\n"
        f"📄 Заключения специалистов: {data.get('specialists_reports')}\n"
        f"📅 Удобные дни: {data.get('convenient_days')}\n"
        f"⏰ Удобное время: {data.get('convenient_time')}\n\n"
        "Подтвердить запись?"
    )
    await state.set_state(BookingForm.confirm)
    await message.answer(card, reply_markup=booking_confirm_keyboard())


@router.callback_query(BookingForm.confirm, F.data == "booking_confirm:yes")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    user = await get_user_by_telegram_id(session, callback.from_user.id)

    user.parent_name = data.get("parent_name")
    user.child_name = data.get("child_name")
    user.child_age = data.get("child_age")
    user.child_gender = data.get("child_gender")
    user.country = data.get("country")
    user.timezone = data.get("timezone")
    await session.commit()

    booking_data = {k: v for k, v in data.items() if k not in ("confirm",)}
    booking = await create_booking(session, user.id, booking_data)

    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "✅ Спасибо! Ваша заявка принята.\n\n"
        "Я свяжусь с вами в ближайшее время, чтобы согласовать детали занятия.\n\n"
        "Вы также можете заполнить 📋 «Анкету ребёнка» — это поможет мне лучше "
        "подготовиться к первому занятию.",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()

    await notify_new_booking(callback.bot, user, booking)
    await callback.answer()


@router.callback_query(BookingForm.confirm, F.data == "booking_confirm:restart")
async def restart_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup()
    await start_booking(callback.message, state)
    await callback.answer()

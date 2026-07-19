from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.main_menu import MENU_QUESTIONNAIRE, main_menu_keyboard
from keyboards.yes_no import ANSWER_LABELS, yes_no_keyboard, yes_no_partially_keyboard
from services.notify_admin import notify_questionnaire_filled
from services.questionnaire_service import create_questionnaire
from services.user_service import get_user_by_telegram_id
from states.questionnaire import QuestionnaireForm

router = Router(name="questionnaire")

# (state, field, question text, kind)
# kind: "text" | "yn3" (да/нет/частично) | "yn2" (да/нет)
STEPS: list[tuple] = [
    (QuestionnaireForm.attends_kindergarten, "attends_kindergarten",
     "Посещает ли ребёнок детский сад?", "yn2"),
    (QuestionnaireForm.attends_school, "attends_school",
     "Посещает ли ребёнок школу?", "yn2"),
    (QuestionnaireForm.native_language, "native_language",
     "Какой родной язык ребёнка?", "text"),
    (QuestionnaireForm.second_language, "second_language",
     "Есть ли второй язык? Если да — какой.", "text"),

    (QuestionnaireForm.says_single_words, "says_single_words",
     "Говорит ли ребёнок отдельные слова?", "yn3"),
    (QuestionnaireForm.says_short_sentences, "says_short_sentences",
     "Говорит ли короткими предложениями?", "yn3"),
    (QuestionnaireForm.says_long_sentences, "says_long_sentences",
     "Говорит ли длинными предложениями?", "yn3"),
    (QuestionnaireForm.tells_about_day, "tells_about_day",
     "Может рассказать о своём дне?", "yn3"),
    (QuestionnaireForm.likes_talking, "likes_talking",
     "Любит разговаривать?", "yn3"),
    (QuestionnaireForm.answers_questions, "answers_questions",
     "Отвечает ли на вопросы?", "yn3"),
    (QuestionnaireForm.understands_speech, "understands_speech",
     "Понимает обращённую речь?", "yn3"),
    (QuestionnaireForm.follows_instructions, "follows_instructions",
     "Выполняет инструкции?", "yn3"),
    (QuestionnaireForm.is_understood_by_others, "is_understood_by_others",
     "Понимают ли ребёнка окружающие?", "yn3"),

    (QuestionnaireForm.pronunciation_difficulties, "pronunciation_difficulties",
     "Есть ли трудности с произношением звуков?", "yn2"),

    (QuestionnaireForm.focuses_20_min, "focuses_20_min",
     "Может спокойно заниматься около 20 минут?", "yn3"),
    (QuestionnaireForm.gets_distracted, "gets_distracted",
     "Быстро отвлекается?", "yn3"),
    (QuestionnaireForm.likes_books, "likes_books",
     "Любит книги?", "yn3"),
    (QuestionnaireForm.likes_board_games, "likes_board_games",
     "Любит настольные игры?", "yn3"),
    (QuestionnaireForm.likes_drawing, "likes_drawing",
     "Любит рисовать?", "yn3"),
    (QuestionnaireForm.likes_modelling, "likes_modelling",
     "Любит лепить?", "yn3"),
    (QuestionnaireForm.behavior_difficulties, "behavior_difficulties",
     "Есть ли сложности в поведении?", "yn3"),
    (QuestionnaireForm.peer_communication_difficulties, "peer_communication_difficulties",
     "Есть ли сложности в общении со сверстниками?", "yn3"),

    (QuestionnaireForm.dresses_independently, "dresses_independently",
     "Самостоятельно ли ребёнок одевается?", "yn3"),
    (QuestionnaireForm.puts_away_toys, "puts_away_toys",
     "Самостоятельно ли убирает игрушки?", "yn3"),
    (QuestionnaireForm.follows_instructions_skill, "follows_instructions_skill",
     "Самостоятельно ли выполняет инструкции?", "yn3"),
    (QuestionnaireForm.repeats_movements, "repeats_movements",
     "Самостоятельно ли повторяет движения?", "yn3"),
    (QuestionnaireForm.repeats_words, "repeats_words",
     "Самостоятельно ли повторяет слова?", "yn3"),
    (QuestionnaireForm.repeats_sentences, "repeats_sentences",
     "Самостоятельно ли повторяет предложения?", "yn3"),
    (QuestionnaireForm.remembers_poems, "remembers_poems",
     "Самостоятельно ли запоминает стихи?", "yn3"),

    (QuestionnaireForm.neurologist_consult, "neurologist_consult",
     "Были ли консультации невролога? (необязательно)", "yn2"),
    (QuestionnaireForm.ent_consult, "ent_consult",
     "Были ли консультации ЛОР-врача? (необязательно)", "yn2"),
    (QuestionnaireForm.psychologist_consult, "psychologist_consult",
     "Были ли консультации психолога? (необязательно)", "yn2"),
    (QuestionnaireForm.had_speech_therapist, "had_speech_therapist",
     "Были ли занятия с логопедом ранее? (необязательно)", "yn2"),
    (QuestionnaireForm.specialist_reports, "specialist_reports",
     "Есть ли заключения специалистов? (необязательно)", "yn2"),
    (QuestionnaireForm.hearing_problems, "hearing_problems",
     "Есть ли проблемы со слухом? (необязательно)", "yn2"),
    (QuestionnaireForm.pregnancy_birth_features, "pregnancy_birth_features",
     "Есть ли особенности беременности или родов? (необязательно)", "yn2"),

    (QuestionnaireForm.additional_info, "additional_info",
     "Расскажите всё, что считаете важным о ребёнке.", "text"),
]

STATE_INDEX = {step[0].state: i for i, step in enumerate(STEPS)}


def _keyboard(kind: str):
    if kind == "yn3":
        return yes_no_partially_keyboard()
    if kind == "yn2":
        return yes_no_keyboard()
    return None


async def _ask_step(message_or_callback, state: FSMContext, index: int) -> None:
    if index >= len(STEPS):
        await _finish_questionnaire(message_or_callback, state)
        return
    step_state, field, text, kind = STEPS[index]
    await state.set_state(step_state)
    keyboard = _keyboard(kind)
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    if keyboard:
        await target.answer(text, reply_markup=keyboard)
    else:
        await target.answer(text)


@router.message(F.text == MENU_QUESTIONNAIRE)
@router.message(F.text == "/questionnaire")
async def start_questionnaire(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    user = await get_user_by_telegram_id(session, message.from_user.id)
    await state.update_data(
        child_name=user.child_name if user else None,
        child_age=user.child_age if user else None,
    )
    intro = "📋 Заполним анкету ребёнка. Отвечайте по очереди — это займёт несколько минут.\n\n"
    if user and user.child_name:
        await message.answer(intro + f"Имя ребёнка: {user.child_name} (использую данные из записи).")
        await _ask_step(message, state, 0)
    else:
        await state.set_state(QuestionnaireForm.child_name)
        await message.answer(intro + "Как зовут ребёнка?")


@router.message(QuestionnaireForm.child_name)
async def q_child_name(message: Message, state: FSMContext) -> None:
    await state.update_data(child_name=message.text)
    await state.set_state(QuestionnaireForm.child_age)
    await message.answer("Сколько лет ребёнку?")


@router.message(QuestionnaireForm.child_age)
async def q_child_age(message: Message, state: FSMContext) -> None:
    await state.update_data(child_age=message.text)
    await _ask_step(message, state, 0)


@router.message(QuestionnaireForm.pronunciation_details)
async def q_pronunciation_details(message: Message, state: FSMContext) -> None:
    await state.update_data(pronunciation_details=message.text)
    current_index = STATE_INDEX[QuestionnaireForm.pronunciation_difficulties.state]
    await _ask_step(message, state, current_index + 1)


@router.message(QuestionnaireForm.additional_info)
async def q_additional_info(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(additional_info=message.text)
    await _finish_questionnaire(message, state, session=session)


@router.callback_query(F.data.startswith("ans:"))
async def q_answer_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    current = await state.get_state()
    if current not in STATE_INDEX:
        await callback.answer()
        return
    index = STATE_INDEX[current]
    step_state, field, text, kind = STEPS[index]
    answer = callback.data.split(":", 1)[1]
    await state.update_data(**{field: answer})
    await callback.message.edit_text(f"{text}\n\n➡️ {ANSWER_LABELS[answer]}")

    if field == "pronunciation_difficulties" and answer == "yes":
        await state.set_state(QuestionnaireForm.pronunciation_details)
        await callback.message.answer("Какие именно звуки вызывают трудности?")
        await callback.answer()
        return

    next_index = index + 1
    if field == "pronunciation_difficulties" and answer != "yes":
        next_index = STATE_INDEX[QuestionnaireForm.pronunciation_difficulties.state] + 1

    if next_index >= len(STEPS):
        await _finish_questionnaire(callback, state, session=session)
    else:
        await _ask_step(callback, state, next_index)
    await callback.answer()


async def _finish_questionnaire(message_or_callback, state: FSMContext, session: AsyncSession | None = None) -> None:
    data = await state.get_data()
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback

    if session is None:
        await target.answer("Спасибо! Анкета сохраняется...")
        await state.clear()
        return

    user = await get_user_by_telegram_id(session, message_or_callback.from_user.id if not isinstance(message_or_callback, CallbackQuery) else message_or_callback.from_user.id)
    q_data = {k: v for k, v in data.items() if k not in ("child_name", "child_age")}
    q_data["child_name"] = data.get("child_name")
    q_data["child_age"] = data.get("child_age")
    questionnaire = await create_questionnaire(session, user.id, q_data)

    await target.answer(
        "✅ Спасибо! Анкета сохранена. Это очень поможет мне подготовиться к занятиям "
        "с вашим ребёнком.",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()
    await notify_questionnaire_filled(message_or_callback.bot, user, questionnaire)

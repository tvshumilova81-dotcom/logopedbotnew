from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.main_menu import MENU_ABOUT

router = Router(name="about")

ABOUT_MAIN = (
    "👩‍🏫 <b>Обо мне</b>\n\n"
    "Меня зовут <b>Татьяна Шумилова</b>.\n"
    "Я детский логопед и педагог.\n\n"
    "📅 Педагогический стаж — 17 лет.\n"
    "🗣 Логопедическая практика — более 3 лет.\n"
    "🏆 Победитель конкурса «Воспитатель года».\n\n"
    "За годы работы помогла более 60 детям успешно подготовиться к школе "
    "и развить речь.\n\n"
    "Сегодня работаю онлайн с детьми из разных стран мира."
)

MY_STORY = (
    "📖 <b>Моя история</b>\n\n"
    "Я родилась в городе Калининграде.\n"
    "Окончила музыкальный колледж имени С. В. Рахманинова.\n"
    "Продолжила обучение в музыкальной консерватории имени М. И. Глинки "
    "в Нижнем Новгороде.\n\n"
    "Музыкальное образование позволило мне глубже понять развитие слуха, "
    "дыхания, чувства ритма и голоса.\n\n"
    "Позже я полностью посвятила себя педагогике. Более 17 лет работала "
    "воспитателем детского сада и стала победителем конкурса «Воспитатель года».\n\n"
    "Сегодня я объединяю педагогический, музыкальный и логопедический опыт, "
    "помогая детям раскрывать свой потенциал."
)

DIRECTIONS = (
    "🧩 <b>Мои направления</b>\n\n"
    "✅ Запуск речи\n"
    "✅ Коррекция речи\n"
    "✅ Постановка звуков\n"
    "✅ Автоматизация звуков\n"
    "✅ Развитие речи\n"
    "✅ Логоритмика\n"
    "✅ Артикуляционная гимнастика\n"
    "✅ Пальчиковые игры\n"
    "✅ Развитие мелкой моторики\n"
    "✅ Развитие крупной моторики\n"
    "✅ Развитие дыхания\n"
    "✅ Развитие слухового восприятия\n"
    "✅ Развитие голоса\n"
    "✅ Развитие внимания\n"
    "✅ Развитие памяти\n"
    "✅ Игры на переключение внимания\n"
    "✅ Подготовка к школе\n"
    "✅ Индивидуальные онлайн-занятия"
)

WHY_ME = (
    "⭐️ <b>Почему родители выбирают меня</b>\n\n"
    "⭐️ 17 лет педагогического опыта\n"
    "⭐️ Более 3 лет логопедической практики\n"
    "⭐️ Победитель конкурса «Воспитатель года»\n"
    "⭐️ Индивидуальный подход\n"
    "⭐️ Игровой формат обучения\n"
    "⭐️ Онлайн-занятия по всему миру\n"
    "⭐️ Комплексное развитие ребёнка\n"
    "⭐️ Поддержка родителей"
)


def about_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Моя история", callback_data="about:story")
    builder.button(text="🧩 Мои направления", callback_data="about:directions")
    builder.button(text="⭐️ Почему выбирают меня", callback_data="about:why")
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text == MENU_ABOUT)
async def show_about(message: Message) -> None:
    await message.answer(ABOUT_MAIN, reply_markup=about_keyboard())


@router.callback_query(F.data == "about:story")
async def about_story(callback) -> None:
    await callback.message.answer(MY_STORY, reply_markup=about_keyboard())
    await callback.answer()


@router.callback_query(F.data == "about:directions")
async def about_directions(callback) -> None:
    await callback.message.answer(DIRECTIONS, reply_markup=about_keyboard())
    await callback.answer()


@router.callback_query(F.data == "about:why")
async def about_why(callback) -> None:
    await callback.message.answer(WHY_ME, reply_markup=about_keyboard())
    await callback.answer()

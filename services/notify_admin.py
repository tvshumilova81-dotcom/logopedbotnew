from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config.settings import settings
from database.models.booking import Booking
from database.models.material import Material
from database.models.questionnaire import Questionnaire
from database.models.user import User
from keyboards.admin import booking_notification_keyboard, questionnaire_notification_keyboard
from keyboards.yes_no import ANSWER_LABELS

logger = logging.getLogger("bot.admin_notify")


async def notify_new_booking(bot: Bot, user: User, booking: Booking) -> int | None:
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔔 <b>Новая заявка на занятие</b>\n\n"
        f"👤 Родитель:\n{booking.parent_name}\n\n"
        f"👶 Ребёнок:\n{booking.child_name}\n\n"
        f"🎂 Возраст:\n{booking.child_age}\n\n"
        f"⚧️ Пол:\n{booking.child_gender}\n\n"
        f"🌍 Страна:\n{booking.country}\n\n"
        f"🕒 Часовой пояс:\n{booking.timezone or '—'}\n\n"
        f"🗣 Проблема:\n{booking.problem or '—'}\n\n"
        f"😟 Беспокоит:\n{booking.concern or '—'}\n\n"
        f"🗓 Когда впервые заметили:\n{booking.noticed_since or '—'}\n\n"
        f"📚 Был ли логопед:\n{booking.saw_speech_therapist or '—'}\n\n"
        f"📄 Заключения специалистов:\n{booking.specialists_reports or '—'}\n\n"
        f"📅 Удобные дни:\n{booking.convenient_days or '—'}\n\n"
        f"⏰ Удобное время:\n{booking.convenient_time or '—'}\n\n"
        f"👤 Username Telegram:\n@{user.username if user.username else '—'}\n\n"
        f"🆔 Telegram ID:\n{user.telegram_id}\n\n"
        f"📅 Дата регистрации:\n{user.created_at.strftime('%d.%m.%Y')}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    sent_id = None
    for admin_id in settings.admin_ids:
        try:
            msg = await bot.send_message(
                admin_id, text, reply_markup=booking_notification_keyboard(booking.id)
            )
            sent_id = msg.message_id
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)
    return sent_id


async def notify_questionnaire_filled(bot: Bot, user: User, questionnaire: Questionnaire) -> None:
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>Заполнена анкета ребёнка</b>\n\n"
        f"👤 Родитель:\n{user.parent_name or '—'}\n\n"
        f"👶 Ребёнок:\n{questionnaire.child_name or '—'}\n\n"
        f"🆔 Telegram ID:\n{user.telegram_id}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                text,
                reply_markup=questionnaire_notification_keyboard(questionnaire.id),
            )
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)


async def notify_new_purchase(bot: Bot, user: User, material: Material) -> None:
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>Новая покупка</b>\n\n"
        f"👤 {user.display_name()}\n\n"
        f"📚 Материал:\n{material.title}\n\n"
        f"⭐️ Оплачено:\n{material.price_stars} Telegram Stars\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)


async def notify_lead_magnet_download(bot: Bot, user: User) -> None:
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📄 <b>Скачан лид-магнит «Речь за 7 минут»</b>\n\n"
        f"👤 {user.display_name()}\n"
        f"🆔 Telegram ID: {user.telegram_id}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)


async def notify_diagnostic_click(bot: Bot, user: User) -> None:
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🩺 <b>Запрос по слову «Диагностика»</b>\n\n"
        f"👤 {user.display_name()}\n"
        f"🆔 Telegram ID: {user.telegram_id}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)


async def notify_new_miniapp_booking(bot: Bot, user: User, booking) -> None:
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🗓 <b>Новая запись через мини-приложение</b>\n\n"
        f"👤 {user.display_name()}\n"
        f"📅 Дата: {booking.date}\n"
        f"⏰ Время: {booking.time}\n"
        f"🌍 Страна: {booking.country or '—'}\n"
        f"🕒 Часовой пояс: {booking.timezone or '—'}\n"
        f"📝 Тема: {booking.topic or '—'}\n"
        f"🆔 Telegram ID: {user.telegram_id}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)


async def notify_miniapp_cancel(bot: Bot, user: User, booking) -> None:
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "❌ <b>Отмена записи (мини-приложение)</b>\n\n"
        f"👤 {user.display_name()}\n"
        f"📅 Дата: {booking.date}\n"
        f"⏰ Время: {booking.time}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)


async def notify_consultation_request(bot: Bot, user: User, text: str) -> None:
    message = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💬 <b>Запрос на консультацию (мини-приложение)</b>\n\n"
        f"👤 {user.display_name()}\n"
        f"🆔 Telegram ID: {user.telegram_id}\n\n"
        f"📝 Сообщение:\n{text}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, message)
        except TelegramAPIError:
            logger.exception("Не удалось отправить уведомление админу %s", admin_id)


async def notify_progress_added(bot: Bot, user: User, title: str) -> None:
    text = (
        f"📈 <b>Новая запись о прогрессе!</b>\n\n"
        f"«{title}»\n\n"
        "Посмотреть подробности можно в разделе «Прогресс» мини-приложения."
    )
    try:
        await bot.send_message(user.telegram_id, text)
    except TelegramAPIError:
        logger.exception("Не удалось отправить уведомление о прогрессе пользователю %s", user.telegram_id)


async def notify_homework_added(bot: Bot, user: User, homework_text: str) -> None:
    text = (
        "📝 <b>Новое домашнее задание!</b>\n\n"
        f"{homework_text}\n\n"
        "Отметить выполнение можно в разделе «Прогресс» мини-приложения."
    )
    try:
        await bot.send_message(user.telegram_id, text)
    except TelegramAPIError:
        logger.exception("Не удалось отправить домашнее задание пользователю %s", user.telegram_id)


def format_questionnaire(user: User, q: Questionnaire) -> str:
    def lbl(value: str | None) -> str:
        if value is None:
            return "—"
        return ANSWER_LABELS.get(value, value)

    return (
        "📋 <b>Анкета ребёнка</b>\n\n"
        f"👤 Родитель: {user.parent_name or '—'}\n"
        f"👶 Ребёнок: {q.child_name or '—'}, возраст: {q.child_age or '—'}\n\n"
        "<b>Общая информация</b>\n"
        f"Детский сад: {lbl(q.attends_kindergarten)}\n"
        f"Школа: {lbl(q.attends_school)}\n"
        f"Родной язык: {q.native_language or '—'}\n"
        f"Второй язык: {q.second_language or '—'}\n\n"
        "<b>Развитие речи</b>\n"
        f"Отдельные слова: {lbl(q.says_single_words)}\n"
        f"Короткие предложения: {lbl(q.says_short_sentences)}\n"
        f"Длинные предложения: {lbl(q.says_long_sentences)}\n"
        f"Рассказывает о дне: {lbl(q.tells_about_day)}\n"
        f"Любит разговаривать: {lbl(q.likes_talking)}\n"
        f"Отвечает на вопросы: {lbl(q.answers_questions)}\n"
        f"Понимает обращённую речь: {lbl(q.understands_speech)}\n"
        f"Выполняет инструкции: {lbl(q.follows_instructions)}\n"
        f"Понимают окружающие: {lbl(q.is_understood_by_others)}\n\n"
        "<b>Произношение</b>\n"
        f"Трудности: {lbl(q.pronunciation_difficulties)}\n"
        f"Какие звуки: {q.pronunciation_details or '—'}\n\n"
        "<b>Поведение</b>\n"
        f"Занимается 20 мин: {lbl(q.focuses_20_min)}\n"
        f"Отвлекается: {lbl(q.gets_distracted)}\n"
        f"Любит книги: {lbl(q.likes_books)}\n"
        f"Любит настольные игры: {lbl(q.likes_board_games)}\n"
        f"Любит рисовать: {lbl(q.likes_drawing)}\n"
        f"Любит лепить: {lbl(q.likes_modelling)}\n"
        f"Сложности в поведении: {lbl(q.behavior_difficulties)}\n"
        f"Сложности со сверстниками: {lbl(q.peer_communication_difficulties)}\n\n"
        "<b>Навыки</b>\n"
        f"Одевается сам: {lbl(q.dresses_independently)}\n"
        f"Убирает игрушки: {lbl(q.puts_away_toys)}\n"
        f"Выполняет инструкции: {lbl(q.follows_instructions_skill)}\n"
        f"Повторяет движения: {lbl(q.repeats_movements)}\n"
        f"Повторяет слова: {lbl(q.repeats_words)}\n"
        f"Повторяет предложения: {lbl(q.repeats_sentences)}\n"
        f"Запоминает стихи: {lbl(q.remembers_poems)}\n\n"
        "<b>Медицинская информация</b>\n"
        f"Невролог: {lbl(q.neurologist_consult)}\n"
        f"ЛОР: {lbl(q.ent_consult)}\n"
        f"Психолог: {lbl(q.psychologist_consult)}\n"
        f"Занятия с логопедом ранее: {lbl(q.had_speech_therapist)}\n"
        f"Заключения специалистов: {lbl(q.specialist_reports)}\n"
        f"Проблемы со слухом: {lbl(q.hearing_problems)}\n"
        f"Особенности беременности/родов: {lbl(q.pregnancy_birth_features)}\n\n"
        f"<b>Дополнительно:</b>\n{q.additional_info or '—'}"
    )

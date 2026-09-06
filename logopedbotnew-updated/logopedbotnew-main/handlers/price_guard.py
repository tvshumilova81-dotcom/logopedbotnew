import re

from aiogram import Router
from aiogram.types import Message

router = Router(name="price_guard")

PRICE_PATTERN = re.compile(
    r"(цен|стоимост|сколько стоит|прайс|тариф|скольк.*плат)", re.IGNORECASE
)

PRICE_ANSWER = "Стоимость занятий можно узнать через мой Instagram или Telegram-канал."


@router.message(lambda message: bool(message.text) and PRICE_PATTERN.search(message.text))
async def price_question(message: Message) -> None:
    await message.answer(PRICE_ANSWER)

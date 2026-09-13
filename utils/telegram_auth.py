"""Проверка подписи initData, которую Telegram Mini App передаёт на backend.

Как это работает:
  1. Фронтенд мини-приложения берёт строку `Telegram.WebApp.initData`
     (её даёт сам Telegram, подделать нельзя без токена бота) и отправляет
     её на наш API в заголовке Authorization: tma <initData>.
  2. Мы пересчитываем HMAC-подпись той же строки с использованием токена
     бота и сравниваем с подписью, которую прислал Telegram. Если совпало —
     запрос точно пришёл из настоящего мини-приложения этого бота, и мы
     знаем telegram_id пользователя, который его открыл.

Документация: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qsl


class InitDataError(Exception):
    pass


@dataclass
class TelegramWebAppUser:
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> TelegramWebAppUser:
    """Проверяет подпись и возвращает пользователя, либо кидает InitDataError."""
    if not init_data:
        raise InitDataError("init data is empty")

    pairs = dict(parse_qsl(init_data, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("hash is missing")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InitDataError("invalid signature")

    auth_date = int(pairs.get("auth_date", "0"))
    if max_age_seconds and (time.time() - auth_date) > max_age_seconds:
        raise InitDataError("init data expired")

    user_raw = pairs.get("user")
    if not user_raw:
        raise InitDataError("user field is missing")

    user_json = json.loads(user_raw)
    return TelegramWebAppUser(
        telegram_id=int(user_json["id"]),
        username=user_json.get("username"),
        first_name=user_json.get("first_name"),
        last_name=user_json.get("last_name"),
    )

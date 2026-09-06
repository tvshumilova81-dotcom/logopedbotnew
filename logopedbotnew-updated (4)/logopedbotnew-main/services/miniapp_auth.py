from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from config.settings import settings

MAX_INIT_DATA_AGE = 24 * 60 * 60  # 24 часа


def validate_init_data(init_data: str) -> dict | None:
    """Проверяет подпись Telegram.WebApp.initData и возвращает данные пользователя.

    Возвращает None, если подпись неверна, данные устарели или отсутствуют.
    См. https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    if not init_data:
        return None

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date = pairs.get("auth_date")
    if auth_date and (time.time() - int(auth_date)) > MAX_INIT_DATA_AGE:
        return None

    user_raw = pairs.get("user")
    if not user_raw:
        return None

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        return None

    return user

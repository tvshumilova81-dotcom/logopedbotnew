from __future__ import annotations

import json
from functools import lru_cache

from config.settings import FAQ_FILE


@lru_cache
def load_faq() -> list[dict]:
    if not FAQ_FILE.exists():
        return []
    with open(FAQ_FILE, encoding="utf-8") as f:
        return json.load(f)

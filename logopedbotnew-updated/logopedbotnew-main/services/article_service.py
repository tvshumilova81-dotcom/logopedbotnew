from __future__ import annotations

from dataclasses import dataclass

from config.settings import ARTICLES_DIR

# Порядок и заголовки статей в меню "Бесплатные материалы"
ARTICLE_ORDER: list[tuple[str, str]] = [
    ("kak_pomoch_nachat_govorit", "📖 Как помочь ребёнку начать говорить"),
    ("igry_dlya_razvitiya_rechi_doma", "📖 Игры для развития речи дома"),
    ("pochemu_ne_vygovarivaet_r", "📖 Почему ребёнок не выговаривает звук «Р»"),
    ("kogda_obratitsya_k_logopedu", "📖 Когда стоит обратиться к логопеду"),
    ("oshibki_roditeley", "📖 Ошибки родителей при развитии речи"),
    ("podgotovka_k_shkole", "📖 Подготовка ребёнка к школе"),
    ("naidi_paru", "🎲 Бонус-игра «Найди пару» (PDF)"),
]


@dataclass
class Article:
    slug: str
    title: str
    content: str


def list_articles() -> list[tuple[str, str]]:
    return ARTICLE_ORDER


def get_article(slug: str) -> Article | None:
    for s, title in ARTICLE_ORDER:
        if s == slug:
            break
    else:
        return None

    path = ARTICLES_DIR / f"{slug}.md"
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    return Article(slug=slug, title=title, content=content)

from __future__ import annotations

from config.settings import MATERIALS_DIR
from database.engine import async_session_maker
from services.material_service import create_material, get_material_by_slug

DEFAULT_MATERIAL = {
    "slug": "30_rechevyh_igr",
    "title": "🎲 30 речевых игр, в которые можно играть дома",
    "description": (
        "Практическое пособие для родителей с играми, которые помогут ежедневно "
        "развивать речь ребёнка в игровой форме.\n\n"
        "Внутри материала:\n"
        "• 30 простых речевых игр;\n"
        "• игры для развития словарного запаса;\n"
        "• игры на внимание;\n"
        "• игры на память;\n"
        "• игры для развития слухового восприятия;\n"
        "• дыхательные упражнения;\n"
        "• пальчиковые игры;\n"
        "• для каждой игры указаны цель, возраст, необходимые материалы, "
        "пошаговое описание и какой навык развивается."
    ),
    "price_stars": 50,
    "file_path": str(MATERIALS_DIR / "30_rechevyh_igr.pdf"),
}


async def seed_default_materials() -> None:
    async with async_session_maker() as session:
        existing = await get_material_by_slug(session, DEFAULT_MATERIAL["slug"])
        if existing:
            return
        await create_material(session, is_active=True, **DEFAULT_MATERIAL)

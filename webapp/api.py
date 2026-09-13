from __future__ import annotations

import json
import logging
from datetime import date, datetime

from aiohttp import web
from sqlalchemy import select

from config.settings import settings
from database.engine import async_session_maker
from database.models.purchase import Purchase
from services import material_service, schedule_service, user_service
from utils.telegram_auth import InitDataError, validate_init_data

logger = logging.getLogger("bot.webapp")

routes = web.RouteTableDef()


# ---------------------------------------------------------------------------
# Аутентификация запросов от мини-приложения
# ---------------------------------------------------------------------------

async def _authed_telegram_user(request: web.Request):
    """Достаёт и проверяет initData из заголовка Authorization: tma <initData>."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("tma "):
        raise web.HTTPUnauthorized(text=json.dumps({"error": "missing_init_data"}))
    init_data = auth[len("tma "):]
    try:
        tg_user = validate_init_data(init_data, settings.BOT_TOKEN)
    except InitDataError as exc:
        logger.warning("initData validation failed: %s", exc)
        raise web.HTTPUnauthorized(text=json.dumps({"error": "invalid_init_data"}))
    return tg_user


async def _require_admin(request: web.Request):
    tg_user = await _authed_telegram_user(request)
    if tg_user.telegram_id not in settings.admin_ids:
        raise web.HTTPForbidden(text=json.dumps({"error": "not_admin"}))
    return tg_user


def _json(data, status=200):
    return web.json_response(data, status=status)


def _booking_dict(b, include_client: bool = False) -> dict:
    data = {
        "id": b.id,
        "date": b.date.isoformat(),
        "time": b.time,
        "topic": b.topic,
        "country": b.country,
        "timezone": b.timezone,
        "price_rub": b.price_rub,
        "status": b.status.value,
    }
    if include_client:
        user = getattr(b, "user", None)
        data["client_username"] = getattr(user, "username", None)
        data["client_name"] = user.display_name() if user else None
        data["client_telegram_id"] = getattr(user, "telegram_id", None)
    return data


def _income_dict(i) -> dict:
    return {
        "id": i.id,
        "date": i.date.isoformat(),
        "amount": i.amount,
        "note": i.note,
        "source": i.source.value,
        "lesson_booking_id": i.lesson_booking_id,
    }


# ---------------------------------------------------------------------------
# Клиентские эндпоинты
# ---------------------------------------------------------------------------

@routes.get("/api/me")
async def api_me(request: web.Request):
    tg_user = await _authed_telegram_user(request)
    async with async_session_maker() as session:
        user = await user_service.get_or_create_user(session, _FakeTgUser(tg_user))
        return _json({
            "telegram_id": tg_user.telegram_id,
            "first_name": tg_user.first_name,
            "username": tg_user.username,
            "parent_name": user.parent_name,
            "child_name": user.child_name,
            "country": user.country,
            "timezone": user.timezone,
            "is_admin": tg_user.telegram_id in settings.admin_ids,
        })


class _FakeTgUser:
    """Адаптер, чтобы переиспользовать user_service.get_or_create_user,
    который ожидает aiogram-объект User с полями .id и .username."""
    def __init__(self, tg_user):
        self.id = tg_user.telegram_id
        self.username = tg_user.username


@routes.post("/api/profile")
async def api_update_profile(request: web.Request):
    tg_user = await _authed_telegram_user(request)
    body = await request.json()
    async with async_session_maker() as session:
        user = await user_service.get_or_create_user(session, _FakeTgUser(tg_user))
        user.parent_name = body.get("parent_name", user.parent_name)
        user.child_name = body.get("child_name", user.child_name)
        user.country = body.get("country", user.country)
        user.timezone = body.get("timezone", user.timezone)
        await session.commit()
    return _json({"ok": True})


@routes.get("/api/slots")
async def api_slots(request: web.Request):
    await _authed_telegram_user(request)
    try:
        year = int(request.query.get("year"))
        month = int(request.query.get("month"))
    except (TypeError, ValueError):
        today = date.today()
        year, month = today.year, today.month
    async with async_session_maker() as session:
        slots = await schedule_service.get_month_slots(session, year, month)
    return _json({"hours": schedule_service.WORK_HOURS, "days": slots})


@routes.post("/api/bookings")
async def api_create_booking(request: web.Request):
    tg_user = await _authed_telegram_user(request)
    body = await request.json()
    try:
        lesson_date = datetime.strptime(body["date"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return _json({"error": "invalid_date"}, status=400)
    time_str = body.get("time")
    if time_str not in schedule_service.WORK_HOURS:
        return _json({"error": "invalid_time"}, status=400)

    async with async_session_maker() as session:
        user = await user_service.get_or_create_user(session, _FakeTgUser(tg_user))
        try:
            booking = await schedule_service.create_booking(
                session, user, lesson_date, time_str,
                topic=body.get("topic"),
                country=body.get("country"),
                timezone=body.get("timezone"),
                price_rub=schedule_service.DEFAULT_SESSION_PRICE,
            )
        except ValueError:
            return _json({"error": "slot_taken"}, status=409)
        await schedule_service.add_income_for_booking(session, booking)
        return _json(_booking_dict(booking))


@routes.get("/api/bookings")
async def api_my_bookings(request: web.Request):
    tg_user = await _authed_telegram_user(request)
    async with async_session_maker() as session:
        user = await user_service.get_or_create_user(session, _FakeTgUser(tg_user))
        bookings = await schedule_service.user_bookings(session, user)
        return _json([_booking_dict(b) for b in bookings])


@routes.get("/api/materials")
async def api_materials(request: web.Request):
    tg_user = await _authed_telegram_user(request)
    async with async_session_maker() as session:
        user = await user_service.get_or_create_user(session, _FakeTgUser(tg_user))
        materials = await material_service.list_active_materials(session)
        purchased_ids = set((await session.execute(
            select(Purchase.material_id).where(Purchase.user_id == user.id)
        )).scalars().all())
        return _json([
            {
                "id": m.id, "title": m.title, "description": m.description,
                "price_stars": m.price_stars, "purchased": m.id in purchased_ids,
            }
            for m in materials
        ])


# ---------------------------------------------------------------------------
# Админские эндпоинты — требуют telegram_id из ADMIN_IDS
# ---------------------------------------------------------------------------

@routes.get("/api/admin/slots")
async def api_admin_slots(request: web.Request):
    await _require_admin(request)
    try:
        year = int(request.query.get("year")); month = int(request.query.get("month"))
    except (TypeError, ValueError):
        today = date.today(); year, month = today.year, today.month
    async with async_session_maker() as session:
        slots = await schedule_service.get_month_slots(session, year, month)
        bookings = await schedule_service.all_bookings(session)
        # ключ строкой "YYYY-MM-DD,HH:MM" — dict с tuple-ключами не сериализуется в JSON
        by_key = {f"{b.date.isoformat()},{b.time}": _booking_dict(b, include_client=True) for b in bookings}
    return _json({"hours": schedule_service.WORK_HOURS, "days": slots, "bookings": by_key})


@routes.post("/api/admin/slots/block")
async def api_admin_block(request: web.Request):
    await _require_admin(request)
    body = await request.json()
    d = datetime.strptime(body["date"], "%Y-%m-%d").date()
    async with async_session_maker() as session:
        await schedule_service.block_slot(session, d, body["time"], body.get("reason"))
    return _json({"ok": True})


@routes.post("/api/admin/slots/unblock")
async def api_admin_unblock(request: web.Request):
    await _require_admin(request)
    body = await request.json()
    d = datetime.strptime(body["date"], "%Y-%m-%d").date()
    async with async_session_maker() as session:
        await schedule_service.unblock_slot(session, d, body["time"])
    return _json({"ok": True})


@routes.get("/api/admin/bookings")
async def api_admin_bookings(request: web.Request):
    await _require_admin(request)
    async with async_session_maker() as session:
        bookings = await schedule_service.all_bookings(session)
        return _json([_booking_dict(b, include_client=True) for b in bookings])


@routes.post("/api/admin/bookings/{booking_id}/cancel")
async def api_admin_cancel_booking(request: web.Request):
    await _require_admin(request)
    booking_id = int(request.match_info["booking_id"])
    async with async_session_maker() as session:
        booking = await schedule_service.cancel_booking(session, booking_id)
        if booking is None:
            return _json({"error": "not_found"}, status=404)
    return _json({"ok": True})


@routes.get("/api/admin/income")
async def api_admin_income(request: web.Request):
    await _require_admin(request)
    async with async_session_maker() as session:
        entries = await schedule_service.list_income(session)
        return _json([_income_dict(i) for i in entries])


@routes.post("/api/admin/income")
async def api_admin_add_income(request: web.Request):
    await _require_admin(request)
    body = await request.json()
    d = datetime.strptime(body["date"], "%Y-%m-%d").date()
    amount = int(body["amount"])
    note = body.get("note", "Доход")
    async with async_session_maker() as session:
        entry = await schedule_service.add_manual_income(session, d, amount, note)
        return _json(_income_dict(entry))


@routes.patch("/api/admin/income/{entry_id}")
async def api_admin_update_income(request: web.Request):
    await _require_admin(request)
    entry_id = int(request.match_info["entry_id"])
    body = await request.json()
    async with async_session_maker() as session:
        entry = await schedule_service.update_income(session, entry_id, int(body["amount"]))
        if entry is None:
            return _json({"error": "not_found"}, status=404)
        return _json(_income_dict(entry))


@routes.delete("/api/admin/income/{entry_id}")
async def api_admin_delete_income(request: web.Request):
    await _require_admin(request)
    entry_id = int(request.match_info["entry_id"])
    async with async_session_maker() as session:
        await schedule_service.delete_income(session, entry_id)
    return _json({"ok": True})


def register_webapp(app: web.Application, static_dir: str) -> None:
    """Регистрирует API и статику мини-приложения в общем aiohttp-приложении бота."""
    app.add_routes(routes)

    async def client_page(_request: web.Request) -> web.Response:
        return web.FileResponse(f"{static_dir}/client.html")

    async def admin_page(_request: web.Request) -> web.Response:
        return web.FileResponse(f"{static_dir}/admin.html")

    app.router.add_get("/webapp", client_page)
    app.router.add_get("/webapp/", client_page)
    app.router.add_get("/webapp/admin", admin_page)
    app.router.add_get("/webapp/admin/", admin_page)

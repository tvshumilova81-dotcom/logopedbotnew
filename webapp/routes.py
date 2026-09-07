from __future__ import annotations

import calendar as calendar_module
import json
from datetime import date
from pathlib import Path

from aiohttp import web

from config.settings import settings
from database.engine import async_session_maker
from database.models.user import User
from services import income_service, progress_service, slot_service
from services.article_service import get_article, list_articles
from services.material_service import list_active_materials, user_purchases
from services.geo_data import COUNTRIES
from services.miniapp_auth import validate_init_data
from services.notify_admin import (
    notify_consultation_request,
    notify_homework_added,
    notify_miniapp_cancel,
    notify_new_miniapp_booking,
    notify_progress_added,
)
from services.user_service import get_or_create_user_by_id, list_users

STATIC_DIR = Path(__file__).resolve().parent / "static"

routes = web.RouteTableDef()


# ==================== Аутентификация ====================

def _get_init_data(request: web.Request) -> str:
    header = request.headers.get("X-Telegram-Init-Data")
    if header:
        return header
    return request.query.get("init_data", "")


async def _authenticate(request: web.Request):
    """Возвращает (user, tg_data) либо кидает web.HTTPUnauthorized."""
    init_data = _get_init_data(request)
    tg_data = validate_init_data(init_data)
    if tg_data is None:
        raise web.HTTPUnauthorized(text=json.dumps({"error": "invalid_init_data"}))

    async with async_session_maker() as session:
        user = await get_or_create_user_by_id(
            session, tg_data["id"], tg_data.get("username")
        )
        return user, tg_data


def _is_admin(tg_data: dict) -> bool:
    return int(tg_data.get("id", 0)) in settings.admin_ids


def _require_admin(tg_data: dict) -> None:
    if not _is_admin(tg_data):
        raise web.HTTPForbidden(text=json.dumps({"error": "not_admin"}))


# ==================== Статика ====================

@routes.get("/webapp")
@routes.get("/webapp/")
async def webapp_index(request: web.Request) -> web.Response:
    return web.FileResponse(STATIC_DIR / "index.html")


@routes.get("/webapp/admin")
@routes.get("/webapp/admin/")
async def webapp_admin(request: web.Request) -> web.Response:
    return web.FileResponse(STATIC_DIR / "admin.html")


@routes.get("/webapp/static/{filename:.+}")
async def webapp_static(request: web.Request) -> web.Response:
    filename = request.match_info["filename"]
    file_path = (STATIC_DIR / filename).resolve()
    if STATIC_DIR not in file_path.parents:
        raise web.HTTPNotFound()
    if not file_path.exists():
        raise web.HTTPNotFound()
    return web.FileResponse(file_path)


# ==================== Общие данные ====================

@routes.get("/api/miniapp/countries")
async def api_countries(request: web.Request) -> web.Response:
    return web.json_response(COUNTRIES)


@routes.get("/api/miniapp/me")
async def api_me(request: web.Request) -> web.Response:
    user, tg_data = await _authenticate(request)
    async with async_session_maker() as session:
        bookings = await slot_service.get_user_bookings(session, user.id)
        upcoming, _past = slot_service.split_upcoming_past(bookings)
        materials_count = len(await user_purchases(session, user.id))
        completed = len([b for b in bookings if b.status.value != "cancelled"])

    return web.json_response(
        {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "parent_name": user.parent_name,
            "child_name": user.child_name,
            "child_age": user.child_age,
            "child_gender": user.child_gender,
            "country": user.country,
            "timezone": user.timezone,
            "is_admin": _is_admin(tg_data),
            "next_booking": _serialize_booking(upcoming[0]) if upcoming else None,
            "stats": {
                "lessons_done": completed,
                "materials": materials_count,
            },
        }
    )


@routes.post("/api/miniapp/profile")
async def api_update_profile(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    body = await request.json()

    async with async_session_maker() as session:
        db_user = await get_or_create_user_by_id(session, user.telegram_id, user.username)
        for field in ("parent_name", "child_name", "child_age", "child_gender", "country", "timezone"):
            if field in body:
                setattr(db_user, field, (body.get(field) or "").strip() or None)
        await session.commit()
        await session.refresh(db_user)

    return web.json_response({"ok": True})


@routes.post("/api/miniapp/consultation")
async def api_consultation(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        raise web.HTTPBadRequest(text=json.dumps({"error": "text_required"}))

    bot = request.app["bot"]
    await notify_consultation_request(bot, user, text)
    return web.json_response({"ok": True})


# ==================== Календарь и запись ====================

def _serialize_booking(b) -> dict:
    return {
        "id": b.id,
        "date": b.date,
        "time": b.time,
        "country": b.country,
        "timezone": b.timezone,
        "topic": b.topic,
        "price": b.price,
        "status": b.status.value,
    }


@routes.get("/api/miniapp/calendar")
async def api_calendar(request: web.Request) -> web.Response:
    """Возвращает по каждому дню месяца: есть ли свободные слоты."""
    year = int(request.query.get("year", date.today().year))
    month = int(request.query.get("month", date.today().month))

    async with async_session_maker() as session:
        await slot_service.ensure_slots_generated(session)
        slots = await slot_service.get_slots_for_month(session, year, month)

    days: dict[str, dict[str, int]] = {}
    for s in slots:
        d = days.setdefault(s.date, {"free": 0, "booked": 0, "blocked": 0})
        d[s.status.value] += 1

    days_in_month = calendar_module.monthrange(year, month)[1]
    result = []
    for day_num in range(1, days_in_month + 1):
        d_str = date(year, month, day_num).isoformat()
        counts = days.get(d_str, {"free": 0, "booked": 0, "blocked": 0})
        result.append({"date": d_str, **counts, "has_free": counts["free"] > 0})

    return web.json_response({"year": year, "month": month, "days": result})


@routes.get("/api/miniapp/slots")
async def api_slots(request: web.Request) -> web.Response:
    date_str = request.query.get("date")
    if not date_str:
        raise web.HTTPBadRequest(text=json.dumps({"error": "date_required"}))

    async with async_session_maker() as session:
        await slot_service.ensure_slots_generated(session)
        slots = await slot_service.get_slots_for_date(session, date_str)

    return web.json_response(
        [{"time": s.time, "status": s.status.value} for s in slots]
    )


@routes.post("/api/miniapp/book")
async def api_book(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    body = await request.json()

    date_str = body.get("date")
    time_str = body.get("time")
    if not date_str or not time_str:
        raise web.HTTPBadRequest(text=json.dumps({"error": "date_and_time_required"}))

    async with async_session_maker() as session:
        db_user = await get_or_create_user_by_id(session, user.telegram_id, user.username)
        booking = await slot_service.book_slot(
            session,
            user_id=db_user.id,
            date_str=date_str,
            time_str=time_str,
            country=body.get("country"),
            timezone=body.get("timezone"),
            topic=body.get("topic"),
        )
        if booking is None:
            raise web.HTTPConflict(text=json.dumps({"error": "slot_taken"}))

        # обновим профиль, если пользователь указал страну/часовой пояс впервые
        if body.get("country") and not db_user.country:
            db_user.country = body.get("country")
        if body.get("timezone") and not db_user.timezone:
            db_user.timezone = body.get("timezone")
        await session.commit()

    bot = request.app["bot"]
    await notify_new_miniapp_booking(bot, db_user, booking)

    return web.json_response({"ok": True, "booking": _serialize_booking(booking)})


@routes.post("/api/miniapp/cancel")
async def api_cancel(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    body = await request.json()
    booking_id = body.get("booking_id")

    from database.models.slot import MiniAppBooking

    async with async_session_maker() as session:
        booking = await session.get(MiniAppBooking, booking_id)
        if booking is None or booking.user_id != user.id:
            raise web.HTTPNotFound(text=json.dumps({"error": "booking_not_found"}))
        ok = await slot_service.cancel_booking(session, booking_id)

    bot = request.app["bot"]
    await notify_miniapp_cancel(bot, user, booking)

    return web.json_response({"ok": ok})


@routes.get("/api/miniapp/history")
async def api_history(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    async with async_session_maker() as session:
        bookings = await slot_service.get_user_bookings(session, user.id)
        upcoming, past = slot_service.split_upcoming_past(bookings)

    return web.json_response(
        {
            "upcoming": [_serialize_booking(b) for b in upcoming],
            "past": [_serialize_booking(b) for b in past],
        }
    )


# ==================== Прогресс и домашние задания ====================

def _serialize_progress(n) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "before_text": n.before_text,
        "after_text": n.after_text,
        "note": n.note,
        "created_at": n.created_at.isoformat(),
    }


def _serialize_homework(h) -> dict:
    return {
        "id": h.id,
        "text": h.text,
        "is_done": h.is_done,
        "created_at": h.created_at.isoformat(),
    }


@routes.get("/api/miniapp/progress")
async def api_progress(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    async with async_session_maker() as session:
        notes = await progress_service.get_progress_notes(session, user.id)
        homework = await progress_service.get_homework(session, user.id)

    return web.json_response(
        {
            "notes": [_serialize_progress(n) for n in notes],
            "homework": [_serialize_homework(h) for h in homework],
        }
    )


@routes.post("/api/miniapp/homework/toggle")
async def api_homework_toggle(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    body = await request.json()
    homework_id = body.get("id")

    async with async_session_maker() as session:
        hw = await progress_service.toggle_homework(session, homework_id, user.id)

    if hw is None:
        raise web.HTTPNotFound()
    return web.json_response({"ok": True, "is_done": hw.is_done})


# ==================== Материалы ====================

@routes.get("/api/miniapp/materials")
async def api_materials(request: web.Request) -> web.Response:
    user, _tg_data = await _authenticate(request)
    async with async_session_maker() as session:
        purchased = await user_purchases(session, user.id)
        all_paid = await list_active_materials(session)

    purchased_ids = {m.id for m in purchased}
    free_articles = [
        {"slug": slug, "title": title} for slug, title in list_articles()
    ]

    return web.json_response(
        {
            "purchased": [
                {"id": m.id, "title": m.title, "description": m.description}
                for m in purchased
            ],
            "available_paid": [
                {
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "price_stars": m.price_stars,
                }
                for m in all_paid
                if m.id not in purchased_ids
            ],
            "free": free_articles,
        }
    )


@routes.get("/api/miniapp/articles/{slug}")
async def api_article(request: web.Request) -> web.Response:
    await _authenticate(request)
    slug = request.match_info["slug"]
    article = get_article(slug)
    if article is None:
        raise web.HTTPNotFound()
    return web.json_response({"title": article.title, "content": article.content})


# ==================== Админ-панель ====================

@routes.get("/api/miniapp/admin/check")
async def api_admin_check(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    return web.json_response({"is_admin": _is_admin(tg_data)})


@routes.get("/api/miniapp/admin/calendar")
async def api_admin_calendar(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    return await api_calendar(request)


@routes.get("/api/miniapp/admin/slots")
async def api_admin_slots(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)

    date_str = request.query.get("date")
    if not date_str:
        raise web.HTTPBadRequest(text=json.dumps({"error": "date_required"}))

    async with async_session_maker() as session:
        await slot_service.ensure_slots_generated(session)
        slots = await slot_service.get_slots_for_date(session, date_str)
        bookings = await slot_service.get_bookings_for_date(session, date_str)

    bookings_by_time = {b.time: b for b in bookings}
    result = []
    for s in slots:
        b = bookings_by_time.get(s.time)
        result.append(
            {
                "time": s.time,
                "status": s.status.value,
                "booking": _serialize_booking(b) if b else None,
            }
        )
    return web.json_response(result)


@routes.post("/api/miniapp/admin/toggle")
async def api_admin_toggle(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    date_str, time_str = body.get("date"), body.get("time")
    if not date_str or not time_str:
        raise web.HTTPBadRequest(text=json.dumps({"error": "date_and_time_required"}))

    async with async_session_maker() as session:
        slot = await slot_service.toggle_block(session, date_str, time_str)

    if slot is None:
        raise web.HTTPBadRequest(text=json.dumps({"error": "cannot_toggle"}))

    return web.json_response({"ok": True, "status": slot.status.value})


@routes.post("/api/miniapp/admin/cancel_booking")
async def api_admin_cancel_booking(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    booking_id = body.get("booking_id")

    from database.models.slot import MiniAppBooking

    async with async_session_maker() as session:
        booking = await session.get(MiniAppBooking, booking_id)
        if booking is None:
            raise web.HTTPNotFound()
        ok = await slot_service.cancel_booking(session, booking_id)

    return web.json_response({"ok": ok})


@routes.get("/api/miniapp/admin/income")
async def api_admin_income(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)

    async with async_session_maker() as session:
        total = await income_service.get_total_income(session)
        bookings_income = await income_service.get_bookings_income(session)
        adjustments = await income_service.list_adjustments(session)

    return web.json_response(
        {
            "total": total,
            "bookings_income": bookings_income,
            "adjustments": [
                {"id": a.id, "amount": a.amount, "comment": a.comment, "created_at": a.created_at.isoformat()}
                for a in adjustments
            ],
        }
    )


@routes.post("/api/miniapp/admin/income/adjust")
async def api_admin_income_adjust(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()

    try:
        amount = int(body.get("amount"))
    except (TypeError, ValueError):
        raise web.HTTPBadRequest(text=json.dumps({"error": "invalid_amount"}))

    async with async_session_maker() as session:
        await income_service.add_adjustment(session, amount, body.get("comment"))
        total = await income_service.get_total_income(session)

    return web.json_response({"ok": True, "total": total})


@routes.post("/api/miniapp/admin/slots/add")
async def api_admin_slots_add(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    date_str, time_str = body.get("date"), body.get("time")
    if not date_str or not time_str:
        raise web.HTTPBadRequest(text=json.dumps({"error": "date_and_time_required"}))

    async with async_session_maker() as session:
        slot = await slot_service.add_custom_slot(session, date_str, time_str)

    if slot is None:
        raise web.HTTPConflict(text=json.dumps({"error": "slot_already_exists"}))

    return web.json_response({"ok": True})


@routes.post("/api/miniapp/admin/slots/delete")
async def api_admin_slots_delete(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    date_str, time_str = body.get("date"), body.get("time")
    if not date_str or not time_str:
        raise web.HTTPBadRequest(text=json.dumps({"error": "date_and_time_required"}))

    async with async_session_maker() as session:
        ok = await slot_service.delete_slot(session, date_str, time_str)

    if not ok:
        raise web.HTTPBadRequest(text=json.dumps({"error": "cannot_delete"}))

    return web.json_response({"ok": True})


# ==================== Админ: клиенты, прогресс, домашние задания ====================

@routes.get("/api/miniapp/admin/clients")
async def api_admin_clients(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    search = request.query.get("q")

    async with async_session_maker() as session:
        users = await list_users(session, search=search)

    return web.json_response(
        [
            {
                "id": u.id,
                "parent_name": u.parent_name,
                "child_name": u.child_name,
                "child_age": u.child_age,
                "username": u.username,
                "display_name": u.display_name(),
            }
            for u in users
        ]
    )


@routes.get("/api/miniapp/admin/clients/{user_id}/progress")
async def api_admin_client_progress(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    user_id = int(request.match_info["user_id"])

    async with async_session_maker() as session:
        notes = await progress_service.get_progress_notes(session, user_id)
        homework = await progress_service.get_homework(session, user_id)
        bookings = await slot_service.get_user_bookings(session, user_id)

    return web.json_response(
        {
            "notes": [_serialize_progress(n) for n in notes],
            "homework": [_serialize_homework(h) for h in homework],
            "bookings": [_serialize_booking(b) for b in bookings],
        }
    )


@routes.post("/api/miniapp/admin/progress/add")
async def api_admin_progress_add(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    user_id = body.get("user_id")
    title = (body.get("title") or "").strip()
    if not user_id or not title:
        raise web.HTTPBadRequest(text=json.dumps({"error": "user_id_and_title_required"}))

    async with async_session_maker() as session:
        note = await progress_service.add_progress_note(
            session,
            user_id=user_id,
            title=title,
            before_text=body.get("before_text"),
            after_text=body.get("after_text"),
            note=body.get("note"),
        )
        target_user = await session.get(User, user_id)

    bot = request.app["bot"]
    if target_user:
        await notify_progress_added(bot, target_user, title)

    return web.json_response({"ok": True, "note": _serialize_progress(note)})


@routes.post("/api/miniapp/admin/progress/delete")
async def api_admin_progress_delete(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    async with async_session_maker() as session:
        ok = await progress_service.delete_progress_note(session, body.get("id"))
    return web.json_response({"ok": ok})


@routes.post("/api/miniapp/admin/homework/add")
async def api_admin_homework_add(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    user_id = body.get("user_id")
    text = (body.get("text") or "").strip()
    if not user_id or not text:
        raise web.HTTPBadRequest(text=json.dumps({"error": "user_id_and_text_required"}))

    async with async_session_maker() as session:
        hw = await progress_service.add_homework(session, user_id=user_id, text=text)
        target_user = await session.get(User, user_id)

    bot = request.app["bot"]
    if target_user:
        await notify_homework_added(bot, target_user, text)

    return web.json_response({"ok": True, "homework": _serialize_homework(hw)})


@routes.post("/api/miniapp/admin/homework/delete")
async def api_admin_homework_delete(request: web.Request) -> web.Response:
    _user, tg_data = await _authenticate(request)
    _require_admin(tg_data)
    body = await request.json()
    async with async_session_maker() as session:
        ok = await progress_service.delete_homework(session, body.get("id"))
    return web.json_response({"ok": ok})

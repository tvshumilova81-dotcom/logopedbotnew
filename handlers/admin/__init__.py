from aiogram import Router

from filters.admin import IsAdmin
from handlers.admin import broadcast, export, materials_admin, notifications, stats, users

admin_router = Router(name="admin_root")
admin_router.message.filter(IsAdmin())

admin_router.include_router(notifications.router)
admin_router.include_router(broadcast.router)
admin_router.include_router(stats.router)
admin_router.include_router(users.router)
admin_router.include_router(export.router)
admin_router.include_router(materials_admin.router)

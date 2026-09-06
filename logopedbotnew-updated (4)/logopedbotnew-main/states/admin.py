from aiogram.fsm.state import State, StatesGroup


class BroadcastForm(StatesGroup):
    waiting_content = State()
    confirm = State()


class MaterialAdminForm(StatesGroup):
    title = State()
    description = State()
    price = State()
    file = State()
    cover = State()
    confirm = State()


class UserSearchForm(StatesGroup):
    query = State()

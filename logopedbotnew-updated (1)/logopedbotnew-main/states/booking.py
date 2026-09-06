from aiogram.fsm.state import State, StatesGroup


class BookingForm(StatesGroup):
    parent_name = State()
    child_name = State()
    child_age = State()
    child_gender = State()
    country = State()
    country_manual = State()
    timezone = State()
    problem = State()
    concern = State()
    noticed_since = State()
    saw_speech_therapist = State()
    specialists_reports = State()
    convenient_days = State()
    convenient_time = State()
    confirm = State()

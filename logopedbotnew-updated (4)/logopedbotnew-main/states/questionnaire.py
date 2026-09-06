from aiogram.fsm.state import State, StatesGroup


class QuestionnaireForm(StatesGroup):
    # Общая информация
    child_name = State()
    child_age = State()
    attends_kindergarten = State()
    attends_school = State()
    native_language = State()
    second_language = State()

    # Развитие речи
    says_single_words = State()
    says_short_sentences = State()
    says_long_sentences = State()
    tells_about_day = State()
    likes_talking = State()
    answers_questions = State()
    understands_speech = State()
    follows_instructions = State()
    is_understood_by_others = State()

    # Произношение
    pronunciation_difficulties = State()
    pronunciation_details = State()

    # Поведение
    focuses_20_min = State()
    gets_distracted = State()
    likes_books = State()
    likes_board_games = State()
    likes_drawing = State()
    likes_modelling = State()
    behavior_difficulties = State()
    peer_communication_difficulties = State()

    # Навыки
    dresses_independently = State()
    puts_away_toys = State()
    follows_instructions_skill = State()
    repeats_movements = State()
    repeats_words = State()
    repeats_sentences = State()
    remembers_poems = State()

    # Медицинская информация
    neurologist_consult = State()
    ent_consult = State()
    psychologist_consult = State()
    had_speech_therapist = State()
    specialist_reports = State()
    hearing_problems = State()
    pregnancy_birth_features = State()

    # Дополнительно
    additional_info = State()

from aiogram.fsm.state import State, StatesGroup

class SurveyStates(StatesGroup):
    """
    Состояния для опроса пользователя.
    """
    answering_questions = State()  # Пользователь отвечает на вопросы опроса

class ProfileStates(StatesGroup):
    """
    Состояния для работы с профилем пользователя.
    """
    viewing = State()  # Пользователь просматривает свой профиль
    editing = State()  # Пользователь редактирует свой профиль

class MeditationStates(StatesGroup):
    """
    Состояния для работы с медитациями.
    """
    selecting_type = State()  # Пользователь выбирает тип медитации
    waiting_for_generation = State()  # Ожидание генерации аудио-медитации

class ReminderStates(StatesGroup):
    """
    Состояния для работы с напоминаниями.
    """
    main_menu = State()      # Главное меню напоминаний
    selecting_days = State()  # Пользователь выбирает дни для напоминаний
    selecting_time = State()  # Пользователь выбирает время для напоминаний
    confirming = State()  # Пользователь подтверждает настройки напоминаний 
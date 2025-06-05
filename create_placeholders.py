#!/usr/bin/env python
"""
Скрипт для создания заглушек недостающих модулей бота.
Запускается в начале сборки в Railway.
"""

import os
import logging
import sys
from pathlib import Path

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [PLACEHOLDER] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("placeholders")

# Список модулей, которые должны быть в проекте
REQUIRED_MODULES = {
    "button_states.py": """
from aiogram.fsm.state import State, StatesGroup

class SurveyStates(StatesGroup):
    \"\"\"
    Состояния для опроса пользователя.
    \"\"\"
    answering_questions = State()  # Пользователь отвечает на вопросы опроса

class ProfileStates(StatesGroup):
    \"\"\"
    Состояния для работы с профилем пользователя.
    \"\"\"
    viewing = State()  # Пользователь просматривает свой профиль
    editing = State()  # Пользователь редактирует свой профиль

class MeditationStates(StatesGroup):
    \"\"\"
    Состояния для работы с медитациями.
    \"\"\"
    selecting_type = State()  # Пользователь выбирает тип медитации
    waiting_for_generation = State()  # Ожидание генерации аудио-медитации

class ReminderStates(StatesGroup):
    \"\"\"
    Состояния для работы с напоминаниями.
    \"\"\"
    main_menu = State()      # Главное меню напоминаний
    selecting_days = State()  # Пользователь выбирает дни для напоминаний
    selecting_time = State()  # Пользователь выбирает время для напоминаний
    confirming = State()  # Пользователь подтверждает настройки напоминаний
""",

    "services/__init__.py": """
# Инициализация пакета services
from services.recs import generate_response
from services.stt import process_voice_message
from services.tts import generate_audio
""",

    "services/tts.py": """
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

async def generate_voice(text: str, user_id: int, voice_id: str = "default") -> Optional[str]:
    \"\"\"
    Генерирует аудиофайл из текста.
    
    Args:
        text: Текст для озвучивания
        user_id: ID пользователя
        voice_id: ID голоса в ElevenLabs
        
    Returns:
        Optional[str]: Путь к созданному файлу или None в случае ошибки
    \"\"\"
    logger.info(f"Генерация голоса для пользователя {user_id} (заглушка)")
    
    try:
        # Создаем имя файла
        file_id = str(uuid.uuid4())
        file_path = f"tmp/{user_id}_{file_id}.mp3"
        
        # В заглушке просто создаем пустой файл
        os.makedirs("tmp", exist_ok=True)
        with open(file_path, "w") as f:
            f.write("# Placeholder audio file")
            
        logger.info(f"Создан заглушка аудиофайла: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Ошибка при создании заглушки аудиофайла: {e}")
        return None
""",

    "communication_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки коммуникаций
communication_handler_router = Router(name="communication_handler")

@communication_handler_router.message(Command("communicate"))
async def handle_communicate(message: Message):
    \"\"\"
    Обработчик команды /communicate
    \"\"\"
    await message.answer(
        "Это заглушка для функции коммуникации. Реальный модуль не загружен."
    )

async def generate_personalized_response(message_text, user_profile, conversation_history=None):
    \"\"\"
    Заглушка для генерации персонализированного ответа.
    \"\"\"
    return "Это заглушка для персонализированного ответа. Реальный модуль не загружен."

async def get_personality_type_from_profile(profile_text):
    \"\"\"
    Заглушка для определения типа личности из профиля.
    \"\"\"
    return "Интеллектуальный"
""",

    "survey_handler.py": """
import logging
from typing import Dict, Any, Optional, List, Tuple
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from button_states import SurveyStates, ProfileStates

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки опроса
survey_router = Router(name="survey")

# Функция для получения основной клавиатуры
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает основную клавиатуру бота.
    
    Returns:
        ReplyKeyboardMarkup: Основная клавиатура бота
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Опрос"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🧘 Медитации"), KeyboardButton(text="⏰ Напоминания")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="💬 Помощь")],
        ],
        resize_keyboard=True
    )
    return keyboard

# Обработчик команды опроса
@survey_router.message(Command("survey"))
@survey_router.message(F.text == "📝 Опрос")
async def cmd_survey(message: Message, state: FSMContext):
    """
    Обработчик команды /survey
    """
    await message.answer(
        "Это заглушка для функции опроса. Реальный модуль не загружен.",
        reply_markup=get_main_keyboard()
    )
    await state.set_state(SurveyStates.answering_questions)

@survey_router.message(Command("profile"))
@survey_router.message(F.text == "👤 Профиль")
async def cmd_profile(message: Message, state: FSMContext):
    """
    Обработчик команды /profile
    """
    await message.answer(
        "Это заглушка для функции профиля. Реальный модуль не загружен.",
        reply_markup=get_main_keyboard()
    )
    await state.set_state(ProfileStates.viewing)
""",

    "meditation_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from button_states import MeditationStates

# Импорт сервиса TTS
try:
    from services.tts import generate_voice
except ImportError:
    # Если не удалось импортировать, создаем заглушку
    async def generate_voice(text, user_id, voice_id="default"):
        logging.warning("Используется заглушка для generate_voice")
        return None

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки медитаций
meditation_router = Router(name="meditation")

@meditation_router.message(Command("meditate"))
@meditation_router.message(F.text == "🧘 Медитации")
async def cmd_meditate(message: Message, state: FSMContext):
    """
    Обработчик команды /meditate
    """
    await message.answer(
        "Это заглушка для функции медитации. Реальный модуль не загружен."
    )
    await state.set_state(MeditationStates.selecting_type)
""",

    "conversation_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

# Пытаемся импортировать модуль communication_handler
try:
    from communication_handler import communication_handler_router
except ImportError:
    # Если не удалось импортировать, создаем заглушку
    logging.warning("Не удалось импортировать communication_handler_router, используется заглушка")
    from aiogram import Router
    communication_handler_router = Router(name="communication_handler")

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки диалогов
conversation_router = Router(name="conversation")

@conversation_router.message()
async def handle_message(message: Message):
    """
    Обработчик сообщений пользователя
    """
    # Заглушка для обработки обычных сообщений
    if message.text and not message.text.startswith('/') and not message.text.startswith('📝') and not message.text.startswith('👤') and not message.text.startswith('🧘') and not message.text.startswith('⏰') and not message.text.startswith('💡') and not message.text.startswith('💬'):
        await message.answer(
            "Это заглушка для функции диалога. Реальный модуль не загружен."
        )
""",

    "reminder_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from button_states import ReminderStates
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем планировщик заданий
scheduler = AsyncIOScheduler()

# Создаем роутер для обработки напоминаний
reminder_router = Router(name="reminder")

@reminder_router.message(Command("reminder"))
@reminder_router.message(F.text == "⏰ Напоминания")
async def cmd_reminder(message: Message, state: FSMContext):
    """
    Обработчик команды /reminder
    """
    await message.answer(
        "Это заглушка для функции напоминаний. Реальный модуль не загружен."
    )
    await state.set_state(ReminderStates.main_menu)
""",

    "voice_handler.py": """
import logging
from aiogram import Router, F
from aiogram.types import Message, Voice
from aiogram.filters import Command

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработки голосовых сообщений
voice_router = Router(name="voice")

@voice_router.message(F.voice)
async def handle_voice(message: Message):
    """
    Обработчик голосовых сообщений
    """
    await message.answer(
        "Это заглушка для функции обработки голосовых сообщений. Реальный модуль не загружен."
    )
""",

    "profile_generator.py": """
import logging
from typing import Dict, Any, Optional

# Настройка логирования
logger = logging.getLogger(__name__)

async def generate_profile(user_id: int, answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Генерирует профиль пользователя на основе ответов.
    
    Args:
        user_id: ID пользователя
        answers: Ответы пользователя
        
    Returns:
        Optional[Dict[str, Any]]: Профиль пользователя или None в случае ошибки
    """
    logger.info(f"Генерация профиля для пользователя {user_id} (заглушка)")
    
    # Создаем базовый профиль (заглушка)
    profile = {
        "user_id": user_id,
        "personality_type": "Не определен",
        "strengths": ["Аналитическое мышление", "Коммуникабельность", "Творческий подход"],
        "created": "2025-05-23"
    }
    
    return profile
"""
}

def create_placeholder_files():
    """
    Создает заглушки для недостающих модулей бота.
    """
    logger.info("Начало создания заглушек для модулей бота")
    
    # Проверяем и создаем заглушки для каждого модуля
    for module_file, module_content in REQUIRED_MODULES.items():
        if not os.path.exists(module_file):
            try:
                logger.info(f"Создание заглушки для {module_file}")
                
                # Убедимся, что директория существует
                os.makedirs(os.path.dirname(module_file) if os.path.dirname(module_file) else '.', exist_ok=True)
                
                with open(module_file, "w", encoding="utf-8") as f:
                    f.write(f"# Placeholder for {module_file}\n")
                    f.write("# This file was automatically created by create_placeholders.py for Railway deployment\n")
                    f.write(module_content.strip())
                
                logger.info(f"Заглушка для {module_file} успешно создана")
                
                # Проверка, что файл действительно создан
                if os.path.exists(module_file):
                    file_size = os.path.getsize(module_file)
                    logger.info(f"Заглушка {module_file} создана успешно. Размер файла: {file_size} байт")
                else:
                    logger.error(f"Не удалось создать заглушку {module_file} (файл не найден после создания)")
            except Exception as e:
                logger.error(f"Ошибка при создании заглушки для {module_file}: {e}")
        else:
            logger.info(f"Файл {module_file} уже существует, проверка содержимого...")
            try:
                # Проверяем размер файла
                file_size = os.path.getsize(module_file)
                if file_size == 0:
                    logger.warning(f"Файл {module_file} существует, но имеет нулевой размер. Создаем заглушку заново.")
                    with open(module_file, "w", encoding="utf-8") as f:
                        f.write(f"# Placeholder for {module_file} (re-created due to zero size)\n")
                        f.write("# This file was automatically created by create_placeholders.py for Railway deployment\n")
                        f.write(module_content.strip())
                    logger.info(f"Заглушка для {module_file} повторно создана")
                elif 'button_states.py' in module_file:
                    # Для button_states.py проверяем наличие ProfileStates
                    with open(module_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Более точная проверка на наличие класса ProfileStates
                    if 'class ProfileStates' not in content or 'viewing = State()' not in content:
                        logger.warning(f"Файл {module_file} существует, но не содержит класс ProfileStates или необходимые методы. Создаем заглушку заново.")
                        with open(module_file, "w", encoding="utf-8") as f:
                            f.write(f"# Placeholder for {module_file} (re-created due to missing or incomplete ProfileStates)\n")
                            f.write("# This file was automatically created by create_placeholders.py for Railway deployment\n")
                            f.write(module_content.strip())
                        logger.info(f"Заглушка для {module_file} повторно создана")
                    else:
                        logger.info(f"Файл {module_file} уже существует и содержит все необходимые классы и методы")
                else:
                    logger.info(f"Файл {module_file} уже существует и не пустой (размер: {file_size} байт)")
            except Exception as e:
                logger.error(f"Ошибка при проверке существующего файла {module_file}: {e}")
    
    logger.info("Завершено создание заглушек для модулей бота")

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК СКРИПТА СОЗДАНИЯ ЗАГЛУШЕК ДЛЯ RAILWAY")
    print("=" * 50)
    
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Файлы в текущей директории: {[f for f in os.listdir('.') if f.endswith('.py')]}")
    
    # Создаем необходимые директории
    os.makedirs("logs", exist_ok=True)
    os.makedirs("tmp", exist_ok=True)
    os.makedirs("services", exist_ok=True)
    logger.info("Созданы директории logs, tmp и services")
    
    create_placeholder_files()
    
    print("=" * 50)
    print("ЗАВЕРШЕНИЕ СКРИПТА СОЗДАНИЯ ЗАГЛУШЕК")
    print("=" * 50) 
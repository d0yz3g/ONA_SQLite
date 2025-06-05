import asyncio
import logging
import os
import sys
import tempfile  # Для создания временного файла блокировки
import socket  # Для получения имени хоста
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.mongo import MongoStorage
from dotenv import load_dotenv
from aiogram.types import BufferedInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from motor.motor_asyncio import AsyncIOMotorClient

# Импортируем fcntl только для Unix-подобных систем
if sys.platform != 'win32':
    try:
        import fcntl
    except ImportError:
        fcntl = None
else:
    fcntl = None

# Блокировка для предотвращения запуска нескольких экземпляров
LOCK_FILE = os.path.join(tempfile.gettempdir(), 'ona_bot.lock')
lock_socket = None
lock_file_handle = None


def acquire_lock():
    """
    Пытается получить блокировку, предотвращающую запуск нескольких экземпляров.

    Returns:
        bool: True, если блокировка получена успешно, False в противном случае
    """
    global lock_socket, lock_file_handle

    try:
        # Создаем именованный сокет для Windows
        if sys.platform == 'win32':
            lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Пытаемся занять порт 50000 (или любой другой специфичный для вашего приложения)
            try:
                lock_socket.bind(('localhost', 50000))
                print("Блокировка получена (Windows)")
                return True
            except socket.error:
                print("Блокировка уже занята другим процессом (Windows)")
                return False
        # Для Unix-подобных систем используем файловую блокировку
        elif fcntl:
            lock_file_handle = open(LOCK_FILE, 'w')
            try:
                fcntl.lockf(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                print("Блокировка получена (Unix с fcntl)")
                return True
            except IOError:
                print("Блокировка уже занята другим процессом (Unix)")
                return False
        # Если fcntl недоступен, используем альтернативный метод
        else:
            # Простая проверка на существование PID файла
            if os.path.exists(LOCK_FILE):
                with open(LOCK_FILE, 'r') as f:
                    pid = f.read().strip()
                    # Проверяем, существует ли процесс с таким PID
                    try:
                        pid = int(pid)
                        # Пытаемся отправить сигнал 0 процессу - это проверка на существование
                        os.kill(pid, 0)
                        print(f"Блокировка уже занята процессом {pid}")
                        return False
                    except (ValueError, OSError):
                        # PID невалидный или процесс не существует
                        pass

            # Записываем текущий PID в файл
            with open(LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
            print("Блокировка получена (PID файл)")
            return True
    except Exception as e:
        print(f"Ошибка при получении блокировки: {e}")
        return False


def release_lock():
    """
    Освобождает блокировку, полученную с помощью acquire_lock().
    """
    global lock_socket, lock_file_handle

    try:
        # Освобождаем сокет для Windows
        if lock_socket:
            try:
                lock_socket.close()
                print("Блокировка освобождена (Windows)")
            except Exception as e:
                print(f"Ошибка при освобождении сокета: {e}")

        # Освобождаем файловую блокировку для Unix
        if lock_file_handle:
            try:
                if fcntl:
                    fcntl.lockf(lock_file_handle, fcntl.LOCK_UN)
                lock_file_handle.close()
                print("Блокировка освобождена (Unix)")
            except Exception as e:
                print(f"Ошибка при освобождении файловой блокировки: {e}")

        # Удаляем PID файл, если использовался такой метод
        if os.path.exists(LOCK_FILE) and sys.platform == 'win32' or not fcntl:
            try:
                os.remove(LOCK_FILE)
                print("PID файл удален")
            except Exception as e:
                print(f"Ошибка при удалении PID файла: {e}")
    except Exception as e:
        print(f"Ошибка при освобождении блокировки: {e}")


# Загружаем переменные окружения из .env
load_dotenv()

# Проверка наличия railway_helper и его инициализация
try:
    from railway_helper import ensure_modules_available, print_railway_info
    # Проверяем и обеспечиваем наличие необходимых модулей
    print_railway_info("Инициализация Railway Helper", "INFO")
    ensure_modules_available([
        "survey_handler",
        "meditation_handler",
        "conversation_handler",
        "reminder_handler",
        "voice_handler",
        "railway_logging",
        "communication_handler"
    ])
except ImportError:
    print("БОТ: Railway Helper не найден, продолжаем без дополнительных проверок")

# Импортируем настройку логирования для Railway
try:
    from railway_logging import setup_railway_logging, railway_print
    # Настраиваем логирование для Railway
    logger = setup_railway_logging("ona_bot", logging.INFO)
    railway_print("Логирование для Railway настроено успешно", "INFO")
except ImportError:
    # Стандартная настройка логирования, если модуль railway_logging не найден
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log")
        ]
    )
    logger = logging.getLogger(__name__)
    print("БОТ: Используется стандартное логирование (railway_logging не найден)")

    # Определяем функцию railway_print, если модуль railway_logging не найден
    def railway_print(message, level="INFO"):
        prefix = "ИНФО"
        if level.upper() == "ERROR":
            prefix = "ОШИБКА"
        elif level.upper() == "WARNING":
            prefix = "ПРЕДУПРЕЖДЕНИЕ"
        elif level.upper() == "DEBUG":
            prefix = "ОТЛАДКА"
        print(f"{prefix}: {message}")
        sys.stdout.flush()

# Информация о запуске
railway_print("=== ONA TELEGRAM BOT STARTING ===", "INFO")
railway_print(f"Python version: {sys.version}", "INFO")
railway_print(f"Current working directory: {os.getcwd()}", "INFO")
railway_print(
    f"Files in directory: {[f for f in os.listdir('.') if f.endswith('.py')]}", "INFO")

# Загружаем API токен из .env файла
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в .env файле")
    railway_print("BOT_TOKEN не найден в .env файле", "ERROR")
    sys.exit(1)
else:
    railway_print("BOT_TOKEN найден успешно", "INFO")

# Проверка наличия psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
    logger.info("Библиотека psutil успешно импортирована")
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning(
        "Библиотека psutil не установлена, некоторые функции будут недоступны")

# Импортируем роутеры
try:
    railway_print("Импорт основных модулей бота...", "INFO")
    from survey_handler import survey_router, get_main_keyboard
    from voice_handler import voice_router
    from conversation_handler import conversation_router
    from meditation_handler import meditation_router
    from reminder_handler import reminder_router, scheduler
    railway_print("Все модули успешно импортированы", "INFO")
except ImportError as e:
    logger.error(f"Ошибка импорта модулей: {e}")
    railway_print(f"Ошибка импорта модулей: {e}", "ERROR")
    railway_print("Попытка аварийной загрузки базовых модулей...", "WARNING")

    # Попытка аварийной загрузки базовых модулей
    # Создаем пустые роутеры
    from aiogram import Router
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    survey_router = Router(name="survey")
    voice_router = Router(name="voice")
    conversation_router = Router(name="conversation")
    meditation_router = Router(name="meditation")
    reminder_router = Router(name="reminder")

    # Создаем базовую клавиатуру
    def get_main_keyboard():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Опрос"),
                 KeyboardButton(text="💬 Помощь")]
            ],
            resize_keyboard=True
        )

    # Создаем пустой планировщик
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()

    railway_print("Аварийная загрузка базовых модулей выполнена", "WARNING")

# Подключения к MongoDB
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "aiogram_fsm_db")
mongo_client = AsyncIOMotorClient(MONGO_URL)

# Создаем экземпляр бота и диспетчер
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,  # Устанавливаем HTML-разметку по умолчанию
        link_preview_is_disabled=True,  # Отключаем предпросмотр веб-страниц
        protect_content=False  # Разрешаем пересылку сообщений
    )
)
dp = Dispatcher(storage=MongoStorage(
    client=mongo_client,
    db_name=DB_NAME
))

# Регистрируем роутеры в правильном порядке
# Сначала регистрируем роутер опроса, чтобы он имел приоритет при обработке сообщений в состоянии опроса
dp.include_router(survey_router)
# Затем регистрируем роутер голосовых сообщений
dp.include_router(voice_router)
# Далее регистрируем остальные роутеры
dp.include_router(meditation_router)
dp.include_router(reminder_router)
# Регистрируем роутер обычных сообщений последним
dp.include_router(conversation_router)

# Обработчик команды /start


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    # Приветственное сообщение
    greeting_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я <b>ОНА</b> - твой Осознанный Наставник и Аналитик.\n\n"
        "Я помогу тебе:\n"
        "• 🧠 Определить твои сильные стороны и таланты\n"
        "• 💡 Дать персонализированные советы\n"
        "• 🌱 Поддержать в развитии и росте\n\n"
        "Чтобы создать твой <b>психологический профиль</b>, нужно пройти опрос из 34 вопросов. "
        "Это займет около 10-15 минут.\n\n"
        "Готов начать?"
    )

    # Используем единую клавиатуру из survey_handler
    keyboard = get_main_keyboard()

    # Отправляем приветственное сообщение
    await message.answer(
        greeting_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

# Обработчик команды /help


@dp.message(Command("help"))
@dp.message(F.text == "💬 Помощь")
async def cmd_help(message: Message):
    """
    Обработчик команды /help
    """
    help_text = (
        "🔍 <b>Основные команды и возможности:</b>\n\n"
        "• /start - Начать работу с ботом\n"
        "• /survey или 📝 Опрос - Пройти опрос для создания профиля\n"
        "• /profile или 👤 Профиль - Посмотреть свой психологический профиль\n"
        "• /meditate или 🧘 Медитации - Получить аудио-медитацию\n"
        "• /reminders или ⏰ Напоминания - Настроить напоминания о практиках\n"
        "• /advice или 💡 Советы - Получить персонализированный совет на основе типа личности\n"
        "• /restart или 🔄 Рестарт - Перезапустить бота\n"
        "• /cancel или ❌ Отменить - Отменить текущее действие\n\n"
        "🗣 <b>Как пользоваться ботом:</b>\n\n"
        "1. Пройдите опрос из 34 вопросов\n"
        "2. Получите свой психологический профиль\n"
        "3. Узнайте ваш тип личности (Интеллектуальный, Эмоциональный, Практический или Творческий)\n"
        "4. Получайте персонализированные советы, соответствующие вашему типу личности\n"
        "5. Общайтесь со мной текстом или голосовыми сообщениями\n"
        "6. Я буду отвечать с учетом ваших психологических особенностей\n\n"
        "💡 <b>Если возникнут вопросы или проблемы:</b>\n"
        "• Напишите \"Помощь\" или используйте команду /help\n"
    )

    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

# Обработчик команды /api_key


@dp.message(Command("api_key"))
async def cmd_api_key(message: Message):
    """
    Обработчик команды /api_key - отображает инструкции по настройке API ключа OpenAI
    """
    try:
        with open('api_key_instructions.md', 'r', encoding='utf-8') as f:
            instructions = f.read()

        instructions_text = (
            "🔑 <b>Инструкции по настройке API ключа OpenAI</b>\n\n"
            "Если бот отвечает шаблонными сообщениями и не генерирует уникальные ответы, "
            "необходимо настроить API ключ OpenAI.\n\n"
            "Краткая инструкция:\n"
            "1. Получите API ключ на сайте OpenAI Platform\n"
            "2. Откройте файл .env в корневой директории\n"
            "3. Установите ключ в параметр OPENAI_API_KEY\n"
            "4. Перезапустите бота\n\n"
            "Полные инструкции отправлены отдельным файлом."
        )

        # Отправляем краткую информацию
        await message.answer(
            instructions_text,
            parse_mode="HTML"
        )

        # Отправляем файл с полными инструкциями
        await message.answer_document(
            document=BufferedInputFile(
                instructions.encode('utf-8'),
                filename="api_key_setup_instructions.md"
            ),
            caption="Подробные инструкции по настройке API ключа OpenAI"
        )

        logger.info(
            f"Отправлены инструкции по настройке API ключа пользователю {message.from_user.id}")

    except Exception as e:
        logger.error(f"Ошибка при отправке инструкций по API ключу: {e}")
        await message.answer(
            "К сожалению, не удалось отправить инструкции. Пожалуйста, обратитесь к администратору бота."
        )

# Обработчик команды /restart


@dp.message(Command("restart"))
@dp.message(F.text == "🔄 Рестарт")
async def cmd_restart(message: Message):
    """
    Обработчик команды /restart
    """
    # Отправляем сообщение о перезапуске
    await message.answer(
        "🔄 <b>Бот перезапущен!</b>\n\n"
        "Начинаем заново. Если вы хотите сбросить свой профиль, "
        "воспользуйтесь кнопкой 📝 Опрос и подтвердите перезапуск.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

# Функция для инициализации планировщика


async def start_scheduler():
    if scheduler and not scheduler.running:
        scheduler.start()
        logger.info("Планировщик заданий запущен")


async def main():
    """
    Главная функция запуска бота
    """
    # Проверяем, что нет другого запущенного экземпляра
    if not acquire_lock():
        logger.error("Другой экземпляр бота уже запущен. Завершение работы.")
        railway_print(
            "КРИТИЧЕСКАЯ ОШИБКА: Обнаружен другой запущенный экземпляр бота. Завершение работы.", "ERROR")
        return

    # Инициализируем бот
    logger.info("Бот ОНА запускается...")
    railway_print("Запуск основного цикла бота...", "INFO")

    try:
        # Удаляем все обновления, которые были пропущены (если бот был отключен)
        await bot.delete_webhook(drop_pending_updates=True)
        railway_print("Старые обновления удалены", "INFO")

        # Удаляем webhook (если он был установлен)
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            await bot.delete_webhook()
            logger.info("Webhook удален, старые обновления очищены")

        # Завершаем потенциально запущенные сессии бота (для предотвращения конфликтов)
        if hasattr(bot, "session") and bot.session:
            try:
                await bot.session.close()
                logger.info("Существующая сессия бота закрыта")
            except Exception as e:
                logger.warning(f"Не удалось закрыть существующую сессию: {e}")

        # Создаем новую сессию
        bot._session = None  # Сбрасываем текущую сессию, чтобы создать новую

        # Проверяем соединение с Telegram API
        bot_info = await bot.get_me()
        logger.info(
            f"Соединение с Telegram API установлено успешно. Имя бота: @{bot_info.username}")
        railway_print(
            f"Бот @{bot_info.username} успешно подключен к Telegram API", "INFO")

        # Запускаем планировщик заданий
        await start_scheduler()

        # Сообщение о готовности бота
        railway_print("=== ONA BOT ЗАПУЩЕН И ГОТОВ К РАБОТЕ ===", "INFO")

        # Запускаем бота с длинным поллингом и параметрами для предотвращения конфликтов
        await dp.start_polling(bot, fast=True, timeout=60, allowed_updates=None, polling_timeout=60)
    except Exception as e:
        # Проверяем, является ли ошибка конфликтом запросов
        if "Conflict: terminated by other getUpdates" in str(e) or "TelegramConflictError" in str(e):
            logger.error(
                "Обнаружен конфликт запросов Telegram API - другой экземпляр бота уже запущен")
            railway_print(
                "КОНФЛИКТ: Другой экземпляр бота уже получает обновления. Выполняем повторную попытку через 10 секунд...", "ERROR")

            # Делаем паузу и пробуем снова
            await asyncio.sleep(10)
            railway_print(
                "Повторная попытка запуска после конфликта...", "INFO")

            try:
                # Создаем новую сессию
                if hasattr(bot, "session") and bot.session:
                    await bot.session.close()
                bot._session = None

                # Пробуем запустить снова
                await dp.start_polling(bot, fast=True, timeout=60, allowed_updates=None, polling_timeout=60)
                railway_print("Повторный запуск выполнен успешно!", "INFO")
            except Exception as retry_error:
                logger.error(
                    f"Повторная попытка запуска не удалась: {retry_error}")
                railway_print(
                    f"Повторная попытка не удалась: {str(retry_error)}", "ERROR")

                # Если мы запускаемся из restart_bot.py, повторный запуск будет выполнен автоматически
                if 'restart_bot.py' in sys.argv[0]:
                    railway_print(
                        "Ожидаем перезапуска через монитор...", "INFO")
                else:
                    railway_print(
                        "Рекомендуется запускать бота через restart_bot.py для автоматического перезапуска", "WARNING")
        else:
            logger.error(f"Ошибка запуска бота: {e}")
            railway_print(f"Ошибка запуска: {str(e)}", "ERROR")
    finally:
        # Освобождаем блокировку при завершении
        release_lock()

        # Останавливаем планировщик заданий при выходе
        if scheduler and scheduler.running:
            scheduler.shutdown()
            logger.info("Планировщик заданий остановлен")

        if hasattr(bot, "session") and bot.session:
            await bot.session.close()
            logger.info("Сессия бота закрыта")

        railway_print("Бот завершил работу", "INFO")

if __name__ == "__main__":
    # Запускаем бота
    asyncio.run(main())

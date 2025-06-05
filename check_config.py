#!/usr/bin/env python
"""
Скрипт для проверки конфигурации окружения и импортов
"""

import os
import sys
import importlib
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("check_config")

def check_environment():
    """Проверка переменных окружения"""
    print("=== Проверка переменных окружения ===")
    
    required_env_vars = ["BOT_TOKEN", "OPENAI_API_KEY", "ELEVEN_API_KEY"]
    missing_env_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Установлен")
        else:
            print(f"❌ {var}: Не установлен")
            missing_env_vars.append(var)
    
    return missing_env_vars

def check_imports():
    """Проверка импортов"""
    print("\n=== Проверка импортов ===")
    
    modules_to_check = [
        ("aiogram", "Библиотека для работы с Telegram API"),
        ("openai", "Библиотека для работы с OpenAI API"),
        ("apscheduler", "Библиотека для планирования задач"),
        ("httpx", "HTTP клиент для асинхронных запросов"),
        ("dotenv", "Библиотека для работы с .env файлами")
    ]
    
    missing_modules = []
    
    for module_name, description in modules_to_check:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}: Установлен ({description})")
        except ImportError:
            print(f"❌ {module_name}: Не установлен ({description})")
            missing_modules.append(module_name)
    
    return missing_modules

def check_project_structure():
    """Проверка структуры проекта"""
    print("\n=== Проверка структуры проекта ===")
    
    files_to_check = [
        ("main.py", "Основной файл бота"),
        ("button_bot.py", "Модуль с обработчиками бота"),
        ("button_states.py", "Модуль с состояниями FSM"),
        ("questions.py", "Модуль с вопросами для опроса"),
        ("services/recs.py", "Модуль с функциями генерации ответов"),
        ("services/stt.py", "Модуль для обработки голосовых сообщений")
    ]
    
    missing_files = []
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: Существует ({description})")
        else:
            print(f"❌ {file_path}: Не существует ({description})")
            missing_files.append(file_path)
    
    return missing_files

def check_services_imports():
    """Проверка импортов в сервисных модулях"""
    print("\n=== Проверка импортов в сервисных модулях ===")
    
    # Убедимся, что директория services в пути для импорта
    if not os.path.exists("services"):
        print("❌ Директория services не найдена")
        return False
    
    try:
        # Проверяем импорт из services.recs
        from services.recs import generate_response
        print("✅ services.recs.generate_response: Импортирован успешно")
    except ImportError as e:
        print(f"❌ services.recs.generate_response: Ошибка импорта - {e}")
        return False
    
    try:
        # Проверяем импорт из services.stt
        from services.stt import process_voice_message
        print("✅ services.stt.process_voice_message: Импортирован успешно")
    except ImportError as e:
        print(f"❌ services.stt.process_voice_message: Ошибка импорта - {e}")
        return False
    
    return True

def main():
    """Основная функция проверки"""
    print("=== Начало проверки конфигурации ===\n")
    
    # Проверка переменных окружения
    missing_env_vars = check_environment()
    
    # Проверка импортов
    missing_modules = check_imports()
    
    # Проверка структуры проекта
    missing_files = check_project_structure()
    
    # Проверка импортов в сервисных модулях
    services_imports_ok = check_services_imports()
    
    print("\n=== Результаты проверки ===")
    
    if missing_env_vars:
        print(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing_env_vars)}")
        print("   Создайте файл .env и добавьте необходимые переменные.")
    else:
        print("✅ Все необходимые переменные окружения установлены.")
    
    if missing_modules:
        print(f"⚠️ Отсутствуют модули: {', '.join(missing_modules)}")
        print("   Установите их с помощью pip: pip install " + " ".join(missing_modules))
    else:
        print("✅ Все необходимые модули установлены.")
    
    if missing_files:
        print(f"⚠️ Отсутствуют файлы: {', '.join(missing_files)}")
        print("   Убедитесь, что структура проекта соответствует требованиям.")
    else:
        print("✅ Все необходимые файлы найдены.")
    
    if not services_imports_ok:
        print("⚠️ Ошибки при импорте модулей из services.")
        print("   Проверьте структуру и содержимое файлов в директории services.")
    else:
        print("✅ Импорты из services работают корректно.")
    
    # Общее заключение
    if not missing_env_vars and not missing_modules and not missing_files and services_imports_ok:
        print("\n✅ Конфигурация в порядке! Бот готов к запуску.")
    else:
        print("\n⚠️ Обнаружены проблемы в конфигурации. Устраните их перед запуском бота.")

if __name__ == "__main__":
    main() 
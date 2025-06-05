#!/usr/bin/env python
"""
Скрипт для исправления путей импорта в Railway.
Добавляет текущий каталог в sys.path и проверяет доступность всех необходимых модулей.
"""

import os
import sys
import importlib
import logging
import pkgutil
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [FIX_IMPORTS] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fix_imports")

def fix_imports():
    """
    Исправляет проблемы с импортами, добавляя текущий каталог в sys.path.
    """
    # Получаем текущий рабочий каталог
    current_dir = os.getcwd()
    logger.info(f"Текущий рабочий каталог: {current_dir}")
    
    # Добавляем каталог в sys.path, если его там еще нет
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        logger.info(f"Добавлен каталог {current_dir} в sys.path")
    
    # Добавляем каталог services, если он существует
    services_dir = os.path.join(current_dir, "services")
    if os.path.exists(services_dir) and os.path.isdir(services_dir):
        if services_dir not in sys.path:
            sys.path.insert(0, services_dir)
            logger.info(f"Добавлен каталог {services_dir} в sys.path")
    
    # Выводим все каталоги в sys.path
    logger.info(f"sys.path содержит каталоги: {sys.path}")
    
    # Попытка импорта критических модулей
    check_critical_modules()
    
    # Выводим все .py файлы в текущем каталоге
    python_files = [f for f in os.listdir(current_dir) if f.endswith('.py')]
    logger.info(f"Python-файлы в текущем каталоге: {python_files}")
    
    # Выводим все .py файлы в services каталоге, если он существует
    if os.path.exists(services_dir) and os.path.isdir(services_dir):
        services_files = [f for f in os.listdir(services_dir) if f.endswith('.py')]
        logger.info(f"Python-файлы в каталоге services: {services_files}")

def check_critical_modules():
    """
    Проверяет, доступны ли критически важные модули.
    """
    critical_modules = [
        "button_states",
        "survey_handler",
        "meditation_handler",
        "conversation_handler",
        "reminder_handler",
        "voice_handler"
    ]
    
    logger.info("Проверка доступности критически важных модулей...")
    
    for module_name in critical_modules:
        try:
            module = importlib.import_module(module_name)
            logger.info(f"✓ Модуль {module_name} успешно импортирован")
        except ImportError as e:
            logger.error(f"✗ Ошибка импорта модуля {module_name}: {e}")
            # Здесь можно добавить автосоздание заглушек для отсутствующих модулей

def create_import_test_script():
    """
    Создает тестовый скрипт для проверки импортов.
    """
    test_file = "test_imports.py"
    
    with open(test_file, "w") as f:
        f.write("""#!/usr/bin/env python
import sys
import os

print("\\nТЕСТИРОВАНИЕ ИМПОРТОВ:")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")
print(f"Текущий каталог: {os.getcwd()}")
print(f"Файлы в текущем каталоге: {[f for f in os.listdir('.') if f.endswith('.py')]}")

try:
    from button_states import ProfileStates
    print("✓ Успешно импортирован ProfileStates из button_states")
except ImportError as e:
    print(f"✗ Ошибка импорта ProfileStates: {e}")

try:
    import survey_handler
    print("✓ Успешно импортирован survey_handler")
except ImportError as e:
    print(f"✗ Ошибка импорта survey_handler: {e}")

try:
    import meditation_handler
    print("✓ Успешно импортирован meditation_handler")
except ImportError as e:
    print(f"✗ Ошибка импорта meditation_handler: {e}")

try:
    from services.tts import generate_voice
    print("✓ Успешно импортирован generate_voice из services.tts")
except ImportError as e:
    print(f"✗ Ошибка импорта services.tts: {e}")
""")
    
    logger.info(f"Создан тестовый скрипт импортов: {test_file}")

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК СКРИПТА ИСПРАВЛЕНИЯ ИМПОРТОВ")
    print("=" * 50)
    
    fix_imports()
    create_import_test_script()
    
    print("=" * 50)
    print("ЗАВЕРШЕНИЕ СКРИПТА ИСПРАВЛЕНИЯ ИМПОРТОВ")
    print("=" * 50) 
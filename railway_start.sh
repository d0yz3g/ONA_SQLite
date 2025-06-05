#!/bin/bash

# Скрипт запуска для Railway
# Выполняет предварительные проверки и запускает бота

echo "=== ONA2.0 TELEGRAM BOT RAILWAY LAUNCHER ==="
echo "Дата запуска: $(date)"
echo "Рабочая директория: $(pwd)"

# Функция для проверки и создания файла
check_and_create() {
    local file="$1"
    local content="$2"
    
    if [ ! -f "$file" ]; then
        echo "ПРЕДУПРЕЖДЕНИЕ: Файл $file не найден, создаем заглушку..."
        echo "$content" > "$file"
        echo "✓ Создана заглушка для файла $file"
    else
        echo "✓ Файл $file найден"
    fi
}

# Вывод информации о рабочей директории
echo "Содержимое рабочей директории:"
ls -la

# Создание необходимых директорий
echo "Создание необходимых директорий..."
mkdir -p logs tmp services
echo "✓ Директории logs, tmp и services созданы"

# Проверка наличия уже запущенного бота и его остановка
echo "Проверка наличия запущенных экземпляров бота..."
RUNNING_BOTS=$(ps aux | grep "python main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$RUNNING_BOTS" ]; then
    echo "ПРЕДУПРЕЖДЕНИЕ: Найдены запущенные экземпляры бота. Останавливаем..."
    for pid in $RUNNING_BOTS; do
        echo "Останавливаем процесс с PID $pid"
        kill -15 $pid
        sleep 2
        # Проверяем, завершился ли процесс
        if ps -p $pid > /dev/null; then
            echo "Процесс $pid не завершился. Принудительная остановка..."
            kill -9 $pid
        fi
    done
    echo "Все процессы бота остановлены"
else
    echo "Запущенных экземпляров бота не найдено"
fi

# Дополнительная пауза чтобы дать Telegram API освободить соединение
echo "Ожидание 10 секунд для освобождения соединений Telegram API..."
sleep 10

# Проверка наличия файлов бота
echo "Проверка наличия ключевых файлов бота..."
REQUIRED_FILES=("main.py" "restart_bot.py" "railway_logging.py" "create_placeholders.py" "fix_imports.py")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ПРЕДУПРЕЖДЕНИЕ: Файл $file не найден!"
        MISSING_FILES+=("$file")
    else
        echo "✓ Файл $file найден"
    fi
done

# Создаем railway_logging.py если не существует
check_and_create "railway_logging.py" '#!/usr/bin/env python
"""Модуль для настройки логирования в Railway."""
import logging
import sys
def setup_railway_logging(logger_name=None, level=logging.INFO):
    logger = logging.getLogger(logger_name or "railway")
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("ИНФО: %(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger
def railway_print(message, level="INFO"):
    prefix = "ИНФО"
    if level.upper() == "ERROR": prefix = "ОШИБКА"
    elif level.upper() == "WARNING": prefix = "ПРЕДУПРЕЖДЕНИЕ"
    print(f"{prefix}: {message}")
    sys.stdout.flush()'

# Создаем базовую заглушку для restart_bot.py если не существует
check_and_create "restart_bot.py" '#!/usr/bin/env python
"""Скрипт для автоматического перезапуска бота."""
import subprocess
import sys
import time
print("ИНФО: Запуск монитора перезапуска")
# Простой запуск main.py без перезапуска для отладки в Railway
subprocess.run([sys.executable, "main.py"])'

# Создаем fix_imports.py если не существует
check_and_create "fix_imports.py" '#!/usr/bin/env python
"""Скрипт для исправления путей импорта."""
import os
import sys
import importlib
print("ИНФО: Исправление путей импорта")
# Добавляем текущую директорию в sys.path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
    print(f"ИНФО: Путь {os.getcwd()} добавлен в sys.path")
# Проверяем доступные модули
print(f"ИНФО: Доступные файлы: {[f for f in os.listdir(\".\") if f.endswith(\".py\")]}")'

# Создаем create_placeholders.py если не существует
check_and_create "create_placeholders.py" '#!/usr/bin/env python
"""Скрипт для создания заглушек для отсутствующих модулей."""
import os
print("ИНФО: Запуск скрипта создания заглушек")
modules = ["survey_handler.py", "meditation_handler.py", "conversation_handler.py", "reminder_handler.py", "voice_handler.py"]
for module in modules:
    if not os.path.exists(module):
        with open(module, "w") as f:
            f.write(f"# Placeholder for {module}\\nfrom aiogram import Router\\n{module.replace(\".py\", \"_router\")} = Router(name=\"{module.replace(\".py\", \"\")}\")")
        print(f"ИНФО: Создана заглушка для {module}")'

# Создаем services директорию и __init__.py если не существует
echo "Проверка директории services..."
mkdir -p services
if [ ! -f "services/__init__.py" ]; then
    echo "Создание services/__init__.py..."
    echo "# Инициализация пакета services
from services.recs import generate_response
from services.stt import process_voice_message
try:
    from services.tts import generate_audio
except ImportError:
    # Заглушка для generate_audio
    async def generate_audio(*args, **kwargs):
        print(\"ПРЕДУПРЕЖДЕНИЕ: Используется заглушка для generate_audio\")
        return None, \"Функция недоступна\"" > services/__init__.py
    echo "✓ Файл services/__init__.py создан"
else
    echo "✓ Файл services/__init__.py существует"
fi

# Запуск скриптов инициализации
echo "Запуск скриптов инициализации..."

# Запуск скрипта исправления путей импорта
if [ -f "fix_imports.py" ]; then
    echo "Запуск fix_imports.py для исправления путей импорта..."
    python fix_imports.py
    echo "✓ Скрипт fix_imports.py выполнен"
else
    echo "ПРЕДУПРЕЖДЕНИЕ: Файл fix_imports.py не найден, пропускаем исправление путей импорта"
fi

# Запуск скрипта создания заглушек
if [ -f "create_placeholders.py" ]; then
    echo "Запуск create_placeholders.py для создания заглушек..."
    python create_placeholders.py
    echo "✓ Скрипт create_placeholders.py выполнен"
else
    echo "ПРЕДУПРЕЖДЕНИЕ: Файл create_placeholders.py не найден, пропускаем создание заглушек"
fi

# Проверка наличия ключевых модулей после создания заглушек
echo "Проверка ключевых модулей после создания заглушек..."
for module in "survey_handler.py" "meditation_handler.py" "conversation_handler.py" "reminder_handler.py" "voice_handler.py"; do
    if [ -f "$module" ]; then
        echo "✓ Модуль $module найден"
        wc -l "$module"
    else
        echo "ОШИБКА: Модуль $module все еще отсутствует!"
    fi
done

# Проверка наличия ключевых переменных окружения
echo "Проверка переменных окружения..."
if [ -z "$BOT_TOKEN" ]; then
    echo "ОШИБКА: Переменная BOT_TOKEN не установлена!"
else
    echo "✓ Переменная BOT_TOKEN установлена"
fi

# Проверка установленных пакетов Python
echo "Проверка установленных пакетов Python..."
pip list | grep aiogram
pip list | grep openai
pip list | grep elevenlabs
pip list | grep psutil

# Создание списка импортированных модулей
echo "Проверка доступности модулей через импорт..."
python -c "import sys; print('sys.path =', sys.path); import aiogram; print('aiogram импортирован успешно')" || echo "ОШИБКА: Не удалось импортировать aiogram"

# Запуск бота с перезапуском
echo "=== ЗАПУСК БОТА С МОНИТОРИНГОМ ПЕРЕЗАПУСКА ==="
echo "Используется Python: $(python --version)"

# Проверка и восстановление button_states.py
echo "Проверка и восстановление button_states.py..."
python fix_button_states.py

# Запуск бота с автоматическим перезапуском
echo "Запуск бота с мониторингом..."
python restart_bot.py 
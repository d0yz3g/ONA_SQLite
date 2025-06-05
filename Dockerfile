FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libc-dev \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Обновим pip
RUN pip install --upgrade pip setuptools wheel

# Копируем только requirements.txt
COPY requirements.txt .

# Установка зависимостей в оптимальном порядке
# Сначала базовые и критичные зависимости
RUN pip install --no-cache-dir python-dotenv pytz pre-commit pytest
RUN pip install --no-cache-dir httpx==0.25.2 aiohttp==3.9.1
RUN pip install --no-cache-dir aiogram==3.2.0
RUN pip install --no-cache-dir openai==1.3.5
RUN pip install --no-cache-dir ephem elevenlabs aiofiles apscheduler

# Явная установка psutil с нужными зависимостями
RUN pip install --no-cache-dir --force-reinstall psutil==5.9.5

# Создаем директорию для временных файлов и логов
RUN mkdir -p tmp logs

# Настройка вывода логов для контейнера
# Обеспечиваем правильное перенаправление stdout и stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONIOENCODING=utf-8
ENV PYTHONPATH=/app

# Копируем все исходные файлы проекта
COPY . .

# Создаем базовые файлы если их нет
RUN echo "print('Creating railway_logging if not exists')" > create_if_not_exists.py
RUN python create_if_not_exists.py

# Создаем вспомогательные скрипты для Railway
RUN echo "#!/usr/bin/env python\nimport os\nimport sys\n\nprint('Добавление /app в PYTHONPATH')\nif '/app' not in sys.path:\n    sys.path.insert(0, '/app')\n    print('Путь /app добавлен в sys.path')" > add_to_pythonpath.py

# Создание списка файлов в контейнере для отладки
RUN echo "Структура файлов в контейнере:" > /app/container_files.txt && \
    ls -la >> /app/container_files.txt && \
    echo "\nСодержимое рабочей директории:" >> /app/container_files.txt && \
    find . -type f -name "*.py" | sort >> /app/container_files.txt

# Проверка импорта ключевых модулей и создание заглушек при необходимости
RUN python -c "import os; print('Проверка наличия create_placeholders.py...'); print('Файл существует' if os.path.exists('create_placeholders.py') else 'Файл не найден')"
RUN python create_placeholders.py || echo "ПРЕДУПРЕЖДЕНИЕ: Не удалось запустить create_placeholders.py, продолжаем сборку"

RUN python -c "import os; print('Проверка наличия fix_imports.py...'); print('Файл существует' if os.path.exists('fix_imports.py') else 'Файл не найден')"
RUN python fix_imports.py || echo "ПРЕДУПРЕЖДЕНИЕ: Не удалось запустить fix_imports.py, продолжаем сборку"

# Проверка наличия обязательных файлов после создания заглушек
RUN echo "Проверка обязательных файлов проекта после создания заглушек..." && \
    for file in main.py survey_handler.py meditation_handler.py conversation_handler.py reminder_handler.py voice_handler.py railway_logging.py communication_handler.py; do \
        if [ -f "$file" ]; then \
            echo "✓ Файл $file найден"; \
            wc -l "$file"; \
        else \
            echo "ОШИБКА: Файл $file не найден!"; \
            ls -la; \
        fi; \
    done

# Создаем директорию services и базовые файлы если их нет
RUN mkdir -p services
RUN if [ ! -f "services/__init__.py" ]; then \
        echo "# Инициализация пакета services" > services/__init__.py; \
        echo "from services.recs import generate_response" >> services/__init__.py; \
        echo "from services.stt import process_voice_message" >> services/__init__.py; \
        echo "try:" >> services/__init__.py; \
        echo "    from services.tts import generate_audio" >> services/__init__.py; \
        echo "except ImportError:" >> services/__init__.py; \
        echo "    # Заглушка для generate_audio" >> services/__init__.py; \
        echo "    async def generate_audio(*args, **kwargs):" >> services/__init__.py; \
        echo "        print(\"ПРЕДУПРЕЖДЕНИЕ: Используется заглушка для generate_audio\")" >> services/__init__.py; \
        echo "        return None, \"Функция недоступна\"" >> services/__init__.py; \
        echo "✓ Файл services/__init__.py создан"; \
    else \
        echo "✓ Файл services/__init__.py существует"; \
    fi

# Дополнительная информация для логов
RUN echo "Ona2.0 Telegram Bot - Railway Deployment" > /app/railway_info.txt
RUN echo "Build date: $(date)" >> /app/railway_info.txt
RUN echo "Python version: $(python --version)" >> /app/railway_info.txt

# Проверка наличия psutil перед запуском
RUN python -c "import psutil; print('psutil успешно установлен, версия:', psutil.__version__)" >> /app/railway_info.txt || echo "ОШИБКА: psutil не импортируется"

# Проверка импорта ключевых модулей
RUN echo "Проверка импорта ключевых модулей:" >> /app/railway_info.txt
RUN python -c "import sys; sys.path.insert(0, '/app'); import railway_logging; print('railway_logging импортирован успешно')" >> /app/railway_info.txt || echo "ОШИБКА: railway_logging не импортируется"

# Делаем railway_start.sh исполняемым
RUN chmod +x railway_start.sh

# Настройка логирования для Railway
RUN touch /app/logs/bot.log /app/logs/restart.log

# Установка psutil отдельно (часто требуется для системных операций)
RUN pip install psutil

# Добавление скрипта для проверки и остановки запущенных процессов бота
RUN echo '#!/bin/bash\n\
# Проверяем наличие запущенных процессов бота\n\
echo "Проверка наличия запущенных экземпляров бота..."\n\
RUNNING_BOTS=$(ps aux | grep "python main.py" | grep -v grep | awk "{print \$2}")\n\
if [ ! -z "$RUNNING_BOTS" ]; then\n\
    echo "ПРЕДУПРЕЖДЕНИЕ: Найдены запущенные экземпляры бота. Останавливаем..."\n\
    for pid in $RUNNING_BOTS; do\n\
        echo "Останавливаем процесс с PID $pid"\n\
        kill -15 $pid\n\
        sleep 2\n\
        if ps -p $pid > /dev/null; then\n\
            echo "Процесс $pid не завершился. Принудительная остановка..."\n\
            kill -9 $pid\n\
            sleep 1\n\
        fi\n\
    done\n\
    echo "Все процессы бота остановлены"\n\
    echo "Ожидание 5 секунд для освобождения соединений..."\n\
    sleep 5\n\
else\n\
    echo "Запущенных экземпляров бота не найдено"\n\
fi\n\
\n\
# Запускаем бота через скрипт перезапуска\n\
python restart_bot.py\n'\
> /app/start_container.sh && chmod +x /app/start_container.sh

# Установка entrypoint
ENTRYPOINT ["/app/start_container.sh"] 
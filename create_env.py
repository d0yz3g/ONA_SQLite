#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Скрипт для создания файла .env с необходимыми переменными окружения

import os

# Содержимое файла .env
env_content = """BOT_TOKEN=5834194789:AAHgF-aOtbEpLJwLgW5rBRfMzKrJ4xEVLFk
OPENAI_API_KEY=sk-insert-your-valid-api-key-here
ELEVEN_API_KEY=test-elevenlabs-api-key-for-testing
ELEVENLABS_API_KEY=test-elevenlabs-api-key-for-testing
ELEVEN_VOICE_ID=EXAVITQu4vr4xnSDxMaL
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
LOG_LEVEL=INFO
DEFAULT_REMINDER_TIME=20:00
"""

# Записываем содержимое в файл
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("Файл .env успешно создан со следующими переменными:")
print(env_content) 
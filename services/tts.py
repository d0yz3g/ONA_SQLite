import os
import uuid
import logging
import aiohttp
import json
import requests
from pathlib import Path

# Настройка логирования
logger = logging.getLogger(__name__)

# Получение токена ElevenLabs из переменных окружения
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVEN_API_KEY and not ELEVENLABS_API_KEY:
    logger.warning("Ни ELEVEN_API_KEY, ни ELEVENLABS_API_KEY не найдены в переменных окружения. Функция генерации голоса будет работать в демо-режиме.")

# API URL ElevenLabs
ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# ID голоса по умолчанию (мягкий, спокойный голос)
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella - успокаивающий женский голос

# Максимальная длина текста для передачи в API
MAX_TEXT_LENGTH = 4000

def synthesize_speech(text: str, output_path: str) -> bool:
    """
    Использует ElevenLabs API для озвучивания текста и сохранения результата в mp3-файл.
    
    Args:
        text: Текст для озвучивания
        output_path: Путь для сохранения mp3-файла
        
    Returns:
        bool: True в случае успешного синтеза, False в случае ошибки
    """
    # Получаем API-ключ и Voice ID из переменных окружения
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    if not api_key:
        logger.error("ELEVENLABS_API_KEY не найден в переменных окружения")
        return False
    
    if not voice_id:
        logger.warning("ELEVENLABS_VOICE_ID не найден, используется голос по умолчанию")
        voice_id = DEFAULT_VOICE_ID
    
    # Проверка длины текста
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH-3] + "..."
        logger.warning(f"Текст для генерации аудио был обрезан до {MAX_TEXT_LENGTH} символов")
    
    # Формируем заголовки запроса
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    # Настройки голоса
    voice_settings = {
        "stability": 0.5,  # 50%
        "similarity_boost": 0.75,  # 75%
        "speed": 0.9  # 0.9 скорость
    }
    
    # Данные для запроса
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": voice_settings
    }
    
    try:
        logger.info(f"Отправка запроса к ElevenLabs API для синтеза речи")
        # Выполняем синхронный запрос к API
        response = requests.post(
            f"{ELEVEN_API_URL}/{voice_id}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            # Создаем папку для файла, если она не существует
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Сохраняем аудио-файл
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Аудио успешно сгенерировано и сохранено: {output_path}")
            return True
        else:
            logger.error(f"Ошибка при генерации аудио: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при генерации аудио: {e}")
        return False

async def generate_audio(text: str, user_id: int, meditation_type: str = "default") -> tuple:
    """
    Генерирует аудио с помощью ElevenLabs API.
    
    Args:
        text: Текст для преобразования в аудио
        user_id: ID пользователя Telegram
        meditation_type: Тип медитации (relax, focus, sleep)
        
    Returns:
        tuple: (str, str) - (Путь к созданному аудио-файлу, причина ошибки) 
               Если аудио создано успешно - (путь_к_файлу, None)
               Если произошла ошибка - (None, текст_ошибки)
    """
    # Создаем директорию tmp, если она не существует
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_name = f"{meditation_type}_{user_id}_{uuid.uuid4()}.mp3"
    file_path = tmp_dir / file_name
    
    # Если API ключ недоступен, генерируем демо-ответ
    api_key = ELEVEN_API_KEY or ELEVENLABS_API_KEY
    if not api_key:
        logger.warning(f"API ключ недоступен, генерация аудио невозможна для пользователя {user_id}")
        return None, "API ключ недоступен"
    
    try:
        # Подготовка данных для запроса
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        # Параметры голоса по запросу пользователя
        voice_settings = {
            "stability": 0.5,  # 50%
            "similarity_boost": 0.75,  # 75%
            "speed": 0.9  # 0.9 скорость
        }
        
        # Подготавливаем текст (ограничиваем длину)
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH-3] + "..."
            logger.warning(f"Текст для генерации аудио был обрезан для пользователя {user_id}")
        
        # Данные для запроса с моделью высокого качества
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Используем модель высокого качества
            "voice_settings": voice_settings
        }
        
        # ID голоса выбираем в зависимости от типа медитации
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
        
        # Отправляем запрос к API
        logger.info(f"Отправка запроса к ElevenLabs API для пользователя {user_id}")
        
        # Выполняем асинхронный запрос к API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ELEVEN_API_URL}/{voice_id}",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    # Сохраняем аудио-файл
                    with open(file_path, "wb") as f:
                        f.write(await response.read())
                    logger.info(f"Аудио успешно сгенерировано и сохранено: {file_path}")
                    return str(file_path), None
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка при генерации аудио: {response.status}, {error_text}")
                    
                    # Проверяем тип ошибки
                    try:
                        error_data = json.loads(error_text)
                        if response.status == 401 and "quota_exceeded" in str(error_data):
                            error_reason = "quota_exceeded"
                        else:
                            error_reason = f"HTTP ошибка {response.status}"
                    except:
                        error_reason = f"HTTP ошибка {response.status}"
                    
                    return None, error_reason
    except Exception as e:
        logger.error(f"Ошибка при генерации аудио: {e}")
        return None, str(e) 
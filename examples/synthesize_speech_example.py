import os
import uuid
import logging
from services.tts import synthesize_speech

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Пример использования функции synthesize_speech для генерации аудио через ElevenLabs API
    
    Для работы скрипта необходимо указать переменные окружения:
    - ELEVENLABS_API_KEY - API-ключ ElevenLabs
    - ELEVENLABS_VOICE_ID - ID голоса для синтеза (необязательно, будет использован голос по умолчанию)
    """
    # Проверяем наличие API-ключа
    if not os.getenv("ELEVENLABS_API_KEY"):
        logger.error("Переменная окружения ELEVENLABS_API_KEY не найдена")
        print("Ошибка: Для работы скрипта необходимо указать ELEVENLABS_API_KEY")
        print("Добавьте переменную окружения или создайте файл .env с содержимым:")
        print("ELEVENLABS_API_KEY=ваш_ключ_elevenlabs")
        print("ELEVENLABS_VOICE_ID=ид_голоса_elevenlabs (необязательно)")
        return
    
    # Генерируем имя файла с использованием UUID
    output_dir = "tmp"
    os.makedirs(output_dir, exist_ok=True)
    
    output_filename = f"example_speech_{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_dir, output_filename)
    
    # Текст для синтеза речи
    text = """Это пример синтеза речи с использованием ElevenLabs API.
    Функция synthesize_speech использует настройки stability=50%, similarity_boost=75% и speed=0.9.
    Результат сохраняется в MP3-файл."""
    
    logger.info(f"Начинаю синтез речи. Текст: '{text[:50]}...'")
    
    # Вызываем функцию синтеза речи
    success = synthesize_speech(text, output_path)
    
    if success:
        logger.info(f"Синтез речи успешно завершен! Файл сохранен по пути: {output_path}")
        print(f"Аудио успешно сгенерировано и сохранено: {output_path}")
        
        # Проверяем, что файл действительно был создан
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Размер файла: {os.path.getsize(output_path) / 1024:.2f} КБ")
        else:
            logger.warning(f"Файл не найден или имеет нулевой размер: {output_path}")
            print("Предупреждение: файл не найден или имеет нулевой размер")
    else:
        logger.error("Не удалось синтезировать речь")
        print("Ошибка: Не удалось синтезировать речь. Проверьте логи для получения дополнительной информации.")

if __name__ == "__main__":
    main() 
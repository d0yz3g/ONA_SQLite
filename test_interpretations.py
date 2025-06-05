"""
Тестовый скрипт для проверки функциональности интерпретаций ответов в опроснике.
"""

import asyncio
from typing import Dict, Any

async def test_interpretations():
    """
    Тестовая функция для проверки работы интерпретаций ответов.
    """
    from questions import get_all_vasini_questions
    
    # Получаем списки вопросов
    vasini_questions = get_all_vasini_questions()
    
    # Выбираем первый вопрос для теста
    test_question = vasini_questions[0]
    print(f"\nТестовый вопрос: {test_question['text']}")
    
    # Выводим варианты ответов
    print("\nВарианты ответов:")
    for option, text in test_question['options'].items():
        print(f"{option}: {text}")
    
    # Тестируем получение интерпретации для всех вариантов
    print("\nПроверка интерпретаций:")
    for option in ["A", "B", "C", "D"]:
        try:
            interpretation = test_question["interpretations"][option]
            print(f"\n🔍 Интерпретация для варианта {option}:")
            print(f"{interpretation}")
        except Exception as e:
            print(f"❌ Ошибка при получении интерпретации для варианта {option}: {e}")
    
    print("\n✅ Проверка завершена!")

if __name__ == "__main__":
    print("Запуск тестирования интерпретаций вопросов...")
    asyncio.run(test_interpretations()) 
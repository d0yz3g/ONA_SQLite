"""
Простой тест для проверки импорта модуля questions.
"""

def test_questions_import():
    """Проверяет импорт модуля questions и его основных функций."""
    try:
        import questions
        print("✅ Импорт модуля questions прошел успешно.")
        
        # Проверяем функцию получения вопросов
        demo_questions = questions.get_demo_questions()
        print(f"✅ Получено {len(demo_questions)} демо-вопросов.")
        
        # Проверяем функцию получения вопросов Vasini
        vasini_questions = questions.get_all_vasini_questions()
        print(f"✅ Получено {len(vasini_questions)} вопросов Vasini.")
        
        # Проверяем наличие интерпретаций
        if len(vasini_questions) > 0:
            first_question = vasini_questions[0]
            if "interpretations" in first_question:
                print("✅ Вопросы содержат интерпретации.")
                print(f"   Доступны интерпретации для опций: {', '.join(first_question['interpretations'].keys())}")
            else:
                print("❌ Вопросы не содержат интерпретаций!")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при тестировании модуля questions: {e}")
        return False

if __name__ == "__main__":
    print("Запуск простого теста модуля questions...")
    success = test_questions_import()
    print(f"\nРезультат теста: {'Успешно' if success else 'Ошибка'}") 
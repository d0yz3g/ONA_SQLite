import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from button_states import SurveyStates, ProfileStates
from profile_generator import generate_profile, save_profile_to_db

# Импорт функции railway_print для логирования
try:
    from railway_logging import railway_print
except ImportError:
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
        import sys
        sys.stdout.flush()

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для опроса
survey_router = Router()

# Функция для получения основной клавиатуры
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает основную клавиатуру приложения.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с основными функциями
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📝 Опрос")],
            [KeyboardButton(text="🧘 Медитации"), KeyboardButton(text="⏰ Напоминания")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="💬 Помощь")],
            [KeyboardButton(text="🔄 Рестарт")]
        ],
        resize_keyboard=True
    )

async def start_survey(message: Message, state: FSMContext):
    """
    Начинает опрос пользователя.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    
    # Проверяем, есть ли у пользователя уже заполненный профиль
    has_profile = user_data.get("profile_completed", False)
    
    if has_profile:
        # Если у пользователя уже есть профиль, спрашиваем подтверждение на перезапись
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Да, начать заново", callback_data="confirm_survey")
        builder.button(text="❌ Нет, отмена", callback_data="cancel_survey")
        builder.adjust(2)  # Размещаем обе кнопки в одном ряду
        
        await message.answer(
            "⚠️ <b>Внимание:</b>\n\n"
            "У вас уже есть заполненный профиль. Если вы пройдете опрос заново, "
            "ваши текущие данные будут перезаписаны.\n\n"
            "Вы уверены, что хотите начать опрос заново?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return
    
    # Если профиля нет, начинаем опрос сразу
    # Импортируем функцию для получения демо-вопросов
    from questions import get_demo_questions
    
    # Получаем список демо-вопросов
    demo_questions = get_demo_questions()
    
    # Показываем первый вопрос
    await message.answer(
        "📋 <b>Начинаем опрос!</b>\n\n"
        "Я задам несколько вопросов, чтобы лучше узнать тебя. "
        "Сначала ответь на несколько базовых вопросов, а затем мы перейдем к "
        "специальному тесту для определения твоих сильных сторон.",
        parse_mode="HTML"
    )
    
    # Показываем первый вопрос
    await message.answer(
        f"Вопрос 1: {demo_questions[0]['text']}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить опрос")]],
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Введите ваш ответ..."
        )
    )
    
    # Инициализируем опрос
    await state.set_state(SurveyStates.answering_questions)
    await state.update_data(
        question_index=0,
        question_type="demo",
        answers={},
        is_demo_questions=True
    )
    
    logger.info(f"Пользователь {message.from_user.id} начал опрос")

# Обработчик для подтверждения перезапуска опроса
@survey_router.callback_query(F.data == "confirm_survey")
async def confirm_restart_survey(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждает перезапуск опроса.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    # Очищаем текущие данные профиля
    await state.update_data(
        answers={},
        profile_completed=False,
        profile_text="",
        personality_type=None
    )
    
    # Начинаем опрос заново
    await start_survey(callback.message, state)
    
    # Отвечаем на callback
    await callback.answer("Начинаем опрос заново")

# Обработчик для отмены перезапуска опроса
@survey_router.callback_query(F.data == "cancel_survey")
async def cancel_restart_survey(callback: CallbackQuery):
    """
    Отменяет перезапуск опроса.
    
    Args:
        callback: Callback query
    """
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    # Отправляем сообщение об отмене
    await callback.message.answer(
        "✅ Опрос отменен. Ваш текущий профиль сохранен.",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Опрос отменен")

# Обработчик ответов на вопросы опроса
@survey_router.message(SurveyStates.answering_questions)
async def process_survey_answer(message: Message, state: FSMContext):
    """
    Обрабатывает ответы на вопросы опроса.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Если пользователь хочет отменить опрос
    if message.text == "❌ Отменить опрос":
        await state.clear()
        await message.answer(
            "❌ Опрос отменен. Вы можете начать его заново в любое время.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем текущее состояние опроса
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    answers = data.get("answers", {})
    is_demo_questions = data.get("is_demo_questions", True)
    
    # Импортируем функции для получения вопросов
    from questions import get_demo_questions, get_all_vasini_questions
    
    # Получаем списки вопросов
    demo_questions = get_demo_questions()
    # Используем функцию get_all_vasini_questions вместо прямого объединения
    try:
        vasini_questions = get_all_vasini_questions()
        logger.info(f"Загружено {len(vasini_questions)} вопросов Vasini")
    except Exception as e:
        logger.error(f"Ошибка при загрузке вопросов Vasini: {e}")
        # Создаем пустой список в случае ошибки
        vasini_questions = []
        railway_print("ОШИБКА: Не удалось загрузить вопросы Vasini, опрос будет недоступен", "ERROR")
    
    # Определяем текущий вопрос
    if is_demo_questions:
        current_question = demo_questions[question_index]
        # Сохраняем ответ на демо-вопрос
        question_id = current_question["id"]
        answers[question_id] = message.text
        # Переходим к следующему вопросу
        question_index += 1
        
        # Если демо-вопросы закончились, переходим к вопросам Vasini
        if question_index >= len(demo_questions):
            is_demo_questions = False
            question_index = 0
            
            # Показываем информацию о начале теста Vasini
            await message.answer(
                "🧠 <b>Основная информация собрана!</b>\n\n"
                "Теперь я задам вам 34 вопроса для определения ваших сильных сторон и талантов. "
                "Этот тест называется Vasini Strengths Constellation и помогает выявить ваши природные способности.\n\n"
                "На каждый вопрос нужно выбрать один из вариантов ответа (A, B, C или D).\n\n"
                "Готовы начать?",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="✅ Да, готов(а)")],
                        [KeyboardButton(text="❌ Отменить опрос")]
                    ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
            
            # Обновляем состояние
            await state.update_data(
                question_index=question_index,
                answers=answers,
                is_demo_questions=is_demo_questions,
                waiting_for_vasini_confirmation=True
            )
            return
    else:
        # Проверяем, ожидаем ли мы подтверждения для начала теста Vasini
        if data.get("waiting_for_vasini_confirmation", False):
            if message.text == "✅ Да, готов(а)":
                # Начинаем тест Vasini
                current_question = vasini_questions[question_index]
                
                # Создаем клавиатуру с вариантами ответов
                options = current_question["options"]
                keyboard = []
                for option, text in options.items():
                    # Формируем текст кнопки с более выраженной буквой варианта
                    button_text = f"{option}: {text}"
                    keyboard.append([KeyboardButton(text=button_text)])
                keyboard.append([KeyboardButton(text="❌ Отменить опрос")])
                
                # Логируем какие варианты ответов мы показываем
                logger.info(f"Показываем вопрос 1 с вариантами ответов: {', '.join(options.keys())}")
                
                await message.answer(
                    f"Вопрос {question_index + 1}/34: {current_question['text']}",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=keyboard,
                        resize_keyboard=True,
                        one_time_keyboard=True,
                        input_field_placeholder="Выберите вариант ответа (A, B, C или D)..."
                    )
                )
                
                # Обновляем состояние
                await state.update_data(
                    waiting_for_vasini_confirmation=False
                )
                return
            elif message.text == "❌ Отменить опрос":
                await state.clear()
                await message.answer(
                    "❌ Опрос отменен. Вы можете начать его заново в любое время.",
                    reply_markup=get_main_keyboard()
                )
                return
            else:
                # Если ответ не соответствует формату, просим повторить
                options = current_question["options"]
                keyboard = []
                for opt, text in options.items():
                    # Формируем текст кнопки с более выраженной буквой варианта
                    button_text = f"{opt}: {text}"
                    keyboard.append([KeyboardButton(text=button_text)])
                keyboard.append([KeyboardButton(text="❌ Отменить опрос")])
                
                # Логируем, что пользователь должен повторить выбор
                logger.info(f"Пользователь должен повторить выбор для вопроса {question_index + 1}")
                
                await message.answer(
                    f"Пожалуйста, выберите один из предложенных вариантов ответа (A, B, C или D).\n\n"
                    f"Вопрос {question_index + 1}/34: {current_question['text']}",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=keyboard,
                        resize_keyboard=True,
                        one_time_keyboard=True,
                        input_field_placeholder="Выберите вариант ответа (A, B, C или D)..."
                    )
                )
                return
        
        # Обрабатываем ответ на вопрос Vasini
        current_question = vasini_questions[question_index]
        
        # Логируем полученный текст сообщения для отладки
        logger.info(f"Получен ответ на вопрос {question_index + 1}: '{message.text}'")
        
        # Проверяем, что ответ содержит букву варианта (A, B, C или D)
        option = None
        # Проверяем различные форматы ответов
        for opt in ["A", "B", "C", "D"]:
            # Проверка на формат "A: текст"
            if message.text.startswith(f"{opt}:"):
                option = opt
                logger.info(f"Распознан ответ '{opt}' по шаблону '{opt}:'")
                break
            # Проверка на формат "A текст" без двоеточия
            elif message.text.startswith(f"{opt} "):
                option = opt
                logger.info(f"Распознан ответ '{opt}' по шаблону '{opt} '")
                break
            # Проверка если пользователь ввел только букву "A", "B", "C" или "D"
            elif message.text.upper() == opt:
                option = opt
                logger.info(f"Распознан ответ '{opt}' (пользователь ввел только букву)")
                break
            # Проверка если текст содержит букву в любом месте (менее строгая проверка)
            elif f" {opt} " in f" {message.text.upper()} ":
                option = opt
                logger.info(f"Распознан ответ '{opt}' в тексте '{message.text}'")
                break
        
        if not option:
            # Если ответ не распознан, логируем это
            logger.warning(f"Не удалось распознать вариант ответа в тексте: '{message.text}'")
            
            # Если ответ не соответствует формату, просим повторить
            options = current_question["options"]
            keyboard = []
            for opt, text in options.items():
                # Формируем текст кнопки с более выраженной буквой варианта
                button_text = f"{opt}: {text}"
                keyboard.append([KeyboardButton(text=button_text)])
            keyboard.append([KeyboardButton(text="❌ Отменить опрос")])
            
            # Логируем, что пользователь должен повторить выбор
            logger.info(f"Пользователь должен повторить выбор для вопроса {question_index + 1}")
            
            await message.answer(
                f"Пожалуйста, выберите один из предложенных вариантов ответа (A, B, C или D).\n\n"
                f"Вопрос {question_index + 1}/34: {current_question['text']}",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=keyboard,
                    resize_keyboard=True,
                    one_time_keyboard=True,
                    input_field_placeholder="Выберите вариант ответа (A, B, C или D)..."
                )
            )
            return
        
        # Сохраняем ответ на вопрос Vasini
        question_id = current_question["id"]
        answers[question_id] = option
        
        # Отправляем интерпретацию ответа пользователю
        try:
            interpretation = current_question["interpretations"][option]
            await message.answer(
                f"💡 <b>Интерпретация:</b>\n\n{interpretation}",
                parse_mode="HTML"
            )
            # Добавляем небольшую задержку для удобства чтения
            await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        except Exception as e:
            logger.error(f"Ошибка при отправке интерпретации: {e}")
        
        # Переходим к следующему вопросу
        question_index += 1
        
        # Если все вопросы Vasini заданы, завершаем опрос
        if question_index >= len(vasini_questions):
            await complete_survey(message, state, answers)
            return
    
    # Показываем следующий вопрос
    if is_demo_questions:
        next_question = demo_questions[question_index]
        await message.answer(
            f"Вопрос {question_index + 1}/{len(demo_questions)}: {next_question['text']}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отменить опрос")]],
                resize_keyboard=True,
                one_time_keyboard=False,
                input_field_placeholder="Введите ваш ответ..."
            )
        )
    else:
        next_question = vasini_questions[question_index]
        
        # Создаем клавиатуру с вариантами ответов
        options = next_question["options"]
        keyboard = []
        for option, text in options.items():
            # Формируем текст кнопки, делая букву варианта более выраженной
            button_text = f"{option}: {text}"
            keyboard.append([KeyboardButton(text=button_text)])
        keyboard.append([KeyboardButton(text="❌ Отменить опрос")])
        
        # Логируем какие варианты ответов мы показываем
        logger.info(f"Показываем вопрос {question_index + 1} с вариантами ответов: {', '.join(options.keys())}")
        
        await message.answer(
            f"Вопрос {question_index + 1}/34: {next_question['text']}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                one_time_keyboard=True,
                input_field_placeholder="Выберите вариант ответа (A, B, C или D)..."
            )
        )
    
    # Обновляем состояние
    await state.update_data(
        question_index=question_index,
        answers=answers,
        is_demo_questions=is_demo_questions
    )

async def complete_survey(message: Message, state: FSMContext, answers: Dict[str, str]):
    """
    Завершает опрос и генерирует психологический профиль пользователя.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
        answers: Словарь с ответами пользователя
    """
    # Показываем индикатор "печатает..."
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Отправляем сообщение о том, что опрос завершен и идет генерация профиля
    processing_message = await message.answer(
        "✅ <b>Опрос завершен!</b>\n\n"
        "Генерирую ваш психологический профиль на основе ответов. "
        "Это может занять несколько секунд...",
        parse_mode="HTML"
    )
    
    # Импортируем функцию для определения типа личности
    from questions import get_personality_type_from_answers
    
    # Определяем тип личности
    type_counts, primary_type, secondary_type = get_personality_type_from_answers(answers)
    
    try:
        # Генерируем профиль
        profile_data = await generate_profile(answers)
        
        # Получаем подробный профиль, игнорируем краткую версию
        detailed_profile = profile_data.get("details", "")
        
        # Логируем информацию о полученных профилях для отладки
        logger.info(f"Получен детальный профиль длиной {len(detailed_profile)} символов")
        
        # Сбрасываем состояние опроса
        await state.set_state(None)
        
        # Сохраняем результаты в состоянии пользователя
        await state.update_data(
            answers=answers,
            profile_completed=True,
            profile_details=detailed_profile,
            profile_text=detailed_profile,
            personality_type=primary_type,
            secondary_type=secondary_type,
            type_counts=type_counts
        )
        
        # Проверяем, что профили действительно сохранились
        verification_data = await state.get_data()
        saved_details = verification_data.get("profile_details", "")
        saved_text = verification_data.get("profile_text", "")
        logger.info(f"Проверка сохранения детального профиля: сохранено {len(saved_details)} символов в profile_details, {len(saved_text)} символов в profile_text")
        
        # Удаляем сообщение о генерации профиля
        await processing_message.delete()
        
        # Создаем клавиатуру с кнопками
        builder = InlineKeyboardBuilder()
        builder.button(text="💡 Получить совет", callback_data="get_advice")
        builder.adjust(1)  # Располагаем кнопки в столбик
        
        # Проверяем, не слишком ли длинный профиль для отправки в одном сообщении
        max_message_length = 4000  # Telegram ограничивает сообщения примерно до 4096 символов
        
        if len(detailed_profile) > max_message_length:
            # Разбиваем детальный профиль на части
            parts = []
            current_part = ""
            for line in detailed_profile.split('\n'):
                if len(current_part) + len(line) + 1 <= max_message_length:
                    current_part += line + '\n'
                else:
                    parts.append(current_part)
                    current_part = line + '\n'
            if current_part:
                parts.append(current_part)
            
            # Отправляем части профиля
            for i, part in enumerate(parts):
                # Добавляем кнопки только к последней части
                if i == len(parts) - 1:
                    await message.answer(
                        part,
                        parse_mode="HTML",
                        reply_markup=builder.as_markup()
                    )
                else:
                    await message.answer(
                        part,
                        parse_mode="HTML"
                    )
        else:
            # Отправляем профиль
            await message.answer(
                detailed_profile,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        
        # Возвращаем основную клавиатуру
        await message.answer(
            "⬅️ Вернуться в главное меню",
            reply_markup=get_main_keyboard()
        )
        
        # Логируем завершение опроса
        logger.info(f"Пользователь {message.from_user.id} завершил опрос, профиль сгенерирован")
        
    except Exception as e:
        # В случае ошибки отправляем сообщение
        logger.error(f"Ошибка при генерации профиля: {e}")
        await processing_message.edit_text(
            "❌ <b>Произошла ошибка при генерации профиля.</b>\n\n"
            "Пожалуйста, попробуйте пройти опрос еще раз.",
            parse_mode="HTML"
        )
        
        # Возвращаем основную клавиатуру
        await message.answer(
            "Вернуться в главное меню",
            reply_markup=get_main_keyboard()
        )
        
        # Удаляем состояние опроса
        await state.clear()
        return

# Обработчик для перезапуска опроса
@survey_router.callback_query(F.data == "restart_survey")
async def restart_survey(callback: CallbackQuery, state: FSMContext):
    """
    Перезапускает опрос, удаляя предыдущий профиль пользователя.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Спрашиваем подтверждение перед сбросом данных
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, сбросить профиль", callback_data="confirm_profile_reset")
    builder.button(text="❌ Нет, отмена", callback_data="cancel_profile_reset")
    builder.adjust(1)
    
    await callback.message.answer(
        "⚠️ <b>Внимание!</b>\n\n"
        "Вы собираетесь сбросить ваш текущий профиль и пройти опрос заново. "
        "Все ваши предыдущие ответы будут удалены.\n\n"
        "Вы уверены, что хотите продолжить?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    # Отвечаем на callback
    await callback.answer("Подтвердите сброс профиля")

@survey_router.callback_query(F.data == "confirm_profile_reset")
async def confirm_profile_reset(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждает сброс профиля и перезапускает опрос.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Очищаем текущие данные профиля
    await state.update_data(
        answers={},
        profile_completed=False,
        profile_text="",
        profile_details="",
        personality_type=None,
        waiting_for_vasini_confirmation=False,
        question_index=0,
        is_demo_questions=True
    )
    
    # Удаляем сообщение с подтверждением
    await callback.message.delete()
    
    # Сообщаем об успешном сбросе
    await callback.message.answer(
        "✅ <b>Профиль успешно сброшен!</b>\n\n"
        "Сейчас мы начнем опрос заново.",
        parse_mode="HTML"
    )
    
    # Небольшая задержка перед началом нового опроса
    import asyncio
    await asyncio.sleep(1)
    
    # Начинаем опрос заново
    await start_survey(callback.message, state)
    
    # Отвечаем на callback
    await callback.answer("Профиль сброшен, начинаем опрос заново")
    logger.info(f"Пользователь {callback.from_user.id} сбросил профиль и начал опрос заново")

@survey_router.callback_query(F.data == "cancel_profile_reset")
async def cancel_profile_reset(callback: CallbackQuery):
    """
    Отменяет сброс профиля.
    
    Args:
        callback: Callback query
    """
    # Удаляем сообщение с подтверждением
    await callback.message.delete()
    
    # Сообщаем об отмене
    await callback.message.answer(
        "✅ Действие отменено. Ваш текущий профиль сохранен.",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Отмена сброса профиля")
    logger.info(f"Пользователь {callback.from_user.id} отменил сброс профиля")

# Добавляем новый обработчик для отображения детального профиля
@survey_router.callback_query(F.data == "show_details")
async def show_profile_details(callback: CallbackQuery, state: FSMContext):
    """
    Отображает детальный психологический профиль.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Показываем индикатор "печатает..."
    await callback.message.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    # Получаем данные пользователя
    user_data = await state.get_data()
    details_text = user_data.get("profile_details", "")
    
    # Логируем полученные данные для отладки
    logger.info(f"Запрошен детальный профиль. Длина текста: {len(details_text) if details_text else 0}")
    logger.info(f"Доступные ключи в user_data: {', '.join(user_data.keys())}")
    
    if not details_text or len(details_text) < 20:
        await callback.message.answer(
            "❌ <b>Ошибка:</b> Детальный профиль не найден или пуст. Пожалуйста, пройдите опрос заново.",
            parse_mode="HTML"
        )
        await callback.answer("Детальный профиль не найден")
        return
    
    # Проверяем, не слишком ли длинный профиль для отправки в одном сообщении
    max_message_length = 4000  # Telegram ограничивает сообщения примерно до 4096 символов
    
    if len(details_text) > max_message_length:
        # Разбиваем детальный профиль на части
        parts = []
        current_part = ""
        for line in details_text.split('\n'):
            if len(current_part) + len(line) + 1 <= max_message_length:
                current_part += line + '\n'
            else:
                parts.append(current_part)
                current_part = line + '\n'
        if current_part:
            parts.append(current_part)
        
        # Отправляем части профиля
        for i, part in enumerate(parts):
            # Добавляем кнопки только к последней части
            if i == len(parts) - 1:
                # Добавляем кнопки для навигации
                builder = InlineKeyboardBuilder()
                builder.button(text="💡 Получить совет", callback_data="get_advice")
                builder.button(text="🔙 Назад", callback_data="view_profile")
                builder.adjust(1)
                
                await callback.message.answer(
                    part,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
            else:
                await callback.message.answer(
                    part,
                    parse_mode="HTML"
                )
    else:
        # Добавляем кнопки для навигации
        builder = InlineKeyboardBuilder()
        builder.button(text="💡 Получить совет", callback_data="get_advice")
        builder.button(text="🔙 Назад", callback_data="view_profile")
        builder.adjust(1)
        
        # Отправляем детальный профиль
        await callback.message.answer(
            details_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    
    # Возвращаем основную клавиатуру после вывода деталей
    await callback.message.answer(
        "⬅️ Вернуться в главное меню",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Детальный психологический профиль")

@survey_router.callback_query(F.data == "view_profile")
async def view_profile_callback(callback: CallbackQuery, state: FSMContext):
    """
    Отображает профиль пользователя.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    
    Примечание: Функция изменена для показа полного профиля вместо краткой версии.
    Кнопки "Статистика" и "Детальный анализ" удалены согласно требованиям.
    """
    # Показываем индикатор "печатает..."
    await callback.message.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    
    # Получаем данные пользователя
    user_data = await state.get_data()
    profile_completed = user_data.get("profile_completed", False)
    
    if not profile_completed:
        # Профиль не найден, предлагаем пройти опрос
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Пройти опрос", callback_data="start_survey")
        builder.button(text="🔙 Главное меню", callback_data="main_menu")
        builder.adjust(1)
        
        await callback.message.answer(
            "❌ <b>Профиль не найден</b>\n\n"
            "Для создания психологического профиля необходимо пройти опрос. "
            "Это займет около 5-10 минут и поможет мне лучше понять ваш стиль мышления и особенности.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        # Возвращаем основную клавиатуру
        await callback.message.answer(
            "Вернуться в главное меню",
            reply_markup=get_main_keyboard()
        )
        
        await callback.answer("Профиль не найден")
        return
    
    # Получаем детальный профиль
    details_text = user_data.get("profile_details", "")
    
    if not details_text or len(details_text) < 20:
        await callback.message.answer(
            "❌ <b>Ошибка:</b> Детальный профиль не найден или пуст. Пожалуйста, пройдите опрос заново.",
            parse_mode="HTML"
        )
        await callback.answer("Детальный профиль не найден")
        return
    
    # Создаем клавиатуру с кнопками для действий
    builder = InlineKeyboardBuilder()
    builder.button(text="💡 Получить совет", callback_data="get_advice")
    builder.button(text="🔄 Пройти опрос заново", callback_data="restart_survey")
    builder.button(text="🔙 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    # Проверяем, не слишком ли длинный профиль для отправки в одном сообщении
    max_message_length = 4000  # Telegram ограничивает сообщения примерно до 4096 символов
    
    if len(details_text) > max_message_length:
        # Разбиваем детальный профиль на части
        parts = []
        current_part = ""
        for line in details_text.split('\n'):
            if len(current_part) + len(line) + 1 <= max_message_length:
                current_part += line + '\n'
            else:
                parts.append(current_part)
                current_part = line + '\n'
        if current_part:
            parts.append(current_part)
        
        # Отправляем части профиля
        for i, part in enumerate(parts):
            # Добавляем кнопки только к последней части
            if i == len(parts) - 1:
                await callback.message.answer(
                    part,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
            else:
                await callback.message.answer(
                    part,
                    parse_mode="HTML"
                )
    else:
        # Отправляем профиль
        await callback.message.answer(
            details_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    
    # Возвращаем основную клавиатуру
    await callback.message.answer(
        "⬅️ Вернуться в главное меню",
        reply_markup=get_main_keyboard()
    )
    
    await callback.answer("Профиль загружен")
    logger.info(f"Пользователь {callback.from_user.id} просмотрел свой профиль")

# Регистрация обработчиков команд
@survey_router.message(Command("survey"))
@survey_router.message(F.text == "📝 Опрос")
async def command_survey(message: Message, state: FSMContext):
    """
    Обработчик команды /survey и кнопки "Опрос".
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    await start_survey(message, state)

# Обработчик команды профиля
@survey_router.message(Command("profile"))
@survey_router.message(F.text == "👤 Профиль")
async def command_profile(message: Message, state: FSMContext):
    """
    Обработчик команды /profile и кнопки "Профиль".
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    
    Примечание: Функция изменена для отображения полного профиля сразу
    вместо краткой версии и промежуточных кнопок.
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    profile_completed = user_data.get("profile_completed", False)
    
    if profile_completed:
        # Показываем индикатор "печатает..."
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Получаем детальный профиль
        details_text = user_data.get("profile_details", "")
        
        if not details_text or len(details_text) < 20:
            await message.answer(
                "❌ <b>Ошибка:</b> Детальный профиль не найден или пуст. Пожалуйста, пройдите опрос заново.",
                parse_mode="HTML"
            )
            return
        
        # Создаем клавиатуру с кнопками для действий
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Пройти опрос заново", callback_data="restart_survey")
        builder.button(text="💡 Получить совет", callback_data="get_advice")
        builder.button(text="◀️ Вернуться в меню", callback_data="main_menu")
        builder.adjust(1)
        
        # Проверяем, не слишком ли длинный профиль для отправки в одном сообщении
        max_message_length = 4000  # Telegram ограничивает сообщения примерно до 4096 символов
        
        if len(details_text) > max_message_length:
            # Разбиваем детальный профиль на части
            parts = []
            current_part = ""
            for line in details_text.split('\n'):
                if len(current_part) + len(line) + 1 <= max_message_length:
                    current_part += line + '\n'
                else:
                    parts.append(current_part)
                    current_part = line + '\n'
            if current_part:
                parts.append(current_part)
            
            # Отправляем части профиля
            for i, part in enumerate(parts):
                # Добавляем кнопки только к последней части
                if i == len(parts) - 1:
                    await message.answer(
                        part,
                        parse_mode="HTML",
                        reply_markup=builder.as_markup()
                    )
                else:
                    await message.answer(
                        part,
                        parse_mode="HTML"
                    )
        else:
            # Отправляем профиль
            await message.answer(
                details_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        
        # Устанавливаем состояние просмотра профиля
        await state.set_state(ProfileStates.viewing)
    else:
        # Предлагаем пройти опрос, если профиля нет
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Начать опрос", callback_data="start_survey")
        
        await message.answer(
            "У вас пока нет психологического профиля. Чтобы создать его, нужно пройти опрос.",
            reply_markup=builder.as_markup()
        )

# Добавляем обработчик отмены опроса
@survey_router.message(Command("cancel"))
@survey_router.message(F.text == "❌ Отменить")
async def cancel_survey_command(message: Message, state: FSMContext):
    """
    Отменяет текущий опрос.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    current_state = await state.get_state()
    
    if current_state == SurveyStates.answering_questions:
        await state.clear()
        await message.answer(
            "❌ Опрос отменен. Вы можете начать его заново в любое время.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "❓ Сейчас нет активного опроса для отмены."
        )

# Обработчик кнопки возврата в главное меню
@survey_router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя в главное меню.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Сбрасываем состояние просмотра профиля или любое другое состояние
    await state.set_state(None)
    
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    # Отправляем сообщение с основной клавиатурой
    await callback.message.answer(
        "Вы вернулись в главное меню. Выберите нужную опцию:",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Возврат в главное меню")
    logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню")

# Функция для генерации персонализированных советов
def get_personalized_advice(personality_type: str, profile_text: str = None, used_advices: list = None) -> str:
    """
    Генерирует персонализированный совет на основе профиля пользователя.
    
    Args:
        personality_type: Тип личности пользователя
        profile_text: Текст профиля пользователя
        used_advices: Список уже использованных советов
        
    Returns:
        str: Персонализированный совет
    """
    # Если нет текста профиля, используем стандартные советы (fallback)
    if not profile_text:
        logger.warning("Текст профиля отсутствует, используем стандартные советы")
        # Словарь с советами для разных типов личности (fallback)
        advice_by_type = {
            "Интеллектуальный": [
                "🧠 Запланируйте 15-20 минут в день для чтения материалов по интересующей вас теме. Это поможет удовлетворить вашу потребность в интеллектуальном развитии.",
                "🧩 Попробуйте метод «пяти почему» при анализе проблемы — задавайте вопрос «почему» пять раз подряд, чтобы докопаться до первопричины."
            ],
            "Эмоциональный": [
                "📓 Практикуйте «эмоциональный дневник»: записывайте свои эмоции в течение дня и их триггеры. Это помогает лучше понимать свои чувства и реакции.",
                "🧘 Используйте технику «дыхание 4-7-8»: вдох на 4 счета, задержка на 7, выдох на 8. Это эффективно снижает тревожность и помогает восстановить эмоциональный баланс."
            ],
            "Практический": [
                "🐸 Используйте технику «ешьте лягушку»: начинайте день с самой сложной и неприятной задачи, и остальной день пройдет более продуктивно.",
                "⏱️ Применяйте правило «двух минут»: если задача требует менее двух минут, сделайте ее сразу, не откладывая — это значительно сократит ваш список дел."
            ],
            "Творческий": [
                "📝 Практикуйте «утренние страницы»: после пробуждения напишите три страницы текста без цензуры и редактирования. Это стимулирует творческое мышление.",
                "🔄 Используйте технику «случайное слово»: выберите любое слово из словаря и попробуйте связать его с задачей, над которой работаете, чтобы найти новые идеи."
            ]
        }
        
        # Получаем список советов для данного типа личности
        advice_list = advice_by_type.get(personality_type, advice_by_type["Интеллектуальный"])
        
        # Выбираем случайный совет
        import random
        advice = random.choice(advice_list)
        
        # Логируем выбранный совет
        logger.info(f"Выбран стандартный совет для типа личности {personality_type}")
        
        return advice
    
    # Если есть текст профиля, генерируем уникальный совет
    return generate_unique_advice(profile_text, personality_type, used_advices or [])

def extract_key_aspects(profile_text: str, personality_type: str) -> list:
    """
    Извлекает ключевые аспекты из профиля пользователя.
    
    Args:
        profile_text: Текст профиля пользователя
        personality_type: Тип личности пользователя
        
    Returns:
        list: Список ключевых аспектов
    """
    # Ключевые слова и фразы для поиска в профиле
    keywords = {
        "Интеллектуальный": [
            "анализ", "логика", "мышление", "интеллект", "знания", 
            "обучение", "информация", "понимание", "исследование", "концепции", 
            "стратегическое мышление", "критическое мышление", "абстрактное мышление",
            "когнитивные процессы", "рациональность", "любознательность"
        ],
        "Эмоциональный": [
            "эмоции", "чувства", "эмпатия", "сопереживание", "отношения", 
            "понимание других", "эмоциональный интеллект", "интуиция", "настроение", 
            "гармония", "самосознание", "саморегуляция", "внутренний мир",
            "эмоциональная глубина", "чувствительность", "психологическая гибкость"
        ],
        "Практический": [
            "организация", "планирование", "эффективность", "результат", "действие", 
            "дисциплина", "методичность", "пунктуальность", "продуктивность", "цели", 
            "структура", "процессы", "упорядоченность", "последовательность", 
            "практичность", "прагматизм", "конкретика"
        ],
        "Творческий": [
            "творчество", "креативность", "воображение", "идеи", "инновации", 
            "оригинальность", "интуиция", "вдохновение", "эстетика", "экспрессия", 
            "искусство", "дизайн", "нестандартное мышление", "творческий потенциал",
            "визуализация", "новаторство", "экспериментирование"
        ],
        "Аналитический тип": [
            "анализ данных", "аналитика", "системный подход", "детали", "точность",
            "структурирование", "классификация", "оценка", "закономерности", "алгоритмы",
            "методология", "верификация", "сравнение", "измерение", "исследование",
            "аргументация", "факты", "логические связи"
        ]
    }
    
    # Аспекты для разных типов личности
    aspects = {
        "Интеллектуальный": [
            "аналитическому мышлению", "обработке информации", "стратегическому планированию", 
            "концептуальному мышлению", "поиску закономерностей", "систематизации знаний", 
            "критическому анализу", "логическим рассуждениям", "глубокому пониманию", 
            "абстрактному мышлению", "поиску связей между концепциями", "интеллектуальной любознательности"
        ],
        "Эмоциональный": [
            "эмпатии", "эмоциональному восприятию", "чувственному опыту", 
            "эмоциональному самоанализу", "глубоким переживаниям", "интуитивному пониманию", 
            "эмоциональной осознанности", "сопереживанию", "построению глубоких отношений", 
            "эмоциональной восприимчивости", "эмоциональному резонансу", "пониманию чувств других"
        ],
        "Практический": [
            "организованности", "структурированию задач", "достижению конкретных результатов", 
            "эффективному планированию", "практическому подходу", "детальному анализу", 
            "последовательным действиям", "конкретным шагам", "организации процессов", 
            "управлению ресурсами", "оптимизации деятельности", "доведению дел до конца"
        ],
        "Творческий": [
            "нестандартному мышлению", "творческой свободе", "генерации новых идей", 
            "креативному подходу", "образному мышлению", "творческой визуализации", 
            "поиску уникальных решений", "эстетическому восприятию", "оригинальности", 
            "творческому самовыражению", "инновационным подходам", "дивергентному мышлению"
        ],
        "Аналитический тип": [
            "детальному анализу", "систематизации информации", "выявлению закономерностей",
            "точной оценке данных", "методологическому подходу", "структурированию сложных проблем",
            "последовательной аргументации", "построению логических моделей", "фактологическому анализу",
            "исследовательскому мышлению", "категоризации", "точности формулировок"
        ]
    }
    
    # Задаем дефолтный тип для случаев, когда переданный тип отсутствует в словаре
    default_type = "Интеллектуальный"
    
    # Логируем переданный тип личности
    logger.info(f"Запрошены аспекты для типа личности: {personality_type}")
    
    # Найденные ключевые слова в профиле
    found_keywords = []
    
    # Проверяем наличие ключевых слов для всех типов личности
    all_keywords = []
    for type_keywords in keywords.values():
        all_keywords.extend(type_keywords)
    
    # Ищем ключевые слова в профиле
    for keyword in all_keywords:
        if keyword.lower() in profile_text.lower():
            found_keywords.append(keyword)
    
    # Если нашли достаточно ключевых слов, используем соответствующие аспекты
    if found_keywords:
        # Определяем, к какому типу личности относится большинство найденных ключевых слов
        type_counts = {type_name: 0 for type_name in keywords.keys()}
        for keyword in found_keywords:
            for type_name, type_keywords in keywords.items():
                if keyword.lower() in [k.lower() for k in type_keywords]:
                    type_counts[type_name] += 1
        
        # Определяем доминирующий тип на основе найденных ключевых слов
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
        
        # Проверяем, что оба типа личности (доминирующий и переданный) существуют в словаре аспектов
        dominant_aspects = aspects.get(dominant_type, aspects.get(default_type, []))
        
        # Если переданный тип личности не существует в словаре аспектов, используем дефолтный
        personality_aspects = aspects.get(personality_type, aspects.get(default_type, []))
        
        # Если доминирующий тип не совпадает с заявленным типом личности,
        # используем комбинацию аспектов обоих типов
        if dominant_type != personality_type:
            combined_aspects = personality_aspects + dominant_aspects
            return combined_aspects
        
        return personality_aspects
    
    # Если ключевые слова не найдены, возвращаем аспекты на основе типа личности
    # Используем .get() с дефолтным значением для безопасного получения аспектов
    return aspects.get(personality_type, aspects.get(default_type, []))

def generate_unique_advice(profile_text: str, personality_type: str, history: list) -> str:
    """
    Генерирует уникальный персонализированный совет на основе текста профиля.
    
    Args:
        profile_text: Текст профиля пользователя
        personality_type: Тип личности пользователя
        history: Список уже использованных советов
        
    Returns:
        str: Уникальный персонализированный совет
    """
    # Логируем процесс генерации
    logger.info(f"Генерация уникального совета на основе профиля длиной {len(profile_text)} символов")
    
    # Устанавливаем дефолтный тип личности для случаев, когда переданный тип не найден в словарях
    default_type = "Интеллектуальный"
    
    # Извлекаем ключевые аспекты из профиля
    aspects = extract_key_aspects(profile_text, personality_type)
    
    # Если аспекты не удалось извлечь, используем тип личности
    if not aspects:
        aspects = ["саморазвитию"]  # Универсальный аспект как запасной вариант
    
    # Эмодзи для разных типов советов
    emoji_map = {
        "Интеллектуальный": ["🧠", "📚", "🔍", "🧩", "📝"],
        "Эмоциональный": ["❤️", "🧘", "🙏", "🌱", "🫂"],
        "Практический": ["⏱️", "✅", "📊", "🚫", "📋"],
        "Творческий": ["🎨", "🔄", "🌈", "🧠", "🎭"],
        "Аналитический тип": ["📊", "🔍", "📈", "🧮", "📋"]
    }
    
    # Выбираем случайный эмодзи на основе типа личности
    import random
    emoji_list = emoji_map.get(personality_type, emoji_map.get(default_type, ["💡"]))
    emoji = random.choice(emoji_list)
    
    # Техники для разных типов личности
    techniques = {
        "Интеллектуальный": [
            "технику глубокого чтения", "метод интервального повторения", 
            "технику создания ментальных карт", "метод Фейнмана", 
            "технику активного вопрошания", "SQ3R метод для работы с текстами",
            "технику поиска межпредметных связей", "дебаты с самим собой",
            "технику ведения интеллектуального дневника", "метод соединения идей"
        ],
        "Эмоциональный": [
            "практику осознанности", "технику эмоционального дистанцирования", 
            "методику прогрессивной мышечной релаксации", "практику благодарности", 
            "технику эмоционального картирования", "метод «заземления» эмоций",
            "журнал эмоций", "практику сострадания к себе",
            "технику эмоционального резонанса", "метод переключения эмоциональных состояний"
        ],
        "Практический": [
            "систему Getting Things Done", "технику Помодоро", 
            "метод «3-2-1»", "технику единой задачи", 
            "блокирование времени", "правило двух минут",
            "технику контекстных списков", "еженедельный обзор задач",
            "метод PARA для организации информации", "технику выравнивания энергии"
        ],
        "Творческий": [
            "технику случайных стимулов", "метод шести шляп", 
            "технику творческих ограничений", "метод мозгового штурма наоборот", 
            "практику творческих комбинаций", "метод синектики",
            "технику 'что если'", "метод SCAMPER",
            "технику дивергентного мышления", "метод случайных ассоциаций"
        ],
        "Аналитический тип": [
            "технику декомпозиции сложных проблем", "метод SWOT-анализа", 
            "технику критериального ранжирования", "методологию 5W1H", 
            "технику последовательной декомпозиции", "прием проверки противоположных гипотез",
            "технику анализа корневых причин", "метод систематической проверки фактов",
            "прием построения причинно-следственных диаграмм", "метод ABC-анализа"
        ]
    }
    
    # Контексты применения для разных типов личности
    contexts = {
        "Интеллектуальный": [
            "в процессе обучения новому", "при работе со сложной информацией", 
            "при подготовке к важной презентации", "во время интеллектуального застоя", 
            "для улучшения запоминания", "при анализе сложных проблем",
            "для развития критического мышления", "при работе с абстрактными концепциями",
            "для систематизации знаний", "при освоении новой области знаний"
        ],
        "Эмоциональный": [
            "в стрессовых ситуациях", "при общении с сложными людьми", 
            "когда вы чувствуете эмоциональное выгорание", "в моменты тревоги", 
            "для улучшения отношений с близкими", "при эмоциональных перепадах",
            "в ситуациях конфликта", "для усиления позитивных эмоций",
            "во время важных переговоров", "в периоды эмоциональной нестабильности"
        ],
        "Практический": [
            "при большом объеме задач", "в начале рабочего дня", 
            "при работе над долгосрочными проектами", "когда чувствуете прокрастинацию", 
            "при планировании сложных задач", "для повышения личной эффективности",
            "при внедрении новых привычек", "при управлении несколькими проектами",
            "для достижения баланса работы и отдыха", "при оптимизации рабочих процессов"
        ],
        "Творческий": [
            "при работе над творческими проектами", "когда нужны нестандартные решения", 
            "в моменты творческого блока", "при генерации новых идей", 
            "для развития творческого мышления", "когда нужно преодолеть шаблонное мышление",
            "для нахождения новых подходов к старым проблемам", "при разработке инноваций",
            "в коллективном творческом процессе", "для расширения границ мышления"
        ],
        "Аналитический тип": [
            "при анализе сложных данных", "когда нужно принять обоснованное решение", 
            "при необходимости объективной оценки", "во время сбора и анализа информации", 
            "для выявления скрытых закономерностей", "при разработке аналитических моделей",
            "для построения прогнозов", "при валидации гипотез",
            "в ситуациях, требующих точности и объективности", "при решении многофакторных задач"
        ]
    }
    
    # Результаты/цели для разных типов советов
    results = {
        "Интеллектуальный": [
            "глубину понимания", "долгосрочное запоминание", 
            "аналитические способности", "когнитивную гибкость", 
            "критическое мышление", "способность к синтезу информации",
            "интеллектуальную выносливость", "качество принимаемых решений",
            "скорость обработки информации", "концептуальное мышление"
        ],
        "Эмоциональный": [
            "эмоциональную устойчивость", "глубину эмпатии", 
            "эмоциональный интеллект", "способность к самосостраданию", 
            "качество отношений", "эмоциональное благополучие",
            "способность к регуляции эмоций", "осознанность в отношениях",
            "внутреннюю гармонию", "резилиентность"
        ],
        "Практический": [
            "личную продуктивность", "эффективность рабочих процессов", 
            "достижение целей", "управление временем", 
            "жизненный баланс", "организационные навыки",
            "способность доводить дела до конца", "качество результатов",
            "стабильность рабочих привычек", "уверенность в принятии решений"
        ],
        "Творческий": [
            "творческую продуктивность", "оригинальность идей", 
            "способность к нестандартному мышлению", "инновационный потенциал", 
            "творческую уверенность", "креативное решение проблем",
            "гибкость мышления", "способность видеть возможности",
            "творческую смелость", "расширение творческих горизонтов"
        ],
        "Аналитический тип": [
            "точность анализа", "объективность суждений", 
            "глубину исследования", "обоснованность выводов", 
            "эффективность системного подхода", "способность выявлять закономерности",
            "качество аналитических моделей", "методологическую точность",
            "достоверность результатов", "способность к комплексной оценке"
        ]
    }
    
    # Выбираем ключевой аспект, технику и контекст с использованием .get() для безопасности
    aspect = random.choice(aspects)
    
    # Безопасно получаем списки с fallback на дефолтный тип
    technique_list = techniques.get(personality_type, techniques.get(default_type, ["практику саморазвития"]))
    technique = random.choice(technique_list)
    
    context_list = contexts.get(personality_type, contexts.get(default_type, ["в повседневной жизни"]))
    context = random.choice(context_list)
    
    result_list = results.get(personality_type, results.get(default_type, ["эффективность"]))
    result = random.choice(result_list)
    
    # Формируем совет по шаблону
    advice = f"{emoji} Учитывая вашу склонность к {aspect.lower()}, попробуйте {technique}, чтобы усилить {result}. Это особенно полезно {context}."
    
    # Проверяем, что совет уникален (не повторяется с предыдущими)
    attempts = 0
    while advice in history and attempts < 5:
        # Если совет уже использовался, генерируем новый
        aspect = random.choice(aspects)
        technique = random.choice(technique_list)
        context = random.choice(context_list)
        result = random.choice(result_list)
        emoji = random.choice(emoji_list)
        
        advice = f"{emoji} Учитывая вашу склонность к {aspect.lower()}, попробуйте {technique}, чтобы усилить {result}. Это особенно полезно {context}."
        attempts += 1
    
    # Логируем сгенерированный совет
    logger.info(f"Сгенерирован уникальный совет: {advice[:50]}...")
    
    return advice

# Обработчик для callback "get_advice"
@survey_router.callback_query(F.data == "get_advice")
async def get_advice_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для получения совета через callback.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    # Показываем индикатор "печатает..."
    await callback.message.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    
    # Получаем данные пользователя
    user_data = await state.get_data()
    personality_type = user_data.get("personality_type", "Интеллектуальный")
    profile_details = user_data.get("profile_details", "")
    used_advices = user_data.get("used_advices", [])
    
    # Получаем персонализированный совет
    advice = get_personalized_advice(personality_type, profile_details, used_advices)
    
    # Сохраняем совет в историю
    used_advices.append(advice)
    # Ограничиваем историю последними 20 советами
    if len(used_advices) > 20:
        used_advices = used_advices[-20:]
    await state.update_data(used_advices=used_advices)
    
    # Отправляем совет
    await callback.message.answer(
        f"💡 <b>Персонализированный совет</b>\n\n{advice}",
        parse_mode="HTML"
    )
    
    # Добавляем кнопки для дополнительных действий
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Получить другой совет", callback_data="get_advice")
    builder.button(text="👤 Посмотреть профиль", callback_data="view_profile")
    builder.button(text="◀️ Главное меню", callback_data="main_menu")
    builder.adjust(1)
    
    await callback.message.answer(
        "Что вы хотите сделать дальше?",
        reply_markup=builder.as_markup()
    )
    
    # Возвращаем основную клавиатуру
    await callback.message.answer(
        "⬅️ Вернуться в главное меню",
        reply_markup=get_main_keyboard()
    )
    
    # Отвечаем на callback
    await callback.answer("Совет получен")

# Обработчик команды советов
@survey_router.message(Command("advice"))
@survey_router.message(F.text == "💡 Советы")
async def command_advice(message: Message, state: FSMContext):
    """
    Обработчик команды /advice и кнопки "Советы".
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Получаем данные пользователя
    user_data = await state.get_data()
    profile_completed = user_data.get("profile_completed", False)
    
    if profile_completed:
        # Если профиль есть, получаем тип личности и детали профиля
        personality_type = user_data.get("personality_type", "Интеллектуальный")
        profile_details = user_data.get("profile_details", "")
        used_advices = user_data.get("used_advices", [])
        
        # Получаем персонализированный совет на основе типа личности и профиля
        advice = get_personalized_advice(personality_type, profile_details, used_advices)
        
        # Сохраняем совет в историю
        used_advices.append(advice)
        # Ограничиваем историю последними 20 советами
        if len(used_advices) > 20:
            used_advices = used_advices[-20:]
        await state.update_data(used_advices=used_advices)
        
        # Отправляем совет
        await message.answer(
            f"💡 <b>Персонализированный совет</b>\n\n{advice}",
            parse_mode="HTML"
        )
        
        # Добавляем кнопки для дополнительных действий
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Получить другой совет", callback_data="get_advice")
        builder.button(text="👤 Посмотреть профиль", callback_data="view_profile")
        builder.button(text="◀️ Главное меню", callback_data="main_menu")
        builder.adjust(1)
        
        await message.answer(
            "Что вы хотите сделать дальше?",
            reply_markup=builder.as_markup()
        )
    else:
        # Если профиля нет, предлагаем пройти опрос
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Начать опрос", callback_data="start_survey")
        
        await message.answer(
            "Чтобы получать персонализированные советы, необходимо сначала пройти психологический тест и создать ваш профиль.",
            reply_markup=builder.as_markup()
        )

# Добавляем обработчик для callback "start_survey"
@survey_router.callback_query(F.data == "start_survey")
async def start_survey_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для начала опроса через callback.
    
    Args:
        callback: Callback query
        state: Состояние FSM
    """
    await callback.message.delete()
    await start_survey(callback.message, state)
    await callback.answer("Начинаем опрос")

# Добавляем функцию для тестирования интерпретаций ответов
async def test_interpretations():
    """
    Тестовая функция для проверки работы интерпретаций ответов.
    """
    from questions import get_all_vasini_questions
    
    # Получаем списки вопросов
    vasini_questions = get_all_vasini_questions()
    
    # Выбираем первый вопрос для теста
    test_question = vasini_questions[0]
    print(f"Тестовый вопрос: {test_question['text']}")
    
    # Выводим варианты ответов
    for option, text in test_question['options'].items():
        print(f"{option}: {text}")
    
    # Тестируем получение интерпретации для варианта A
    option = "A"
    try:
        interpretation = test_question["interpretations"][option]
        print(f"\nИнтерпретация для варианта {option}:\n{interpretation}")
        print("\nПроверка успешна! Интерпретации работают корректно.")
    except Exception as e:
        print(f"Ошибка при получении интерпретации: {e}")

# Добавляем в конец файла для запуска теста при прямом вызове
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_interpretations()) 
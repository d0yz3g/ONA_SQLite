@echo off
title ONA Bot Launcher
echo ===================================
echo Запуск бота ОНА с предварительной очисткой
echo ===================================
echo.

REM Активируем виртуальное окружение, если оно есть
if exist .venv\Scripts\activate.bat (
    echo Активация виртуального окружения...
    call .venv\Scripts\activate.bat
)

REM Очищаем все блокировки и процессы
echo Очистка всех блокировок и процессов...
python cleanup.py

REM Небольшая пауза для завершения всех процессов
echo Ожидание 3 секунды перед запуском бота...
timeout /t 3 /nobreak >nul

REM Запуск бота через restart_bot.py
echo Запуск бота...
python restart_bot.py

REM Если бот завершился, держим окно открытым
pause 
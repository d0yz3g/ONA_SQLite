#!/usr/bin/env python
"""
Модуль для настройки логирования в Railway.
Обеспечивает правильное отображение уровней логирования с русскоязычными префиксами.
"""

import sys
import logging
from logging import StreamHandler, Formatter
from datetime import datetime

def get_time():
    """
    Возвращает текущее время в формате для логов.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class RailwayFormatter(Formatter):
    """
    Форматтер для логов в Railway, добавляющий русскоязычные префиксы.
    """
    
    def __init__(self):
        super().__init__()
        
        # Форматы для разных уровней логирования
        self.formatters = {
            logging.DEBUG: Formatter("ОТЛАДКА: %(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            logging.INFO: Formatter("ИНФО: %(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            logging.WARNING: Formatter("ПРЕДУПРЕЖДЕНИЕ: %(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            logging.ERROR: Formatter("ОШИБКА: %(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            logging.CRITICAL: Formatter("КРИТИЧЕСКАЯ ОШИБКА: %(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        }
    
    def format(self, record):
        """
        Форматирует запись лога в зависимости от уровня.
        """
        formatter = self.formatters.get(record.levelno, self.formatters[logging.INFO])
        return formatter.format(record)

class RailwayHandler(StreamHandler):
    """
    Обработчик логов для Railway, который выводит все в stdout
    и форматирует сообщения с правильными префиксами.
    """
    
    def __init__(self):
        super().__init__(stream=sys.stdout)
        self.setFormatter(RailwayFormatter())
    
    def emit(self, record):
        """
        Выводит запись лога в stdout с принудительным сбросом буфера.
        """
        super().emit(record)
        self.flush()  # Принудительно сбрасываем буфер для Railway

def setup_railway_logging(logger_name=None, level=logging.INFO):
    """
    Настраивает логирование для Railway.
    
    Args:
        logger_name: Имя логгера
        level: Уровень логирования
        
    Returns:
        Logger: Настроенный логгер
    """
    # Получаем или создаем логгер
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Удаляем существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Добавляем наш обработчик для Railway
    handler = RailwayHandler()
    logger.addHandler(handler)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, StreamHandler):
            root_logger.removeHandler(handler)
    
    root_handler = RailwayHandler()
    root_logger.addHandler(root_handler)
    
    return logger

def railway_print(message, level="INFO"):
    """
    Выводит сообщение в формате для Railway.
    
    Args:
        message: Сообщение для вывода
        level: Уровень сообщения (INFO, ERROR, WARNING, DEBUG)
    """
    prefix = "ИНФО"
    if level.upper() == "ERROR":
        prefix = "ОШИБКА"
    elif level.upper() == "WARNING":
        prefix = "ПРЕДУПРЕЖДЕНИЕ"
    elif level.upper() == "DEBUG":
        prefix = "ОТЛАДКА"
    elif level.upper() == "CRITICAL":
        prefix = "КРИТИЧЕСКАЯ ОШИБКА"
    
    print(f"{prefix}: {message}")
    sys.stdout.flush()  # Принудительно сбрасываем буфер для Railway

# Если запускаем как отдельный скрипт, настраиваем логирование
if __name__ == "__main__":
    print("=" * 50)
    print("НАСТРОЙКА ЛОГИРОВАНИЯ ДЛЯ RAILWAY")
    print("=" * 50)
    
    # Настраиваем логирование
    logger = setup_railway_logging("railway_logging_test")
    
    # Проверяем разные уровни логирования
    logger.debug("Это отладочное сообщение")
    logger.info("Это информационное сообщение")
    logger.warning("Это предупреждение")
    logger.error("Это сообщение об ошибке")
    logger.critical("Это критическая ошибка")
    
    # Проверяем функцию railway_print
    railway_print("Тестовое сообщение через railway_print")
    railway_print("Предупреждение через railway_print", level="WARNING")
    railway_print("Ошибка через railway_print", level="ERROR")
    
    print("=" * 50)
    print("ЗАВЕРШЕНИЕ НАСТРОЙКИ ЛОГИРОВАНИЯ")
    print("=" * 50) 
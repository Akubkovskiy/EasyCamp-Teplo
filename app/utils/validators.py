"""
Утилиты валидации данных
"""

import re
from datetime import datetime
from typing import Optional, Tuple


def validate_phone(phone: str) -> bool:
    """
    Валидация номера телефона.
    Поддерживает форматы: +79991234567, 89991234567, 79991234567
    """
    # Удаляем все кроме цифр и плюса
    clean_phone = re.sub(r"[^0-9+]", "", phone)

    # Проверка длины и формата
    pattern = r"^(\+7|8|7)\d{10}$"
    return bool(re.match(pattern, clean_phone))


def format_phone(phone: str) -> str:
    """
    Форматирование телефона в стандартный вид +7 (XXX) XXX-XX-XX
    """
    # Удаляем все нецифровые символы
    clean_phone = re.sub(r"[^0-9]", "", phone)

    # Если номер пустой или слишком короткий, возвращаем как есть
    if len(clean_phone) < 10:
        return phone

    # Нормализация к 7XXXXXXXXXX
    if len(clean_phone) == 11:
        if clean_phone.startswith("8"):
            clean_phone = "7" + clean_phone[1:]
        elif clean_phone.startswith("7"):
            pass  # уже 7...
    elif len(clean_phone) == 10:
        # Если 10 цифр (9991234567), добавляем 7
        clean_phone = "7" + clean_phone

    # Форматирование
    if len(clean_phone) == 11 and clean_phone.startswith("7"):
        return f"+{clean_phone[0]} ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:9]}-{clean_phone[9:]}"

    return phone


def validate_dates(check_in: str, check_out: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация дат заезда и выезда
    Возвращает (is_valid, error_message)
    """
    try:
        start = datetime.strptime(check_in, "%Y-%m-%d").date()
        end = datetime.strptime(check_out, "%Y-%m-%d").date()
        today = datetime.now().date()

        if start < today:
            return False, "Дата заезда не может быть в прошлом"

        if end <= start:
            return False, "Дата выезда должна быть позже даты заезда"

        return True, None
    except ValueError:
        return False, "Неверный формат даты"

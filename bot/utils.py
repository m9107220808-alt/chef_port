import re
from typing import Optional


def format_phone(phone: str) -> str:
    """Форматирование телефона в единый формат"""
    digits = re.sub(r'\D', '', phone)
    
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    
    if len(digits) == 11:
        return f"+{digits[0]}({digits[1:4]}){digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return phone


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста с добавлением многоточия"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

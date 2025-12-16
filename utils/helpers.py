#!/usr/bin/env python3
"""
Вспомогательные функции
"""

import random
import string
from typing import List, Tuple

def generate_password(length: int = 12) -> str:
    """Генерация случайного пароля"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def parse_attributes(text: str) -> List[Tuple[str, str]]:
    """Парсинг строки с атрибутами в формате Атрибут=Значение"""
    attributes = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                attr, value = line.split('=', 1)
                attributes.append((attr.strip(), value.strip()))
    
    return attributes

def validate_username(username: str) -> Tuple[bool, str]:
    """Валидация имени пользователя"""
    if not username:
        return False, "Имя пользователя не может быть пустым"
    
    if len(username) > 64:
        return False, "Имя пользователя не должно превышать 64 символа"
    
    # Проверка на запрещенные символы
    forbidden_chars = ['"', "'", ';', ',', '=', '>', '<', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', ' ', '\t']
    for char in forbidden_chars:
        if char in username:
            return False, f"Имя пользователя содержит запрещенный символ: {char}"
    
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """Валидация пароля"""
    if not password:
        return False, "Пароль не может быть пустым"
    
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    
    return True, ""

def split_csv_line(line: str) -> List[str]:
    """Разбор строки CSV с учетом кавычек"""
    result = []
    current = ''
    in_quotes = False
    
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            result.append(current)
            current = ''
        else:
            current += char
    
    result.append(current)
    return [item.strip() for item in result]

def format_file_size(size_in_bytes: int) -> str:
    """Форматирование размера файла"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def get_connection_colors(status: bool) -> Tuple[str, str]:
    """Получение цветов для индикатора подключения"""
    if status:
        return "green", "●"
    else:
        return "red", "●"

def center_window(window, width: int = None, height: int = None):
    """Центрирование окна на экране"""
    window.update_idletasks()
    
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()
    
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    
    window.geometry(f'{width}x{height}+{x}+{y}')
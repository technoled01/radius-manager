#!/usr/bin/env python3
"""
Модуль логирования
"""

from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

class Logger:
    """Класс для логирования сообщений"""
    
    def __init__(self, log_widget: scrolledtext.ScrolledText = None, status_label: tk.Label = None):
        self.log_widget = log_widget
        self.status_label = status_label
        self.messages = []
    
    def log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Сохраняем в памяти
        self.messages.append(log_entry)
        
        # Выводим в виджет, если он есть
        if self.log_widget:
            self.log_widget.configure(state='normal')
            self.log_widget.insert(tk.END, log_entry + "\n")
            self.log_widget.see(tk.END)
            self.log_widget.configure(state='disabled')
        
        # Обновляем статус бар, если он есть
        if self.status_label:
            self.status_label.config(text=message[:100])
        
        # Также выводим в консоль для отладки
        print(log_entry)
    
    def clear(self):
        """Очистка лога"""
        self.messages = []
        if self.log_widget:
            self.log_widget.configure(state='normal')
            self.log_widget.delete(1.0, tk.END)
            self.log_widget.configure(state='disabled')
    
    def get_messages(self, count: int = None):
        """Получение последних сообщений"""
        if count is None:
            return self.messages
        return self.messages[-count:]
    
    def set_log_widget(self, log_widget: scrolledtext.ScrolledText):
        """Установка виджета для вывода лога"""
        self.log_widget = log_widget
    
    def set_status_label(self, status_label: tk.Label):
        """Установка метки статуса"""
        self.status_label = status_label
#!/usr/bin/env python3
"""
Виджеты для GUI
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Any

class StyledButton(tk.Button):
    """Стилизованная кнопка"""
    
    def __init__(self, master, text: str, command: Callable = None, 
                 color: str = '#4CAF50', hover_color: str = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.text = text
        self.color = color
        self.hover_color = hover_color or self._lighten_color(color)
        self.default_color = color
        
        self.config(
            text=text,
            bg=color,
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=command,
            padx=15,
            pady=5
        )
        
        # Эффект наведения
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _lighten_color(self, color: str) -> str:
        """Осветление цвета для эффекта hover"""
        # Простая реализация - можно заменить на более сложную
        if color == '#4CAF50':  # primary
            return '#5CBF60'
        elif color == '#2196F3':  # secondary
            return '#33A6FF'
        elif color == '#f44336':  # danger
            return '#FF5555'
        elif color == '#FF9800':  # warning
            return '#FFAD33'
        return color
    
    def _on_enter(self, event):
        self.config(bg=self.hover_color)
    
    def _on_leave(self, event):
        self.config(bg=self.default_color)

class StatusBar(tk.Frame):
    """Строка состояния"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.config(bg='#e0e0e0', relief=tk.SUNKEN, bd=1)
        
        self.status_label = tk.Label(
            self, 
            text="Готово к работе",
            bg='#e0e0e0',
            fg='#333333'
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Индикатор подключения
        self.connection_indicator = tk.Label(
            self, 
            text="●", 
            fg="red", 
            font=('Arial', 12, 'bold'),
            bg='#e0e0e0'
        )
        self.connection_indicator.pack(side=tk.RIGHT, padx=5)
        
        tk.Label(
            self, 
            text="Статус:",
            bg='#e0e0e0',
            fg='#333333'
        ).pack(side=tk.RIGHT, padx=(10, 0))
    
    def set_status(self, text: str):
        """Установка текста статуса"""
        self.status_label.config(text=text)
    
    def set_connection_status(self, connected: bool):
        """Установка статуса подключения"""
        color = "green" if connected else "red"
        self.connection_indicator.config(fg=color)

class ToolBar(tk.Frame):
    """Панель инструментов"""
    
    def __init__(self, master, buttons: List[Dict[str, Any]] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.config(bg='#333333', height=50)
        
        # Заголовок
        self.title_label = tk.Label(
            self, 
            text="RADIUS User Manager - MSSQL", 
            font=('Arial', 14, 'bold'),
            bg='#333333',
            fg='white'
        )
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        # Кнопки управления
        self.buttons_frame = tk.Frame(self, bg='#333333')
        self.buttons_frame.pack(side=tk.RIGHT, padx=10)
        
        if buttons:
            for button_info in buttons:
                self.add_button(**button_info)
    
    def add_button(self, text: str, command: Callable, color: str = '#4CAF50'):
        """Добавление кнопки на панель"""
        btn = StyledButton(
            self.buttons_frame,
            text=text,
            command=command,
            color=color
        )
        btn.pack(side=tk.LEFT, padx=2)
        return btn

class ScrollableFrame(ttk.Frame):
    """Прокручиваемый фрейм"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Привязка колесика мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

class EditableTreeview(ttk.Treeview):
    """Редактируемый Treeview"""
    
    def __init__(self, master, editable_columns: List[str] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.editable_columns = editable_columns or []
        self.bind('<Double-1>', self._on_double_click)
        
        # Переменные для редактирования
        self.edit_entry = None
        self.edit_column = None
        self.edit_item = None
    
    def _on_double_click(self, event):
        """Обработка двойного клика для редактирования"""
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return
        
        column = self.identify_column(event.x)
        item = self.identify_row(event.y)
        
        if not item or column not in self.editable_columns:
            return
        
        # Получаем текущее значение
        column_index = int(column.replace('#', '')) - 1
        current_value = self.item(item)['values'][column_index]
        
        # Позиция и размеры ячейки
        x, y, width, height = self.bbox(item, column)
        
        # Создаем поле для редактирования
        self.edit_entry = tk.Entry(self, borderwidth=0)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.focus_set()
        
        self.edit_item = item
        self.edit_column = column_index
        
        # Привязка событий
        self.edit_entry.bind('<Return>', self._save_edit)
        self.edit_entry.bind('<Escape>', self._cancel_edit)
        self.edit_entry.bind('<FocusOut>', self._save_edit)
    
    def _save_edit(self, event):
        """Сохранение изменений"""
        if not self.edit_entry:
            return
        
        new_value = self.edit_entry.get()
        item = self.edit_item
        column = self.edit_column
        
        # Обновляем значение
        values = list(self.item(item)['values'])
        values[column] = new_value
        self.item(item, values=values)
        
        self._cancel_edit()
    
    def _cancel_edit(self, event=None):
        """Отмена редактирования"""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
            self.edit_item = None
            self.edit_column = None
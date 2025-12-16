#!/usr/bin/env python3
"""
Главное окно приложения
"""

import tkinter as tk
from tkinter import ttk
from config import ConfigManager
from database import DatabaseManager
from utils.logger import Logger
from gui.widgets import ToolBar, StatusBar
from gui.tabs.connection_tab import ConnectionTab
from gui.tabs.users_tab import UsersTab
from gui.tabs.add_user_tab import AddUserTab
from gui.tabs.groups_tab import GroupsTab
from gui.tabs.bulk_tab import BulkTab

class RadiusManagerMainWindow:
    """Главное окно управления RADIUS пользователями"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("RADIUS User Manager v2.0 - MSSQL")
        
        # Инициализация компонентов
        self.config_manager = ConfigManager()
        self.logger = Logger()
        self.db = DatabaseManager(logger=self.logger)
        
        # Получаем конфигурацию
        self.config = self.config_manager.get_application_config()
        
        # Устанавливаем размер окна
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.center_window()
        
        # Устанавливаем стили
        self.setup_styles()
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Автоподключение
        self.auto_connect()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """Настройка стилей виджетов"""
        style = ttk.Style()
        style.theme_use(self.config.theme)
        
        # Настройка цветов
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Success.TButton', foreground='green')
        style.configure('Danger.TButton', foreground='red')
        
        # Цвета для кнопок
        self.colors = {
            'primary': '#4CAF50',
            'secondary': '#2196F3',
            'danger': '#f44336',
            'warning': '#FF9800',
            'dark': '#333333'
        }
    
    def create_widgets(self):
        """Создание интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Верхняя панель с кнопками
        self.create_toolbar(main_frame)
        
        # Панель статуса
        self.status_bar = StatusBar(main_frame)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.logger.set_status_label(self.status_bar.status_label)
        
        # Основная область с вкладками
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Создаем вкладки
        self.create_tabs()
        
        # Устанавливаем первую вкладку активной
        self.notebook.select(0)
    
    def create_toolbar(self, parent):
        """Панель инструментов"""
        toolbar = ToolBar(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Кнопки управления
        buttons = [
            {"text": "Подключить", "command": self.connect_db, "color": self.colors['primary']},
            {"text": "Отключить", "command": self.disconnect_db, "color": self.colors['danger']},
            {"text": "Обновить", "command": self.refresh_all, "color": self.colors['secondary']},
            {"text": "Настройки", "command": self.show_settings, "color": self.colors['warning']},
        ]
        
        for button_info in buttons:
            toolbar.add_button(**button_info)
    
    def create_tabs(self):
        """Создание всех вкладок"""
        # Вкладка подключения
        self.connection_tab = ConnectionTab(
            self.notebook, 
            self.config_manager, 
            self.db, 
            self.logger
        )
        self.notebook.add(self.connection_tab.frame, text="Подключение")
        
        # Вкладка пользователей
        self.users_tab = UsersTab(
            self.notebook,
            self.db,
            self.logger,
            self.status_bar
        )
        self.notebook.add(self.users_tab.frame, text="Пользователи")
        
        # Вкладка добавления пользователя
        self.add_user_tab = AddUserTab(
            self.notebook,
            self.db,
            self.logger
        )
        self.notebook.add(self.add_user_tab.frame, text="Добавить пользователя")
        
        # Вкладка групп
        self.groups_tab = GroupsTab(
            self.notebook,
            self.db,
            self.logger
        )
        self.notebook.add(self.groups_tab.frame, text="Группы")
        
        # Вкладка массовых операций
        self.bulk_tab = BulkTab(
            self.notebook,
            self.db,
            self.logger
        )
        self.notebook.add(self.bulk_tab.frame, text="Массовые операции")
    
    def auto_connect(self):
        """Автоподключение к БД при запуске"""
        db_config = self.config_manager.get_database_config()
        if db_config.autoconnect:
            self.connect_db()
    
    def connect_db(self):
        """Подключение к базе данных"""
        if self.connection_tab.connect():
            self.status_bar.set_connection_status(True)
            self.logger.log("Успешное подключение к базе данных")
            
            # Обновляем данные во вкладках
            self.refresh_all()
            
            # Переключаемся на вкладку пользователей
            self.notebook.select(1)
        else:
            self.status_bar.set_connection_status(False)
            self.logger.log("Не удалось подключиться к базе данных")
    
    def disconnect_db(self):
        """Отключение от базы данных"""
        if self.db.disconnect():
            self.status_bar.set_connection_status(False)
            self.logger.log("Отключено от базы данных")
            
            # Очищаем данные во вкладках
            self.users_tab.clear_users()
            self.groups_tab.clear_groups()
        else:
            self.logger.log("Ошибка отключения от базы данных")
    
    def refresh_all(self):
        """Обновление всех данных"""
        if self.db.connection_status:
            self.users_tab.load_users()
            self.groups_tab.load_groups()
            self.add_user_tab.update_groups()   # Добавлено
            self.bulk_tab.update_groups()       # Добавлено
            self.logger.log("Данные обновлены")
        else:
            self.logger.log("Нет подключения к БД. Подключитесь сначала.")
    
    def show_settings(self):
        """Показать окно настроек"""
        self.notebook.select(0)  # Переключаемся на вкладку подключения
    
    def on_closing(self):
        """Обработка закрытия окна"""
        import tkinter.messagebox as messagebox
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            if self.db.conn:
                try:
                    self.db.disconnect()
                    self.logger.log("Программа завершена")
                except:
                    pass
            
            self.root.destroy()
    
    def update_connection_status(self, connected: bool):
        """Обновление статуса подключения"""
        self.status_bar.set_connection_status(connected)
        if connected:
            self.refresh_all()
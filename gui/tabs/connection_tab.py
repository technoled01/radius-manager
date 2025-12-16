#!/usr/bin/env python3
"""
Вкладка подключения к базе данных
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Callable

class ConnectionTab:
    """Вкладка для настройки подключения к БД"""
    
    def __init__(self, parent, config_manager, db_manager, logger):
        self.parent = parent
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = logger
        
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self._load_config()
    
    def _create_widgets(self):
        """Создание виджетов вкладки"""
        # Основной фрейм
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - настройки
        left_frame = ttk.LabelFrame(main_frame, text="Параметры подключения MSSQL", padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        fields = [
            ("Драйвер ODBC:", "driver", "ODBC Driver 17 for SQL Server", False),
            ("Сервер:", "server", "localhost", False),
            ("Порт:", "port", "1433", False),
            ("База данных:", "database", "radius", False),
            ("Имя пользователя:", "username", "sa", False),
            ("Пароль:", "password", "", True),
        ]
        
        self.conn_entries = {}
        
        for i, (label, key, default, is_password) in enumerate(fields):
            row_frame = ttk.Frame(left_frame)
            row_frame.pack(fill=tk.X, pady=8)
            
            ttk.Label(row_frame, text=label, width=20).pack(side=tk.LEFT)
            
            entry = tk.Entry(row_frame, show="*" if is_password else None, width=35)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.conn_entries[key] = entry
        
        # Дополнительные опции
        options_frame = ttk.Frame(left_frame)
        options_frame.pack(fill=tk.X, pady=15)
        
        self.trusted_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Trusted Connection", 
                       variable=self.trusted_var,
                       command=self._toggle_auth_method).pack(side=tk.LEFT, padx=(0, 20))
        
        self.encrypt_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Encrypt", 
                       variable=self.encrypt_var).pack(side=tk.LEFT)
        
        # Кнопки управления подключением
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(btn_frame, text="Сохранить настройки", 
                  command=self._save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Тест подключения", 
                  command=self._test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Восстановить по умолчанию", 
                  command=self._restore_defaults).pack(side=tk.LEFT, padx=5)
        
        # Правая панель - информация и лог
        right_frame = ttk.LabelFrame(main_frame, text="Информация и лог", padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Информация о подключении
        info_text = """Параметры подключения MSSQL:

1. Драйвер ODBC - должен быть установлен на системе
2. Сервер - имя или IP адрес SQL Server
3. Порт - по умолчанию 1433
4. Имя базы данных - должна существовать
5. Учетные данные - имя пользователя и пароль

Для Windows Authentication используйте
Trusted Connection (без имени/пароля)."""
        
        info_label = tk.Label(
            right_frame, 
            text=info_text,
            justify=tk.LEFT,
            bg='#f9f9f9',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        info_label.pack(fill=tk.X, pady=(0, 15))
        
        # Лог подключения
        log_frame = ttk.LabelFrame(right_frame, text="Лог подключения", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.conn_log = scrolledtext.ScrolledText(
            log_frame, 
            height=10, 
            state='normal',
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.conn_log.pack(fill=tk.BOTH, expand=True)
        
        # Устанавливаем виджет лога в logger
        self.logger.set_log_widget(self.conn_log)
    
    def _load_config(self):
        """Загрузка конфигурации"""
        config = self.config_manager.get_database_config()
        
        self.conn_entries['driver'].delete(0, tk.END)
        self.conn_entries['driver'].insert(0, config.driver)
        
        self.conn_entries['server'].delete(0, tk.END)
        self.conn_entries['server'].insert(0, config.server)
        
        self.conn_entries['port'].delete(0, tk.END)
        self.conn_entries['port'].insert(0, config.port)
        
        self.conn_entries['database'].delete(0, tk.END)
        self.conn_entries['database'].insert(0, config.database)
        
        self.conn_entries['username'].delete(0, tk.END)
        self.conn_entries['username'].insert(0, config.username)
        
        self.conn_entries['password'].delete(0, tk.END)
        self.conn_entries['password'].insert(0, config.password)
        
        self.trusted_var.set(config.trusted_connection)
        self.encrypt_var.set(config.encrypt)
        
        self._toggle_auth_method()
    
    def _toggle_auth_method(self):
        """Переключение метода аутентификации"""
        if self.trusted_var.get():
            self.conn_entries['username'].config(state='disabled')
            self.conn_entries['password'].config(state='disabled')
        else:
            self.conn_entries['username'].config(state='normal')
            self.conn_entries['password'].config(state='normal')
    
    def _save_settings(self):
        """Сохранение настроек подключения"""
        try:
            # Обновляем конфиг
            self.config_manager.update_database_config(
                driver=self.conn_entries['driver'].get(),
                server=self.conn_entries['server'].get(),
                port=self.conn_entries['port'].get(),
                database=self.conn_entries['database'].get(),
                username=self.conn_entries['username'].get(),
                password=self.conn_entries['password'].get(),
                trusted_connection=self.trusted_var.get(),
                encrypt=self.encrypt_var.get()
            )
            
            # Сохраняем в файл
            if self.config_manager.save():
                self.logger.log("Настройки подключения сохранены")
                messagebox.showinfo("Сохранено", "Настройки подключения сохранены!")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить настройки!")
            
        except Exception as e:
            self.logger.log(f"Ошибка сохранения настроек: {str(e)}")
            messagebox.showerror("Ошибка", str(e))
    
    def _test_connection(self):
        """Тестирование подключения к БД"""
        try:
            # Получаем текущие настройки
            config = self.config_manager.get_database_config()
            
            # Временно обновляем настройки из полей ввода
            config.driver = self.conn_entries['driver'].get()
            config.server = self.conn_entries['server'].get()
            config.port = self.conn_entries['port'].get()
            config.database = self.conn_entries['database'].get()
            config.username = self.conn_entries['username'].get()
            config.password = self.conn_entries['password'].get()
            config.trusted_connection = self.trusted_var.get()
            config.encrypt = self.encrypt_var.get()
            
            # Тестируем подключение
            success, message = self.db_manager.test_connection(config)
            
            if success:
                self.logger.log("Тест подключения успешен")
                messagebox.showinfo("Тест подключения", 
                    f"Подключение успешно установлено!\n\n{message}")
            else:
                self.logger.log(f"Тест подключения не удался: {message}")
                messagebox.showerror("Ошибка подключения", 
                    f"Не удалось подключиться:\n\n{message}\n\n"
                    f"Проверьте:\n"
                    f"1. Запущен ли SQL Server\n"
                    f"2. Правильность параметров подключения\n"
                    f"3. Установлен ли драйвер ODBC")
            
        except Exception as e:
            self.logger.log(f"Ошибка тестирования подключения: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка тестирования подключения:\n{str(e)}")
    
    def _restore_defaults(self):
        """Восстановление настроек по умолчанию"""
        if messagebox.askyesno("Подтверждение", "Восстановить настройки по умолчанию?"):
            self.config_manager.restore_defaults()
            self._load_config()
            self.logger.log("Настройки восстановлены по умолчанию")
    
    def connect(self):
        """Подключение к базе данных"""
        try:
            # Обновляем конфиг из полей ввода
            self.config_manager.update_database_config(
                driver=self.conn_entries['driver'].get(),
                server=self.conn_entries['server'].get(),
                port=self.conn_entries['port'].get(),
                database=self.conn_entries['database'].get(),
                username=self.conn_entries['username'].get(),
                password=self.conn_entries['password'].get(),
                trusted_connection=self.trusted_var.get(),
                encrypt=self.encrypt_var.get()
            )
            
            config = self.config_manager.get_database_config()
            
            if self.db_manager.connect(config):
                return True
            else:
                return False
            
        except Exception as e:
            self.logger.log(f"Ошибка подключения: {str(e)}")
            return False
#!/usr/bin/env python3
"""
Вкладка добавления нового пользователя
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import string
from datetime import datetime, timedelta
from database import User, Attribute
from utils.helpers import generate_password

class AddUserTab:
    """Вкладка для добавления нового пользователя"""
    
    def __init__(self, parent, db_manager, logger):
        self.parent = parent
        self.db = db_manager
        self.logger = logger
        
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self._load_groups()  # Загружаем группы при инициализации
    
    def _create_widgets(self):
        """Создание виджетов вкладки"""
        # Основной фрейм с двумя колонками
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая колонка - основные данные
        left_frame = ttk.LabelFrame(main_frame, text="Основные данные", padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        fields = [
            ("Имя пользователя*:", "username", False),
            ("Пароль*:", "password", True),
            ("Подтверждение пароля*:", "confirm_password", True),
            ("Группа:", "group", False),
            ("Срок действия:", "expiration", False),
            ("Макс. сессий:", "simultaneous_use", False),
            ("Session-Timeout (сек):", "session_timeout", False),
            ("Idle-Timeout (сек):", "idle_timeout", False),
        ]
        
        self.user_entries = {}
        
        for i, (label, field, is_password) in enumerate(fields):
            row_frame = ttk.Frame(left_frame)
            row_frame.pack(fill=tk.X, pady=6)
            
            ttk.Label(row_frame, text=label, width=25).pack(side=tk.LEFT)
            
            if field == 'group':
                # Выпадающий список для групп
                var = tk.StringVar()
                var.set("users")  # Значение по умолчанию
                
                self.group_combobox = ttk.Combobox(row_frame, textvariable=var, 
                                                    values=["users"],  # Начальное значение
                                                    width=25, state="readonly")
                self.group_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.user_entries[field] = var
                
            elif field in ['simultaneous_use', 'session_timeout', 'idle_timeout']:
                # Спинбокс для числовых значений
                var = tk.StringVar(value="1" if field == 'simultaneous_use' else "3600")
                spinbox = tk.Spinbox(row_frame, from_=1, to=99999, textvariable=var, width=25)
                spinbox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.user_entries[field] = var
            else:
                # Обычное поле ввода
                var = tk.StringVar()
                if is_password:
                    entry = tk.Entry(row_frame, textvariable=var, show="*", width=27)
                else:
                    entry = tk.Entry(row_frame, textvariable=var, width=27)
                entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.user_entries[field] = var
        
        # Генератор паролей
        pass_gen_frame = ttk.Frame(left_frame)
        pass_gen_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(pass_gen_frame, text="Сгенерировать пароль", 
                  command=self._generate_password).pack(side=tk.LEFT, padx=5)
        
        self.pass_length_var = tk.StringVar(value="12")
        ttk.Label(pass_gen_frame, text="Длина:").pack(side=tk.LEFT, padx=(10, 2))
        ttk.Entry(pass_gen_frame, textvariable=self.pass_length_var, width=5).pack(side=tk.LEFT)
        
        # Правая колонка - дополнительные атрибуты
        right_frame = ttk.LabelFrame(main_frame, text="Дополнительные атрибуты", padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Быстрые атрибуты
        quick_attrs_frame = ttk.LabelFrame(right_frame, text="Быстрые атрибуты", padding=10)
        quick_attrs_frame.pack(fill=tk.X, pady=(0, 10))
        
        quick_attrs = [
            ("Framed-Protocol", "PPP"),
            ("Service-Type", "Framed-User"),
            ("Framed-Compression", "Van-Jacobson-TCP-IP"),
            ("WISPr-Bandwidth-Max-Up", "1024000"),
            ("WISPr-Bandwidth-Max-Down", "2048000"),
        ]
        
        self.quick_attr_vars = {}
        
        for i, (attr, default) in enumerate(quick_attrs):
            attr_frame = ttk.Frame(quick_attrs_frame)
            attr_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(attr_frame, text=attr, width=25).pack(side=tk.LEFT)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(attr_frame, textvariable=var, width=20)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.quick_attr_vars[attr] = var
        
        # Расширенные атрибуты
        attrs_frame = ttk.LabelFrame(right_frame, text="Расширенные атрибуты", padding=10)
        attrs_frame.pack(fill=tk.BOTH, expand=True)
        
        self.attrs_text = scrolledtext.ScrolledText(attrs_frame, height=10, width=40)
        self.attrs_text.pack(fill=tk.BOTH, expand=True)
        
        # Подсказка
        hint = """# Формат: Атрибут=Значение
# По одному атрибуту на строку
# Примеры:
# Mikrotik-Rate-Limit=512k/2M
# Framed-IP-Address=10.0.0.100
# Calling-Station-Id=00:11:22:33:44:55
# NAS-IP-Address=192.168.1.1
"""
        self.attrs_text.insert(1.0, hint)
        
        # Кнопки
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Добавить пользователя", 
                  command=self._add_user, 
                  style='Success.TButton',
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить форму", 
                  command=self._clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Проверить доступность", 
                  command=self._check_username).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Заполнить тестовыми данными", 
                  command=self._fill_test_data).pack(side=tk.LEFT, padx=5)
    
    def _load_groups(self):
        """Загрузка списка групп из БД"""
        try:
            if self.db.connection_status:
                groups = self.db.get_groups()
                if groups:
                    group_names = [group.name for group in groups if group.name and not group.name.startswith('_group_')]
                    
                    if group_names:
                        # Обновляем список в комбобоксе
                        self.group_combobox['values'] = group_names
                        
                        # Если текущее значение не в списке, устанавливаем первое значение
                        current_value = self.user_entries.get('group', tk.StringVar()).get()
                        if current_value not in group_names:
                            self.user_entries['group'].set(group_names[0])
                else:
                    # Если групп нет, используем значение по умолчанию
                    self.group_combobox['values'] = ["users"]
                    self.user_entries['group'].set("users")
            else:
                # Если нет подключения, используем значение по умолчанию
                self.group_combobox['values'] = ["users"]
                self.user_entries['group'].set("users")
                
        except Exception as e:
            self.logger.log(f"Ошибка загрузки групп: {str(e)}")
            # В случае ошибки используем значение по умолчанию
            self.group_combobox['values'] = ["users"]
            self.user_entries['group'].set("users")
    
    def _generate_password(self):
        """Генерация случайного пароля"""
        try:
            length = int(self.pass_length_var.get())
            password = generate_password(length)
            
            # Устанавливаем пароль в поля
            self.user_entries['password'].set(password)
            self.user_entries['confirm_password'].set(password)
            
            self.logger.log(f"Сгенерирован пароль длиной {length} символов")
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная длина пароля")
    
    def _fill_test_data(self):
        """Заполнение формы тестовыми данными"""
        # Генерируем случайное имя пользователя
        username = 'testuser_' + ''.join(random.choice(string.digits) for _ in range(4))
        
        # Генерируем пароль
        password = 'TestPass' + ''.join(random.choice(string.digits) for _ in range(3))
        
        # Заполняем поля
        self.user_entries['username'].set(username)
        self.user_entries['password'].set(password)
        self.user_entries['confirm_password'].set(password)
        
        # Выбираем случайную группу
        groups = self.group_combobox['values']
        if groups and len(groups) > 0:
            try:
                self.user_entries['group'].set(random.choice(groups))
            except:
                pass
        
        # Случайная дата истечения (в течение года)
        expiration = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
        self.user_entries['expiration'].set(expiration)
        
        self.logger.log(f"Заполнены тестовые данные для пользователя: {username}")
    
    def _check_username(self):
        """Проверка доступности имени пользователя"""
        username = self.user_entries['username'].get().strip()
        
        if not username:
            messagebox.showwarning("Внимание", "Введите имя пользователя для проверки")
            return
        
        if self.db.connection_status and self.db.user_exists(username):
            messagebox.showwarning("Занято", f"Имя пользователя '{username}' уже занято!")
        else:
            messagebox.showinfo("Доступно", f"Имя пользователя '{username}' доступно!")
    
    def _add_user(self):
        """Добавление нового пользователя"""
        if not self.db.connection_status:
            messagebox.showerror("Ошибка", "Нет подключения к БД!")
            return
        
        # Получаем данные из формы
        username = self.user_entries['username'].get().strip()
        password = self.user_entries['password'].get()
        confirm = self.user_entries['confirm_password'].get()
        group = self.user_entries['group'].get()
        expiration = self.user_entries['expiration'].get().strip()
        simultaneous_use = self.user_entries['simultaneous_use'].get()
        session_timeout = self.user_entries['session_timeout'].get()
        idle_timeout = self.user_entries['idle_timeout'].get()
        
        # Валидация
        if not username or not password:
            messagebox.showerror("Ошибка", "Имя пользователя и пароль обязательны!")
            return
        
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают!")
            return
        
        if not group:
            group = "users"
        
        # Проверяем, не существует ли уже такой пользователь
        if self.db.user_exists(username):
            messagebox.showerror("Ошибка", f"Пользователь '{username}' уже существует!")
            return
        
        # Создаем объект пользователя
        user = User(
            username=username,
            password=password,
            group=group,
            expiration=expiration,
            simultaneous_use=int(simultaneous_use) if simultaneous_use else 1,
            session_timeout=int(session_timeout) if session_timeout else 3600,
            idle_timeout=int(idle_timeout) if idle_timeout else 0
        )
        
        # Собираем дополнительные атрибуты
        extra_attributes = []
        
        # Быстрые атрибуты
        for attr, var in self.quick_attr_vars.items():
            value = var.get()
            if value:
                extra_attributes.append(Attribute(attribute=attr, op='=', value=value))
        
        # Расширенные атрибуты из текстового поля
        attrs_text = self.attrs_text.get(1.0, tk.END).strip()
        if attrs_text and not attrs_text.startswith('#'):
            lines = attrs_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        attr, value = line.split('=', 1)
                        extra_attributes.append(Attribute(
                            attribute=attr.strip(),
                            op='=',
                            value=value.strip()
                        ))
        
        # Добавляем пользователя в БД
        if self.db.add_user(user, extra_attributes):
            self.logger.log(f"Добавлен пользователь: {username}")
            messagebox.showinfo("Успех", f"Пользователь '{username}' добавлен!")
            
            # Очищаем форму
            self._clear_form()
        else:
            messagebox.showerror("Ошибка", f"Не удалось добавить пользователя '{username}'")
    
    def _clear_form(self):
        """Очистка формы добавления пользователя"""
        for key, var in self.user_entries.items():
            if isinstance(var, tk.StringVar):
                if key != 'group':  # Не очищаем поле группы
                    var.set("")
        
        # Восстанавливаем значения по умолчанию
        self.user_entries['simultaneous_use'].set("1")
        self.user_entries['session_timeout'].set("3600")
        self.user_entries['idle_timeout'].set("0")
        
        # Сбрасываем быстрые атрибуты
        defaults = {
            "Framed-Protocol": "PPP",
            "Service-Type": "Framed-User",
            "Framed-Compression": "Van-Jacobson-TCP-IP",
            "WISPr-Bandwidth-Max-Up": "1024000",
            "WISPr-Bandwidth-Max-Down": "2048000",
        }
        
        for attr, default in defaults.items():
            if attr in self.quick_attr_vars:
                self.quick_attr_vars[attr].set(default)
        
        # Очищаем поле дополнительных атрибутов
        self.attrs_text.delete(1.0, tk.END)
        hint = """# Формат: Атрибут=Значение
# По одному атрибуту на строку
# Примеры:
# Mikrotik-Rate-Limit=512k/2M
# Framed-IP-Address=10.0.0.100
# Calling-Station-Id=00:11:22:33:44:55
# NAS-IP-Address=192.168.1.1
"""
        self.attrs_text.insert(1.0, hint)
    
    def update_groups(self):
        """Обновление списка групп"""
        self._load_groups()
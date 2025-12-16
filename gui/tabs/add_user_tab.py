#!/usr/bin/env python3
"""
Вкладка добавления нового пользователя
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import string
from datetime import datetime, timedelta
from tkcalendar import Calendar  # Импортируем Calendar вместо DateEntry
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
        self._load_groups()
    
    def _create_widgets(self):
        """Создание виджетов вкладки"""
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.LabelFrame(main_frame, text="Основные данные", padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        fields = [
            ("Имя пользователя*:", "username", False),
            ("Пароль*:", "password", True),
            ("Подтверждение пароля*:", "confirm_password", True),
            ("Группа:", "group", False),
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
                var = tk.StringVar()
                var.set("users")
                
                self.group_combobox = ttk.Combobox(row_frame, textvariable=var, 
                                                    values=["users"],
                                                    width=25, state="readonly")
                self.group_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.user_entries[field] = var
                
            elif field in ['simultaneous_use', 'session_timeout', 'idle_timeout']:
                var = tk.StringVar(value="1" if field == 'simultaneous_use' else "3600")
                spinbox = tk.Spinbox(row_frame, from_=1, to=99999, textvariable=var, width=25)
                spinbox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.user_entries[field] = var
            else:
                var = tk.StringVar()
                if is_password:
                    entry = tk.Entry(row_frame, textvariable=var, show="*", width=27)
                else:
                    entry = tk.Entry(row_frame, textvariable=var, width=27)
                entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.user_entries[field] = var
        
        # ПОЛЕ СРОКА ДЕЙСТВИЯ С КАЛЕНДАРЕМ
        self._create_expiration_field(left_frame)
        
        pass_gen_frame = ttk.Frame(left_frame)
        pass_gen_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(pass_gen_frame, text="Сгенерировать пароль", 
                  command=self._generate_password).pack(side=tk.LEFT, padx=5)
        
        self.pass_length_var = tk.StringVar(value="12")
        ttk.Label(pass_gen_frame, text="Длина:").pack(side=tk.LEFT, padx=(10, 2))
        ttk.Entry(pass_gen_frame, textvariable=self.pass_length_var, width=5).pack(side=tk.LEFT)
        
        right_frame = ttk.LabelFrame(main_frame, text="Дополнительные атрибуты", padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
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
        
        attrs_frame = ttk.LabelFrame(right_frame, text="Расширенные атрибуты", padding=10)
        attrs_frame.pack(fill=tk.BOTH, expand=True)
        
        self.attrs_text = scrolledtext.ScrolledText(attrs_frame, height=10, width=40)
        self.attrs_text.pack(fill=tk.BOTH, expand=True)
        
        hint = """# Формат: Атрибут=Значение
# По одному атрибуту на строку
# Примеры:
# Mikrotik-Rate-Limit=512k/2M
# Framed-IP-Address=10.0.0.100
# Calling-Station-Id=00:11:22:33:44:55
# NAS-IP-Address=192.168.1.1
"""
        self.attrs_text.insert(1.0, hint)
        
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
    
    def _create_expiration_field(self, parent_frame):
        """Создание поля для выбора даты с календарем"""
        date_frame = ttk.Frame(parent_frame)
        date_frame.pack(fill=tk.X, pady=6)
        
        ttk.Label(date_frame, text="Срок действия:", width=25).pack(side=tk.LEFT)
        
        # Обычное текстовое поле для даты
        self.expiration_var = tk.StringVar()
        self.expiration_entry = ttk.Entry(date_frame, textvariable=self.expiration_var, 
                                         width=23)
        self.expiration_entry.pack(side=tk.LEFT, padx=5)
        
        # Кнопка для открытия календаря
        ttk.Button(date_frame, text="📅", width=3,
                  command=self._open_calendar).pack(side=tk.LEFT, padx=2)
        
        # Кнопка "Очистить дату" - будет работать гарантированно
        ttk.Button(date_frame, text="×", width=3,
                  command=self._clear_expiration_date).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(date_frame, text="(оставьте пустым, если без ограничения)",
                 font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=5)
    
    def _open_calendar(self):
        """Открытие всплывающего окна с календарем"""
        # Создаем всплывающее окно
        calendar_window = tk.Toplevel(self.parent)
        calendar_window.title("Выберите дату")
        calendar_window.transient(self.parent)
        calendar_window.grab_set()
        calendar_window.geometry("300x250")
        
        # Создаем календарь в окне
        calendar = Calendar(
            calendar_window,
            selectmode='day',
            date_pattern='dd/mm/yyyy',
            mindate=datetime.now(),
            maxdate=datetime.now() + timedelta(days=365*5),
            showweeknumbers=False,
            firstweekday='monday'
        )
        calendar.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Кнопки
        btn_frame = ttk.Frame(calendar_window)
        btn_frame.pack(pady=5)
        
        def set_date():
            selected_date = calendar.get_date()  # Возвращает строку "dd/mm/yyyy"
            self.expiration_var.set(selected_date)
            calendar_window.destroy()
        
        ttk.Button(btn_frame, text="Выбрать", command=set_date).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=calendar_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Центрируем окно
        self._center_window(calendar_window)
        
        # Фокус на календаре
        calendar.focus_set()
    
    def _center_window(self, window):
        """Центрирование окна"""
        window.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        
        x = parent_x + (parent_width // 2) - (window_width // 2)
        y = parent_y + (parent_height // 2) - (window_height // 2)
        
        window.geometry(f"+{x}+{y}")
    
    def _clear_expiration_date(self):
        """Очистка поля даты - РАБОТАЕТ ГАРАНТИРОВАННО"""
        self.expiration_var.set("")
    
    def _load_groups(self):
        """Загрузка списка групп из БД"""
        try:
            if self.db.connection_status:
                groups = self.db.get_groups()
                if groups:
                    group_names = [group.name for group in groups if group.name and not group.name.startswith('_group_')]
                    
                    if group_names:
                        self.group_combobox['values'] = group_names
                        
                        current_value = self.user_entries.get('group', tk.StringVar()).get()
                        if current_value not in group_names:
                            self.user_entries['group'].set(group_names[0])
                else:
                    self.group_combobox['values'] = ["users"]
                    self.user_entries['group'].set("users")
            else:
                self.group_combobox['values'] = ["users"]
                self.user_entries['group'].set("users")
                
        except Exception as e:
            self.logger.log(f"Ошибка загрузки групп: {str(e)}")
            self.group_combobox['values'] = ["users"]
            self.user_entries['group'].set("users")
    
    def _generate_password(self):
        """Генерация случайного пароля"""
        try:
            length = int(self.pass_length_var.get())
            password = generate_password(length)
            
            self.user_entries['password'].set(password)
            self.user_entries['confirm_password'].set(password)
            
            self.logger.log(f"Сгенерирован пароль длиной {length} символов")
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная длина пароля")
    
    def _fill_test_data(self):
        """Заполнение формы тестовыми данными"""
        username = 'testuser_' + ''.join(random.choice(string.digits) for _ in range(4))
        password = 'TestPass' + ''.join(random.choice(string.digits) for _ in range(3))
        
        self.user_entries['username'].set(username)
        self.user_entries['password'].set(password)
        self.user_entries['confirm_password'].set(password)
        
        groups = self.group_combobox['values']
        if groups and len(groups) > 0:
            try:
                self.user_entries['group'].set(random.choice(groups))
            except:
                pass
        
        # Устанавливаем тестовую дату в формате dd/mm/yyyy
        test_date = datetime.now() + timedelta(days=random.randint(30, 365))
        formatted_date = test_date.strftime("%d/%m/%Y")
        self.expiration_var.set(formatted_date)
        
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
    
    def _convert_date_to_radius_format(self, date_str):
        """Преобразование даты из формата dd/mm/yyyy в формат FreeRADIUS"""
        if not date_str or not date_str.strip():
            return ""
        
        try:
            # Парсим дату из формата dd/mm/yyyy
            day, month_num, year = date_str.split('/')
            day = int(day)
            month_num = int(month_num)
            year = int(year)
            
            # Словарь для английских названий месяцев
            month_names = {
                1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
            }
            
            if month_num not in month_names:
                # Если формат другой, пытаемся распознать
                from datetime import datetime
                
                # Пробуем различные форматы
                formats_to_try = [
                    "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", 
                    "%d %b %Y", "%d %B %Y"
                ]
                
                for fmt in formats_to_try:
                    try:
                        date_obj = datetime.strptime(date_str.strip(), fmt)
                        day = date_obj.day
                        month_num = date_obj.month
                        year = date_obj.year
                        break
                    except ValueError:
                        continue
                
                if month_num not in month_names:
                    return date_str.strip()  # Возвращаем как есть
            
            return f"{day:02d} {month_names[month_num]} {year}"
            
        except (ValueError, AttributeError):
            # Если не удалось распарсить, возвращаем как есть
            return date_str.strip()
    
    def _add_user(self):
        """Добавление нового пользователя"""
        if not self.db.connection_status:
            messagebox.showerror("Ошибка", "Нет подключения к БД!")
            return
        
        username = self.user_entries['username'].get().strip()
        password = self.user_entries['password'].get()
        confirm = self.user_entries['confirm_password'].get()
        group = self.user_entries['group'].get()
        
        # Преобразуем дату в формат FreeRADIUS
        expiration_date = self.expiration_var.get().strip()
        expiration = self._convert_date_to_radius_format(expiration_date)
        
        simultaneous_use = self.user_entries['simultaneous_use'].get()
        session_timeout = self.user_entries['session_timeout'].get()
        idle_timeout = self.user_entries['idle_timeout'].get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Имя пользователя и пароль обязательны!")
            return
        
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают!")
            return
        
        if not group:
            group = "users"
        
        if self.db.user_exists(username):
            messagebox.showerror("Ошибка", f"Пользователь '{username}' уже существует!")
            return
        
        user = User(
            username=username,
            password=password,
            group=group,
            expiration=expiration,
            simultaneous_use=int(simultaneous_use) if simultaneous_use else 1,
            session_timeout=int(session_timeout) if session_timeout else 3600,
            idle_timeout=int(idle_timeout) if idle_timeout else 0
        )
        
        extra_attributes = []
        
        for attr, var in self.quick_attr_vars.items():
            value = var.get()
            if value:
                extra_attributes.append(Attribute(attribute=attr, op='=', value=value))
        
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
        
        if self.db.add_user(user, extra_attributes):
            messagebox.showinfo("Успех", f"Пользователь '{username}' добавлен!")
            
            self._clear_form()
        else:
            messagebox.showerror("Ошибка", f"Не удалось добавить пользователя '{username}'")
    
    def _clear_form(self):
        """Очистка формы добавления пользователя"""
        for key, var in self.user_entries.items():
            if isinstance(var, tk.StringVar):
                if key != 'group':
                    var.set("")
        
        # Очищаем поле даты
        self._clear_expiration_date()
        
        self.user_entries['simultaneous_use'].set("1")
        self.user_entries['session_timeout'].set("3600")
        self.user_entries['idle_timeout'].set("0")
        
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
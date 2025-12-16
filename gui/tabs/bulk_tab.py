#!/usr/bin/env python3
"""
Вкладка массовых операций
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import csv
import random
import string
from typing import List
from database import User, Attribute

class BulkTab:
    """Вкладка для массовых операций"""
    
    def __init__(self, parent, db_manager, logger):
        self.parent = parent
        self.db = db_manager
        self.logger = logger
        
        self.frame = ttk.Frame(parent)
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов вкладки"""
        # Фрейм для массового добавления
        bulk_frame = ttk.LabelFrame(self.frame, text="Массовое добавление пользователей", padding=15)
        bulk_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель с настройками
        settings_frame = ttk.Frame(bulk_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="Шаблон пароля:").pack(side=tk.LEFT, padx=(0, 5))
        self.bulk_pass_template = tk.StringVar(value="Pass{num}")
        ttk.Entry(settings_frame, textvariable=self.bulk_pass_template, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(settings_frame, text="Группа:").pack(side=tk.LEFT, padx=(10, 5))
        self.bulk_group = tk.StringVar(value="users")
        self.group_combo = ttk.Combobox(settings_frame, textvariable=self.bulk_group, 
                                  values=["users", "admin", "staff", "guest", "vip"],
                                  width=12)
        self.group_combo.pack(side=tk.LEFT, padx=5)
        
        # Текстовое поле для ввода
        input_frame = ttk.Frame(bulk_frame)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Label(input_frame, text="Введите данные (по одному пользователю на строку):").pack(anchor=tk.W, pady=(0, 5))
        
        self.bulk_text = scrolledtext.ScrolledText(input_frame, height=12, font=('Consolas', 10))
        self.bulk_text.pack(fill=tk.BOTH, expand=True)
        
        # Подсказка
        hint = """# Формат: username или username,additional_attributes
# Примеры:
# user1
# user2,Session-Timeout=7200,Idle-Timeout=1800
# user3,Framed-IP-Address=10.0.0.101
# user4
"""
        self.bulk_text.insert(1.0, hint)
        
        # Кнопки для массовых операций
        btn_frame = ttk.Frame(bulk_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Добавить всех", 
                  command=self._bulk_add_users,
                  style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Импорт из CSV", 
                  command=self._import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Экспорт в CSV", 
                  command=self._export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить", 
                  command=self._clear_bulk).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сгенерировать пользователей", 
                  command=self._generate_users).pack(side=tk.LEFT, padx=5)
        
        # Фрейм для массовых действий
        actions_frame = ttk.LabelFrame(self.frame, text="Массовые действия", padding=15)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(actions_frame, text="Блокировать выбранных", 
                  command=self._bulk_block).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Разблокировать выбранных", 
                  command=self._bulk_unblock).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Изменить пароль выбранных", 
                  command=self._bulk_change_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Удалить выбранных", 
                  command=self._bulk_delete, 
                  style='Danger.TButton').pack(side=tk.LEFT, padx=5)
    
    def update_groups(self):
        """Обновление списка групп в комбобоксе"""
        if self.db.connection_status:
            try:
                groups = self.db.get_groups()
                group_names = [group.name for group in groups]
                
                if group_names:
                    self.group_combo['values'] = group_names
                    if not self.bulk_group.get():
                        self.bulk_group.set(group_names[0])
            except Exception as e:
                self.logger.log(f"Ошибка обновления списка групп: {str(e)}")
    
    def _generate_users(self):
        """Генерация списка пользователей"""
        try:
            count = 10
            if '{num}' in self.bulk_pass_template.get():
                # Пытаемся извлечь количество из шаблона
                try:
                    count = int(self.bulk_pass_template.get().split('{num}')[0].replace('Pass', ''))
                except:
                    count = 10
            
            bulk_text = ""
            for i in range(1, count + 1):
                username = f"user{i:03d}"
                bulk_text += f"{username}\n"
            
            self.bulk_text.delete(1.0, tk.END)
            self.bulk_text.insert(1.0, bulk_text)
            
            self.logger.log(f"Сгенерировано {count} тестовых пользователей")
            
        except Exception as e:
            self.logger.log(f"Ошибка генерации пользователей: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось сгенерировать пользователей:\n{str(e)}")
    
    def _clear_bulk(self):
        """Очистка поля массового добавления"""
        self.bulk_text.delete(1.0, tk.END)
    
    def _bulk_add_users(self):
        """Массовое добавление пользователей"""
        if not self.db.connection_status:
            messagebox.showerror("Ошибка", "Нет подключения к БД!")
            return
        
        text = self.bulk_text.get(1.0, tk.END).strip()
        if not text or text.startswith('#'):
            messagebox.showwarning("Внимание", "Нет данных для добавления!")
            return
        
        lines = text.split('\n')
        users = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#'):
                continue
            
            # Разбираем строку
            parts = line.split(',', 1)
            username = parts[0].strip()
            
            if not username:
                continue
            
            # Генерируем пароль по шаблону
            password_template = self.bulk_pass_template.get()
            if '{num}' in password_template:
                password = password_template.replace('{num}', str(i))
            else:
                password = password_template + str(i)
            
            # Создаем объект пользователя
            user = User(
                username=username,
                password=password,
                group=self.bulk_group.get()
            )
            
            # Дополнительные атрибуты, если указаны
            extra_attributes = []
            if len(parts) > 1:
                attrs = parts[1].split(',')
                for attr_str in attrs:
                    attr_str = attr_str.strip()
                    if '=' in attr_str:
                        attr_name, attr_value = attr_str.split('=', 1)
                        extra_attributes.append(Attribute(
                            attribute=attr_name.strip(),
                            op='=',
                            value=attr_value.strip()
                        ))
            
            users.append((user, extra_attributes))
        
        if not users:
            messagebox.showwarning("Внимание", "Нет данных для добавления!")
            return
        
        # Подтверждение
        if not messagebox.askyesno("Подтверждение", 
            f"Добавить {len(users)} пользователей?"):
            return
        
        added = 0
        errors = []
        
        for user, extra_attrs in users:
            try:
                if self.db.add_user(user, extra_attrs):
                    added += 1
                else:
                    errors.append(f"{user.username}: ошибка добавления")
            except Exception as e:
                errors.append(f"{user.username}: {str(e)}")
        
        if errors:
            error_msg = "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n... и еще {len(errors) - 10} ошибок"
            
            self.logger.log(f"Массовое добавление: {len(errors)} ошибок")
            messagebox.showerror("Ошибки при добавлении", error_msg)
        
        if added > 0:
            self.logger.log(f"Массовое добавление: {added} пользователей")
            messagebox.showinfo("Успех", f"Добавлено пользователей: {added}")
            self._clear_bulk()
    
    def _import_csv(self):
        """Импорт пользователей из CSV файла"""
        if not self.db.connection_status:
            messagebox.showerror("Ошибка", "Нет подключения к БД!")
            return
        
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Пропускаем заголовок, если есть
                try:
                    header = next(reader)
                except StopIteration:
                    header = []
                
                users = []
                errors = []
                
                for i, row in enumerate(reader, 2 if header else 1):
                    if len(row) < 2:
                        errors.append(f"Строка {i}: недостаточно данных")
                        continue
                    
                    username = row[0].strip()
                    password = row[1].strip()
                    group = row[2].strip() if len(row) > 2 else self.bulk_group.get()
                    
                    if not username or not password:
                        errors.append(f"Строка {i}: отсутствует имя пользователя или пароль")
                        continue
                    
                    user = User(
                        username=username,
                        password=password,
                        group=group
                    )
                    
                    # Дополнительные поля
                    if len(row) > 3 and row[3].strip():
                        user.expiration = row[3].strip()
                    
                    users.append(user)
                
                if errors:
                    error_msg = "\n".join(errors[:10])
                    if len(errors) > 10:
                        error_msg += f"\n... и еще {len(errors) - 10} ошибок"
                    
                    self.logger.log(f"Импорт CSV: {len(errors)} ошибок")
                    messagebox.showerror("Ошибки импорта", error_msg)
                    return
                
                if not users:
                    messagebox.showwarning("Внимание", "Нет данных для импорта!")
                    return
                
                # Подтверждение
                if not messagebox.askyesno("Подтверждение", 
                    f"Импортировать {len(users)} пользователей?"):
                    return
                
                added = 0
                import_errors = []
                
                for user in users:
                    try:
                        if self.db.add_user(user):
                            added += 1
                        else:
                            import_errors.append(f"{user.username}: ошибка добавления")
                    except Exception as e:
                        import_errors.append(f"{user.username}: {str(e)}")
                
                if import_errors:
                    error_msg = "\n".join(import_errors[:10])
                    if len(import_errors) > 10:
                        error_msg += f"\n... и еще {len(import_errors) - 10} ошибок"
                    
                    self.logger.log(f"Импорт CSV: {len(import_errors)} ошибок")
                    messagebox.showerror("Ошибки импорта", error_msg)
                
                if added > 0:
                    self.logger.log(f"Импорт CSV: {added} пользователей")
                    messagebox.showinfo("Успех", f"Импортировано пользователей: {added}")
        
        except Exception as e:
            self.logger.log(f"Ошибка импорта CSV: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось импортировать файл:\n{str(e)}")
    
    def _export_csv(self):
        """Экспорт пользователей в CSV файл"""
        if not self.db.connection_status:
            messagebox.showerror("Ошибка", "Нет подключения к БД!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить как CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        count = self.db.export_users_to_csv(file_path)
        if count > 0:
            self.logger.log(f"Экспорт CSV: {count} пользователей")
            messagebox.showinfo("Успех", f"Экспортировано пользователей: {count}\nФайл: {file_path}")
        else:
            messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
    
    def _bulk_block(self):
        """Массовая блокировка выбранных пользователей"""
        self._bulk_toggle_block(True)
    
    def _bulk_unblock(self):
        """Массовая разблокировка выбранных пользователей"""
        self._bulk_toggle_block(False)
    
    def _bulk_toggle_block(self, block: bool):
        """Массовая блокировка/разблокировка пользователей"""
        # Этот метод должен вызываться из главного окна с передачей списка пользователей
        # В текущей реализации он требует интеграции с вкладкой пользователей
        messagebox.showinfo("Информация", 
            "Эта функция должна быть вызвана из вкладки 'Пользователи'.\n"
            "Выберите пользователей в таблице пользователей и используйте контекстное меню.")
    
    def _bulk_change_password(self):
        """Массовое изменение пароля выбранных пользователей"""
        # Этот метод также требует интеграции с вкладкой пользователей
        messagebox.showinfo("Информация", 
            "Эта функция должна быть вызвана из вкладки 'Пользователи'.\n"
            "Выберите пользователей в таблице пользователей и используйте контекстное меню.")
    
    def _bulk_delete(self):
        """Массовое удаление выбранных пользователей"""
        # Этот метод также требует интеграции с вкладкой пользователей
        messagebox.showinfo("Информация", 
            "Эта функция должна быть вызвана из вкладки 'Пользователи'.\n"
            "Выберите пользователей в таблице пользователей и используйте контекстное меню.")
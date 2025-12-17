#!/usr/bin/env python3
"""
Вкладка управления пользователями
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List
from database import User, Attribute
from gui.dialogs import PasswordDialog, AttributeDialog

class UsersTab:
    """Вкладка для управления пользователями"""
    
    def __init__(self, parent, db_manager, logger, status_bar):
        self.parent = parent
        self.db = db_manager
        self.logger = logger
        self.status_bar = status_bar
        self.selected_user = None
        
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self._create_context_menu()
    
    def _create_widgets(self):
        """Создание виджетов вкладки"""
        # Основной фрейм с двумя колонками
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая колонка - список пользователей
        left_frame = ttk.LabelFrame(main_frame, text="Список пользователей", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Панель поиска и фильтров
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Поиск по имени
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_row, text="Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', self._search_users)
        
        ttk.Button(search_row, text="Сбросить", 
                  command=self._clear_search).pack(side=tk.LEFT, padx=5)
        
        # Фильтры
        filter_row = ttk.Frame(search_frame)
        filter_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_row, text="Статус:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_filter = tk.StringVar(value="Все")
        status_combo = ttk.Combobox(filter_row, textvariable=self.status_filter, 
                                   values=["Все", "Активен", "Заблокирован"],
                                   width=12, state="readonly")
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind('<<ComboboxSelected>>', self._apply_filters)
        
        ttk.Label(filter_row, text="Группа:").pack(side=tk.LEFT, padx=(10, 5))
        self.group_filter = tk.StringVar(value="Все")
        self.group_filter_widget = ttk.Combobox(filter_row, textvariable=self.group_filter, 
                                                values=["Все"],
                                                width=12, state="readonly")
        self.group_filter_widget.pack(side=tk.LEFT, padx=5)
        self.group_filter_widget.bind('<<ComboboxSelected>>', self._apply_filters)
        
        # Кнопки управления
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Добавить", 
                  command=self._add_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", 
                  command=self.load_users).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Импорт CSV", 
                  command=self._import_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Экспорт CSV", 
                  command=self._export_all_users).pack(side=tk.LEFT, padx=2)
        
        # Таблица пользователей
        table_frame = ttk.Frame(left_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем Treeview с колонками
        columns = ('username', 'group', 'status', 'last_login')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Настраиваем заголовки
        self.tree.heading('username', text='Имя пользователя')
        self.tree.heading('group', text='Группа')
        self.tree.heading('status', text='Статус')
        self.tree.heading('last_login', text='Последний вход')
        
        # Настраиваем ширину колонок
        self.tree.column('username', width=150, minwidth=150)
        self.tree.column('group', width=100, minwidth=80)
        self.tree.column('status', width=100, minwidth=80)
        self.tree.column('last_login', width=120, minwidth=100)
        
        # Теги для цветовой маркировки
        self.tree.tag_configure('blocked', background='#ffebee')
        self.tree.tag_configure('active', background='#e8f5e9')
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Привязка событий
        self.tree.bind('<<TreeviewSelect>>', self._on_user_selected)
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # Панель статистики
        stats_frame = ttk.Frame(left_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Всего пользователей: 0")
        self.stats_label.pack(side=tk.LEFT)
        
        # Правая колонка - атрибуты выбранного пользователя
        right_frame = ttk.LabelFrame(main_frame, text="Атрибуты пользователя", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок с именем выбранного пользователя
        self.selected_user_label = ttk.Label(
            right_frame, 
            text="Выберите пользователя для просмотра атрибутов",
            font=('Arial', 10, 'bold'),
            foreground='#666666'
        )
        self.selected_user_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Вкладки для типов атрибутов
        self.attr_notebook = ttk.Notebook(right_frame)
        self.attr_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка Check атрибутов
        check_frame = ttk.Frame(self.attr_notebook)
        self.attr_notebook.add(check_frame, text="Check атрибуты")
        
        # Таблица Check атрибутов
        check_columns = ('attribute', 'op', 'value')
        self.check_tree = ttk.Treeview(
            check_frame, 
            columns=check_columns, 
            show='headings',
            height=8,
            selectmode='browse'
        )
        
        self.check_tree.heading('attribute', text='Атрибут')
        self.check_tree.heading('op', text='Оператор')
        self.check_tree.heading('value', text='Значение')
        
        self.check_tree.column('attribute', width=120)
        self.check_tree.column('op', width=60)
        self.check_tree.column('value', width=150)
        
        check_vsb = ttk.Scrollbar(check_frame, orient="vertical", command=self.check_tree.yview)
        check_hsb = ttk.Scrollbar(check_frame, orient="horizontal", command=self.check_tree.xview)
        self.check_tree.configure(yscrollcommand=check_vsb.set, xscrollcommand=check_hsb.set)
        
        self.check_tree.grid(row=0, column=0, sticky='nsew')
        check_vsb.grid(row=0, column=1, sticky='ns')
        check_hsb.grid(row=1, column=0, sticky='ew')
        
        check_frame.grid_columnconfigure(0, weight=1)
        check_frame.grid_rowconfigure(0, weight=1)
        
        # Панель управления Check атрибутами
        check_btn_frame = ttk.Frame(check_frame)
        check_btn_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5, 0))
        
        ttk.Button(check_btn_frame, text="Добавить", 
                  command=self._add_check_attr, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(check_btn_frame, text="Изменить", 
                  command=self._edit_check_attr, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(check_btn_frame, text="Удалить", 
                  command=self._delete_check_attr, width=12).pack(side=tk.LEFT, padx=2)
        
        # Вкладка Reply атрибутов
        reply_frame = ttk.Frame(self.attr_notebook)
        self.attr_notebook.add(reply_frame, text="Reply атрибуты")
        
        # Таблица Reply атрибутов
        reply_columns = ('attribute', 'op', 'value')
        self.reply_tree = ttk.Treeview(
            reply_frame, 
            columns=reply_columns, 
            show='headings',
            height=8,
            selectmode='browse'
        )
        
        self.reply_tree.heading('attribute', text='Атрибут')
        self.reply_tree.heading('op', text='Оператор')
        self.reply_tree.heading('value', text='Значение')
        
        self.reply_tree.column('attribute', width=120)
        self.reply_tree.column('op', width=60)
        self.reply_tree.column('value', width=150)
        
        reply_vsb = ttk.Scrollbar(reply_frame, orient="vertical", command=self.reply_tree.yview)
        reply_hsb = ttk.Scrollbar(reply_frame, orient="horizontal", command=self.reply_tree.xview)
        self.reply_tree.configure(yscrollcommand=reply_vsb.set, xscrollcommand=reply_hsb.set)
        
        self.reply_tree.grid(row=0, column=0, sticky='nsew')
        reply_vsb.grid(row=0, column=1, sticky='ns')
        reply_hsb.grid(row=1, column=0, sticky='ew')
        
        reply_frame.grid_columnconfigure(0, weight=1)
        reply_frame.grid_rowconfigure(0, weight=1)
        
        # Панель управления Reply атрибутами
        reply_btn_frame = ttk.Frame(reply_frame)
        reply_btn_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5, 0))
        
        ttk.Button(reply_btn_frame, text="Добавить", 
                  command=self._add_reply_attr, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(reply_btn_frame, text="Изменить", 
                  command=self._edit_reply_attr, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(reply_btn_frame, text="Удалить", 
                  command=self._delete_reply_attr, width=12).pack(side=tk.LEFT, padx=2)
        
        # Статистика атрибутов
        self.attr_stats_label = ttk.Label(right_frame, text="Check: 0 | Reply: 0")
        self.attr_stats_label.pack(side=tk.BOTTOM, anchor=tk.W, pady=(10, 0))
    
    def _create_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.parent, tearoff=0, font=('Arial', 10))
        
        menu_items = [
            ("Изменить пароль", self._change_password),
            ("Копировать имя", self._copy_username),
            ("Блокировать", self._block_user),
            ("Разблокировать", self._unblock_user),
            ("Удалить", self._delete_user),
            ("Экспортировать", self._export_selected),
        ]
        
        for text, command in menu_items:
            self.context_menu.add_command(label=text, command=command)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Обновить список", command=self.load_users)
    
    def load_users(self):
        """Загрузка списка пользователей из БД"""
        if not self.db.connection_status:
            self.logger.log("Нет подключения к БД. Подключитесь сначала.")
            return
        
        try:
            # Очищаем текущий список
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Получаем пользователей из БД
            users = self.db.get_users()
            
            # Заполняем таблицу
            for user in users:
                # Выбираем тег в зависимости от статуса
                tag = 'blocked' if user.status == 'Заблокирован' else 'active'
                
                self.tree.insert('', tk.END, values=(
                    user.username,
                    user.group,
                    user.status,
                    user.last_login
                ), tags=(tag,))
            
            # Обновляем статистику
            self.stats_label.config(text=f"Всего пользователей: {len(users)}")
            self.logger.log(f"Загружено пользователей: {len(users)}")
            
            # Обновляем список групп в фильтрах
            self._update_group_filters()
            
            # Очищаем атрибуты
            self._clear_attributes()
            
        except Exception as e:
            self.logger.log(f"Ошибка загрузки пользователей: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить пользователей:\n{str(e)}")
    
    def clear_users(self):
        """Очистка списка пользователей"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.stats_label.config(text="Всего пользователей: 0")
        self._clear_attributes()
    
    def _on_user_selected(self, event=None):
        """Обработка выбора пользователя"""
        selected = self.tree.selection()
        if not selected:
            self._clear_attributes()
            return
        
        username = self.tree.item(selected[0])['values'][0]
        self.selected_user = username
        self.selected_user_label.config(
            text=f"Атрибуты пользователя: {username}",
            foreground='#333333'
        )
        self._load_user_attributes(username)
    
    def _load_user_attributes(self, username):
        """Загрузка атрибутов выбранного пользователя"""
        try:
            # Обновляем заголовок
            self.selected_user_label.config(
                text=f"Атрибуты пользователя: {username}",
                foreground='#333333'
            )
            
            # Очищаем таблицы атрибутов
            self._clear_attributes()
            
            # Получаем атрибуты из БД
            check_attrs, reply_attrs = self.db.get_user_attributes(username)
            
            # Заполняем Check атрибуты
            for attr in check_attrs:
                self.check_tree.insert('', tk.END, values=(
                    attr.attribute,
                    attr.op,
                    attr.value
                ))
            
            # Заполняем Reply атрибуты
            for attr in reply_attrs:
                self.reply_tree.insert('', tk.END, values=(
                    attr.attribute,
                    attr.op,
                    attr.value
                ))
            
            # Обновляем статистику
            self.attr_stats_label.config(text=f"Check: {len(check_attrs)} | Reply: {len(reply_attrs)}")
            
        except Exception as e:
            self.logger.log(f"Ошибка загрузки атрибутов пользователя: {str(e)}")
            self.selected_user_label.config(
                text="Ошибка загрузки атрибутов",
                foreground='red'
            )
    
    def _clear_attributes(self):
        """Очистка таблиц атрибутов"""
        for item in self.check_tree.get_children():
            self.check_tree.delete(item)
        
        for item in self.reply_tree.get_children():
            self.reply_tree.delete(item)
        
        self.selected_user_label.config(
            text="Выберите пользователя для просмотра атрибутов",
            foreground='#666666'
        )
        self.attr_stats_label.config(text="Check: 0 | Reply: 0")
        self.selected_user = None
    
    def _add_check_attr(self):
        """Добавление Check атрибута пользователя"""
        # Исправлено: проверяем выбранного пользователя
        selected_users = self.tree.selection()
        if not selected_users:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected_users[0])['values'][0]
        self.selected_user = username  # Обновляем выбранного пользователя
        self._load_user_attributes(username)  # Загружаем атрибуты
        
        dialog = AttributeDialog(self.parent, "Добавить Check атрибут", username, 'check')
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            attr = Attribute(attribute=attribute, op=op, value=value)
            
            if self.db.add_user_attribute(username, attr, 'check'):
                self.logger.log(f"Добавлен Check атрибут '{attribute}' для пользователя '{username}'")
                self._load_user_attributes(username)
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить атрибут '{attribute}'")
    
    def _add_reply_attr(self):
        """Добавление Reply атрибута пользователя"""
        # Исправлено: проверяем выбранного пользователя
        selected_users = self.tree.selection()
        if not selected_users:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected_users[0])['values'][0]
        self.selected_user = username  # Обновляем выбранного пользователя
        self._load_user_attributes(username)  # Загружаем атрибуты
        
        dialog = AttributeDialog(self.parent, "Добавить Reply атрибут", username, 'reply')
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            attr = Attribute(attribute=attribute, op=op, value=value)
            
            if self.db.add_user_attribute(username, attr, 'reply'):
                self.logger.log(f"Добавлен Reply атрибут '{attribute}' для пользователя '{username}'")
                self._load_user_attributes(username)
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить атрибут '{attribute}'")
    
    def _edit_check_attr(self):
        """Редактирование Check атрибута пользователя"""
        selected_attr = self.check_tree.selection()
        if not selected_attr:
            messagebox.showwarning("Внимание", "Выберите атрибут для редактирования!")
            return
        
        # Исправлено: проверяем выбранного пользователя
        selected_users = self.tree.selection()
        if not selected_users:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected_users[0])['values'][0]
        self.selected_user = username
        
        # Получаем текущие значения
        values = self.check_tree.item(selected_attr[0])['values']
        
        dialog = AttributeDialog(
            self.parent, 
            "Изменить Check атрибут", 
            username, 
            'check',
            (values[0], values[1], values[2])
        )
        
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            old_attr = Attribute(attribute=values[0], op=values[1], value=values[2])
            new_attr = Attribute(attribute=attribute, op=op, value=value)
            
            # Исправлено: используем правильный метод
            if self.db.delete_user_attribute(username, old_attr, 'check'):
                if self.db.add_user_attribute(username, new_attr, 'check'):
                    self.logger.log(f"Изменен Check атрибут для пользователя '{username}'")
                    self._load_user_attributes(username)
                else:
                    # Пытаемся восстановить старый атрибут
                    self.db.add_user_attribute(username, old_attr, 'check')
                    messagebox.showerror("Ошибка", f"Не удалось изменить атрибут '{attribute}'")
            else:
                messagebox.showerror("Ошибка", f"Не удалось найти старый атрибут '{values[0]}'")
    
    def _edit_reply_attr(self):
        """Редактирование Reply атрибута пользователя"""
        selected_attr = self.reply_tree.selection()
        if not selected_attr:
            messagebox.showwarning("Внимание", "Выберите атрибут для редактирования!")
            return
        
        # Исправлено: проверяем выбранного пользователя
        selected_users = self.tree.selection()
        if not selected_users:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected_users[0])['values'][0]
        self.selected_user = username
        
        # Получаем текущие значения
        values = self.reply_tree.item(selected_attr[0])['values']
        
        dialog = AttributeDialog(
            self.parent, 
            "Изменить Reply атрибут", 
            username, 
            'reply',
            (values[0], values[1], values[2])
        )
        
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            old_attr = Attribute(attribute=values[0], op=values[1], value=values[2])
            new_attr = Attribute(attribute=attribute, op=op, value=value)
            
            # Исправлено: используем правильный метод
            if self.db.delete_user_attribute(username, old_attr, 'reply'):
                if self.db.add_user_attribute(username, new_attr, 'reply'):
                    self.logger.log(f"Изменен Reply атрибут для пользователя '{username}'")
                    self._load_user_attributes(username)
                else:
                    # Пытаемся восстановить старый атрибут
                    self.db.add_user_attribute(username, old_attr, 'reply')
                    messagebox.showerror("Ошибка", f"Не удалось изменить атрибут '{attribute}'")
            else:
                messagebox.showerror("Ошибка", f"Не удалось найти старый атрибут '{values[0]}'")
    
    def _delete_check_attr(self):
        """Удаление Check атрибута пользователя"""
        selected_attr = self.check_tree.selection()
        if not selected_attr:
            messagebox.showwarning("Внимание", "Выберите атрибут для удаления!")
            return
        
        # Исправлено: проверяем выбранного пользователя
        selected_users = self.tree.selection()
        if not selected_users:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected_users[0])['values'][0]
        self.selected_user = username
        
        values = self.check_tree.item(selected_attr[0])['values']
        attr = Attribute(attribute=values[0], op=values[1], value=values[2])
        
        if not messagebox.askyesno("Подтверждение", 
            f"Удалить Check атрибут '{values[0]}' для пользователя '{username}'?"):
            return
        
        if self.db.delete_user_attribute(username, attr, 'check'):
            self.logger.log(f"Удален Check атрибут '{values[0]}' для пользователя '{username}'")
            self._load_user_attributes(username)
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить атрибут '{values[0]}'")
    
    def _delete_reply_attr(self):
        """Удаление Reply атрибута пользователя"""
        selected_attr = self.reply_tree.selection()
        if not selected_attr:
            messagebox.showwarning("Внимание", "Выберите атрибут для удаления!")
            return
        
        # Исправлено: проверяем выбранного пользователя
        selected_users = self.tree.selection()
        if not selected_users:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected_users[0])['values'][0]
        self.selected_user = username
        
        values = self.reply_tree.item(selected_attr[0])['values']
        attr = Attribute(attribute=values[0], op=values[1], value=values[2])
        
        if not messagebox.askyesno("Подтверждение", 
            f"Удалить Reply атрибут '{values[0]}' для пользователя '{username}'?"):
            return
        
        if self.db.delete_user_attribute(username, attr, 'reply'):
            self.logger.log(f"Удален Reply атрибут '{values[0]}' для пользователя '{username}'")
            self._load_user_attributes(username)
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить атрибут '{values[0]}'")
    
    def _search_users(self, event=None):
        """Поиск пользователей по имени"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            # Если поиск пустой, показываем всех
            for item in self.tree.get_children():
                self.tree.selection_remove(item)
            return
        
        # Ищем совпадения
        found_items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            username = values[0].lower() if values[0] else ''
            
            if search_term in username:
                found_items.append(item)
        
        # Выделяем найденные элементы
        self.tree.selection_set(found_items)
        
        if found_items:
            self.tree.see(found_items[0])
            self.stats_label.config(text=f"Найдено пользователей: {len(found_items)}")
    
    def _clear_search(self):
        """Очистка поиска"""
        self.search_var.set("")
        for item in self.tree.get_children():
            self.tree.selection_remove(item)
        self.load_users()  # Перезагружаем полный список
    
    def _apply_filters(self, event=None):
        """Применение фильтров"""
        status_filter = self.status_filter.get()
        group_filter = self.group_filter.get()
        
        # Показываем/скрываем элементы в зависимости от фильтров
        visible_count = 0
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            status = values[2] if len(values) > 2 else ''
            group = values[1] if len(values) > 1 else ''
            
            # Проверяем фильтры
            status_match = (status_filter == "Все") or (status == status_filter)
            group_match = (group_filter == "Все") or (group == group_filter)
            
            if status_match and group_match:
                self.tree.item(item, open=True)
                visible_count += 1
            else:
                self.tree.item(item, open=False)
        
        self.stats_label.config(text=f"Отфильтровано пользователей: {visible_count}")
    
    def _update_group_filters(self):
        """Обновление списка групп в фильтрах"""
        if not self.db.connection_status:
            return
        
        try:
            groups = self.db.get_groups()
            group_names = [group.name for group in groups]
            
            # Обновляем комбобокс фильтра
            self.group_filter.set("Все")
            if self.group_filter_widget is not None:
                self.group_filter_widget['values'] = ["Все"] + group_names
            
        except Exception as e:
            self.logger.log(f"Ошибка обновления фильтров групп: {str(e)}")
    
    def _show_context_menu(self, event):
        """Показать контекстное меню"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        else:
            # Если клик не на элементе, показываем меню для таблицы
            table_menu = tk.Menu(self.parent, tearoff=0)
            table_menu.add_command(label="Обновить список", command=self.load_users)
            table_menu.add_command(label="Экспортировать всех", command=self._export_all_users)
            table_menu.post(event.x_root, event.y_root)
    
    def _change_password(self):
        """Изменение пароля выбранного пользователя"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected[0])['values'][0]
        
        # Создаем диалог для ввода нового пароля
        dialog = PasswordDialog(self.parent, "Изменить пароль", username)
        new_password = dialog.show()
        
        if new_password:
            if self.db.update_user_password(username, new_password):
                self.logger.log(f"Изменен пароль для: {username}")
                messagebox.showinfo("Успех", f"Пароль для пользователя '{username}' изменен!")
                self.load_users()
            else:
                messagebox.showerror("Ошибка", f"Не удалось изменить пароль для '{username}'")
    
    def _copy_username(self):
        """Копирование имени пользователя в буфер обмена"""
        selected = self.tree.selection()
        if not selected:
            return
        
        username = self.tree.item(selected[0])['values'][0]
        self.parent.clipboard_clear()
        self.parent.clipboard_append(username)
        self.logger.log(f"Скопировано имя: {username}")
        
        # Временное уведомление
        self.status_bar.set_status(f"Скопировано: {username}")
        self.parent.after(2000, lambda: self.status_bar.set_status("Готово"))
    
    def _add_user(self):
        """Добавление нового пользователя - переключение на вкладку добавления"""
        # Находим notebook родителя и переключаемся на вкладку добавления
        parent = self.frame.winfo_parent()
        # Вам нужно получить доступ к главному окну для переключения вкладок
        # Это упрощенная реализация - может потребоваться адаптация
        messagebox.showinfo("Информация", 
            "Для добавления пользователя перейдите на вкладку 'Добавить пользователя'")
    
    def _block_user(self):
        """Блокировка выбранного пользователя"""
        self._toggle_user_block(True)
    
    def _unblock_user(self):
        """Разблокировка выбранного пользователя"""
        self._toggle_user_block(False)
    
    def _toggle_user_block(self, block=True):
        """Блокировка/разблокировка пользователя"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected[0])['values'][0]
        action = "заблокирован" if block else "разблокирован"
        
        if self.db.block_user(username, block):
            self.logger.log(f"Пользователь {username} {action}")
            messagebox.showinfo("Успех", f"Пользователь '{username}' {action}!")
            self.load_users()
        else:
            messagebox.showerror("Ошибка", f"Не удалось {action} пользователя '{username}'")
    
    def _delete_user(self):
        """Удаление выбранного пользователя"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите пользователя!")
            return
        
        username = self.tree.item(selected[0])['values'][0]
        
        if not messagebox.askyesno("Подтверждение", 
            f"Удалить пользователя '{username}'?\nЭто действие нельзя отменить!"):
            return
        
        if self.db.delete_user(username):
            self.logger.log(f"Удален пользователь: {username}")
            messagebox.showinfo("Успех", f"Пользователь '{username}' удален!")
            self.load_users()
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить пользователя '{username}'")
    
    def _import_csv(self):
        """Импорт пользователей из CSV"""
        # Перенаправляем на вкладку массовых операций
        messagebox.showinfo("Информация", 
            "Для импорта CSV перейдите на вкладку 'Массовые операции'")
    
    def _export_selected(self):
        """Экспорт выбранных пользователей"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите пользователей!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Экспорт выбранных пользователей",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Username,Group,Status,Last Login\n")
                
                for item in selected:
                    values = self.tree.item(item)['values']
                    f.write(','.join([f'"{v}"' for v in values]) + '\n')
            
            self.logger.log(f"Экспорт выбранных: {len(selected)} пользователей")
            messagebox.showinfo("Успех", f"Экспортировано пользователей: {len(selected)}")
            
        except Exception as e:
            self.logger.log(f"Ошибка экспорта: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные:\n{str(e)}")
    
    def _export_all_users(self):
        """Экспорт всех пользователей"""
        if not self.db.connection_status:
            messagebox.showerror("Ошибка", "Нет подключения к БД!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Экспорт всех пользователей",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        count = self.db.export_users_to_csv(file_path)
        if count > 0:
            messagebox.showinfo("Успех", f"Экспортировано пользователей: {count}\nФайл: {file_path}")
        else:
            messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
    
    def get_selected_users(self) -> List[str]:
        """Получение списка выбранных пользователей"""
        selected = self.tree.selection()
        return [self.tree.item(item)['values'][0] for item in selected]
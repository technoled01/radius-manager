#!/usr/bin/env python3
"""
Вкладка управления пользователями
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List
from database import User
from gui.dialogs import PasswordDialog

class UsersTab:
    """Вкладка для управления пользователями"""
    
    def __init__(self, parent, db_manager, logger, status_bar):
        self.parent = parent
        self.db = db_manager
        self.logger = logger
        self.status_bar = status_bar
        
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self._create_context_menu()
    
    def _create_widgets(self):
        """Создание виджетов вкладки"""
        # Панель поиска и фильтров
        search_frame = ttk.LabelFrame(self.frame, text="Поиск и фильтры", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Поиск по имени
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_row, text="Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=40)
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
                                   width=15, state="readonly")
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind('<<ComboboxSelected>>', self._apply_filters)
        
        ttk.Label(filter_row, text="Группа:").pack(side=tk.LEFT, padx=(20, 5))
        self.group_filter = tk.StringVar(value="Все")
        self.group_filter_widget = ttk.Combobox(filter_row, textvariable=self.group_filter, 
                                  values=["Все"],
                                  width=15, state="readonly")
        self.group_filter_widget.pack(side=tk.LEFT, padx=5)
        self.group_filter_widget.bind('<<ComboboxSelected>>', self._apply_filters)
        
        # Таблица пользователей
        table_frame = ttk.LabelFrame(self.frame, text="Список пользователей", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Создаем Treeview с колонками
        columns = ('username', 'group', 'status', 'last_login')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Настраиваем заголовки
        self.tree.heading('username', text='Имя пользователя')
        self.tree.heading('group', text='Группа')
        self.tree.heading('status', text='Статус')
        self.tree.heading('last_login', text='Последний вход')
        
        # Настраиваем ширину колонок
        self.tree.column('username', width=200, minwidth=150)
        self.tree.column('group', width=120, minwidth=100)
        self.tree.column('status', width=120, minwidth=100)
        self.tree.column('last_login', width=150, minwidth=120)
        
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
        
        # Привязка правой кнопки мыши
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # Панель статистики
        self.stats_frame = ttk.Frame(self.frame)
        self.stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.stats_label = ttk.Label(self.stats_frame, text="Всего пользователей: 0")
        self.stats_label.pack(side=tk.LEFT)
    
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
            
        except Exception as e:
            self.logger.log(f"Ошибка загрузки пользователей: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить пользователей:\n{str(e)}")
    
    def clear_users(self):
        """Очистка списка пользователей"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.stats_label.config(text="Всего пользователей: 0")
    
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
            messagebox.showinfo("Успех", f"Пользователь '{username}' удален!")
            self.load_users()
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить пользователя '{username}'")
    
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
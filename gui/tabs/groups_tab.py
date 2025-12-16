#!/usr/bin/env python3
"""
Вкладка управления группами
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database import Group, Attribute
from gui.dialogs import GroupDialog, AttributeDialog

class GroupsTab:
    """Вкладка для управления группами"""
    
    def __init__(self, parent, db_manager, logger):
        self.parent = parent
        self.db = db_manager
        self.logger = logger
        
        self.frame = ttk.Frame(parent)
        self.selected_group = None
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов вкладки"""
        # Основной фрейм с двумя колонками
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая колонка - список групп
        left_frame = ttk.LabelFrame(main_frame, text="Список групп", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Панель управления группами
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Добавить группу", 
                  command=self._add_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Удалить выбранную", 
                  command=self._delete_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Обновить список", 
                  command=self.load_groups).pack(side=tk.LEFT, padx=5)
        
        # Таблица групп
        table_frame = ttk.Frame(left_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('name', 'user_count', 'default_priority')
        self.groups_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        self.groups_tree.heading('name', text='Имя группы')
        self.groups_tree.heading('user_count', text='Пользователей')
        self.groups_tree.heading('default_priority', text='Приоритет по умолчанию')
        
        self.groups_tree.column('name', width=150)
        self.groups_tree.column('user_count', width=100)
        self.groups_tree.column('default_priority', width=120)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.groups_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.groups_tree.xview)
        self.groups_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.groups_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Привязываем событие выбора группы
        self.groups_tree.bind('<<TreeviewSelect>>', self._on_group_selected)
        
        # Информация о группах
        self.groups_info_label = ttk.Label(left_frame, text="Всего групп: 0")
        self.groups_info_label.pack(side=tk.BOTTOM, anchor=tk.W, pady=(10, 0))
        
        # Правая колонка - атрибуты выбранной группы
        right_frame = ttk.LabelFrame(main_frame, text="Атрибуты группы", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок с именем выбранной группы
        self.selected_group_label = ttk.Label(
            right_frame, 
            text="Выберите группу для просмотра атрибутов",
            font=('Arial', 10, 'bold'),
            foreground='#666666'
        )
        self.selected_group_label.pack(anchor=tk.W, pady=(0, 10))
        
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
    
    def load_groups(self):
        """Загрузка списка групп из БД"""
        if not self.db.connection_status:
            self.logger.log("Нет подключения к БД. Подключитесь сначала.")
            return
        
        try:
            # Очищаем текущий список
            for item in self.groups_tree.get_children():
                self.groups_tree.delete(item)
            
            # Получаем группы из БД
            groups = self.db.get_groups()
            
            # Фильтруем фиктивные группы
            real_groups = [group for group in groups if not group.name.startswith('_group_')]
            
            # Заполняем таблицу
            for group in real_groups:
                self.groups_tree.insert('', tk.END, values=(
                    group.name,
                    group.user_count,
                    group.default_priority
                ))
            
            # Обновляем информацию
            self.groups_info_label.config(text=f"Всего групп: {len(real_groups)}")
            self.logger.log(f"Загружено групп: {len(real_groups)}")
            
        except Exception as e:
            self.logger.log(f"Ошибка загрузки групп: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить группы:\n{str(e)}")
    
    def clear_groups(self):
        """Очистка списка групп"""
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)
        self.groups_info_label.config(text="Всего групп: 0")
        self._clear_attributes()
    
    def _on_group_selected(self, event):
        """Обработка выбора группы"""
        selected = self.groups_tree.selection()
        if not selected:
            return
        
        groupname = self.groups_tree.item(selected[0])['values'][0]
        self.selected_group = groupname
        self._load_group_attributes(groupname)
    
    def _load_group_attributes(self, groupname):
        """Загрузка атрибутов выбранной группы"""
        try:
            # Обновляем заголовок
            self.selected_group_label.config(
                text=f"Атрибуты группы: {groupname}",
                foreground='#333333'
            )
            
            # Очищаем таблицы атрибутов
            self._clear_attributes()
            
            # Получаем атрибуты из БД
            check_attrs, reply_attrs = self.db.get_group_attributes(groupname)
            
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
            self.logger.log(f"Ошибка загрузки атрибутов группы: {str(e)}")
            self.selected_group_label.config(
                text="Ошибка загрузки атрибутов группы",
                foreground='red'
            )
    
    def _clear_attributes(self):
        """Очистка таблиц атрибутов"""
        for item in self.check_tree.get_children():
            self.check_tree.delete(item)
        
        for item in self.reply_tree.get_children():
            self.reply_tree.delete(item)
        
        self.attr_stats_label.config(text="Check: 0 | Reply: 0")
    
    def _add_group(self):
        """Добавление новой группы"""
        if not self.db.connection_status:
            messagebox.showerror("Ошибка", "Нет подключения к БД!")
            return
        
        dialog = GroupDialog(self.parent, "Добавить группу")
        result = dialog.show()
        
        if result:
            groupname, priority = result
            
            # Проверяем, не существует ли уже такая группа
            groups = self.db.get_groups()
            existing_groups = [group.name for group in groups if not group.name.startswith('_group_')]
            
            if groupname in existing_groups:
                messagebox.showinfo("Информация", f"Группа '{groupname}' уже существует!")
                return
            
            # Создаем группу
            group = Group(name=groupname, default_priority=int(priority))
            
            if self.db.add_group(group):
                self.logger.log(f"Добавлена группа: {groupname}")
                messagebox.showinfo("Успех", f"Группа '{groupname}' создана!")
                self.load_groups()
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить группу '{groupname}'")
    
    def _delete_group(self):
        """Удаление группы"""
        selected = self.groups_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите группу для удаления!")
            return
        
        groupname = self.groups_tree.item(selected[0])['values'][0]
        user_count = self.groups_tree.item(selected[0])['values'][1]
        
        # Проверяем, что это не системная группа
        if groupname == "default" or groupname == "users":
            messagebox.showerror("Ошибка", f"Группа '{groupname}' является системной и не может быть удалена!")
            return
        
        # Проверяем количество реальных пользователей
        if user_count > 0:
            if not messagebox.askyesno("Подтверждение", 
                f"В группе '{groupname}' есть {user_count} пользователей.\n"
                f"Все пользователи будут удалены из этой группы. Продолжить?"):
                return
        
        if not messagebox.askyesno("Подтверждение", 
            f"Удалить группу '{groupname}'?\n"
            f"Все пользователи будут удалены из этой группы."):
            return
        
        if self.db.delete_group(groupname):
            self.logger.log(f"Удалена группа: {groupname}")
            messagebox.showinfo("Успех", f"Группа '{groupname}' удалена!")
            self.load_groups()
            self._clear_attributes()
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить группу '{groupname}'")
    
    def _add_check_attr(self):
        """Добавление Check атрибута"""
        if not self.selected_group:
            messagebox.showwarning("Внимание", "Выберите группу!")
            return
        
        dialog = AttributeDialog(self.parent, "Добавить Check атрибут", self.selected_group, 'check')
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            attr = Attribute(attribute=attribute, op=op, value=value)
            
            if self.db.add_group_attribute(self.selected_group, attr, 'check'):
                self.logger.log(f"Добавлен Check атрибут '{attribute}' для группы '{self.selected_group}'")
                self._load_group_attributes(self.selected_group)
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить атрибут '{attribute}'")
    
    def _add_reply_attr(self):
        """Добавление Reply атрибута"""
        if not self.selected_group:
            messagebox.showwarning("Внимание", "Выберите группу!")
            return
        
        dialog = AttributeDialog(self.parent, "Добавить Reply атрибут", self.selected_group, 'reply')
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            attr = Attribute(attribute=attribute, op=op, value=value)
            
            if self.db.add_group_attribute(self.selected_group, attr, 'reply'):
                self.logger.log(f"Добавлен Reply атрибут '{attribute}' для группы '{self.selected_group}'")
                self._load_group_attributes(self.selected_group)
            else:
                messagebox.showerror("Ошибка", f"Не удалось добавить атрибут '{attribute}'")
    
    def _edit_check_attr(self):
        """Редактирование Check атрибута"""
        selected = self.check_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите атрибут для редактирования!")
            return
        
        if not self.selected_group:
            return
        
        # Получаем текущие значения
        values = self.check_tree.item(selected[0])['values']
        
        dialog = AttributeDialog(
            self.parent, 
            "Изменить Check атрибут", 
            self.selected_group, 
            'check',
            values[0],  # attribute
            values[1],  # op
            values[2]   # value
        )
        
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            old_attr = Attribute(attribute=values[0], op=values[1], value=values[2])
            new_attr = Attribute(attribute=attribute, op=op, value=value)
            
            # Удаляем старый атрибут
            if self.db.delete_group_attribute(self.selected_group, old_attr, 'check'):
                # Добавляем новый атрибут
                if self.db.add_group_attribute(self.selected_group, new_attr, 'check'):
                    self.logger.log(f"Изменен Check атрибут для группы '{self.selected_group}'")
                    self._load_group_attributes(self.selected_group)
                else:
                    messagebox.showerror("Ошибка", f"Не удалось изменить атрибут '{attribute}'")
                    # Пытаемся восстановить старый атрибут
                    self.db.add_group_attribute(self.selected_group, old_attr, 'check')
            else:
                messagebox.showerror("Ошибка", f"Не удалось изменить атрибут '{attribute}'")
    
    def _edit_reply_attr(self):
        """Редактирование Reply атрибута"""
        selected = self.reply_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите атрибут для редактирования!")
            return
        
        if not self.selected_group:
            return
        
        # Получаем текущие значения
        values = self.reply_tree.item(selected[0])['values']
        
        dialog = AttributeDialog(
            self.parent, 
            "Изменить Reply атрибут", 
            self.selected_group, 
            'reply',
            values[0],  # attribute
            values[1],  # op
            values[2]   # value
        )
        
        result = dialog.show()
        
        if result:
            attribute, op, value = result
            old_attr = Attribute(attribute=values[0], op=values[1], value=values[2])
            new_attr = Attribute(attribute=attribute, op=op, value=value)
            
            # Удаляем старый атрибут
            if self.db.delete_group_attribute(self.selected_group, old_attr, 'reply'):
                # Добавляем новый атрибут
                if self.db.add_group_attribute(self.selected_group, new_attr, 'reply'):
                    self.logger.log(f"Изменен Reply атрибут для группы '{self.selected_group}'")
                    self._load_group_attributes(self.selected_group)
                else:
                    messagebox.showerror("Ошибка", f"Не удалось изменить атрибут '{attribute}'")
                    # Пытаемся восстановить старый атрибут
                    self.db.add_group_attribute(self.selected_group, old_attr, 'reply')
            else:
                messagebox.showerror("Ошибка", f"Не удалось изменить атрибут '{attribute}'")
    
    def _delete_check_attr(self):
        """Удаление Check атрибута"""
        selected = self.check_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите атрибут для удаления!")
            return
        
        if not self.selected_group:
            return
        
        values = self.check_tree.item(selected[0])['values']
        attr = Attribute(attribute=values[0], op=values[1], value=values[2])
        
        if not messagebox.askyesno("Подтверждение", 
            f"Удалить Check атрибут '{values[0]}' для группы '{self.selected_group}'?"):
            return
        
        if self.db.delete_group_attribute(self.selected_group, attr, 'check'):
            self.logger.log(f"Удален Check атрибут '{values[0]}' для группы '{self.selected_group}'")
            self._load_group_attributes(self.selected_group)
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить атрибут '{values[0]}'")
    
    def _delete_reply_attr(self):
        """Удаление Reply атрибута"""
        selected = self.reply_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите атрибут для удаления!")
            return
        
        if not self.selected_group:
            return
        
        values = self.reply_tree.item(selected[0])['values']
        attr = Attribute(attribute=values[0], op=values[1], value=values[2])
        
        if not messagebox.askyesno("Подтверждение", 
            f"Удалить Reply атрибут '{values[0]}' для группы '{self.selected_group}'?"):
            return
        
        if self.db.delete_group_attribute(self.selected_group, attr, 'reply'):
            self.logger.log(f"Удален Reply атрибут '{values[0]}' для группы '{self.selected_group}'")
            self._load_group_attributes(self.selected_group)
        else:
            messagebox.showerror("Ошибка", f"Не удалось удалить атрибут '{values[0]}'")
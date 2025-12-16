#!/usr/bin/env python3
"""
Диалоговые окна приложения
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple

class PasswordDialog:
    """Диалог для изменения пароля"""
    
    def __init__(self, parent, title: str, username: str):
        self.parent = parent
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{title} - {username}")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text=f"Пользователь: {username}", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        ttk.Label(self.dialog, text="Новый пароль:").pack()
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.dialog, textvariable=self.password_var, show="*", width=30)
        self.password_entry.pack(pady=5)
        
        ttk.Label(self.dialog, text="Подтверждение:").pack()
        self.confirm_var = tk.StringVar()
        self.confirm_entry = ttk.Entry(self.dialog, textvariable=self.confirm_var, show="*", width=30)
        self.confirm_entry.pack(pady=5)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self._center_dialog()
        self.password_entry.focus_set()
    
    def _center_dialog(self):
        """Центрирование диалогового окна"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _save(self):
        """Сохранение пароля"""
        if self.password_var.get() != self.confirm_var.get():
            messagebox.showerror("Ошибка", "Пароли не совпадают!")
            return
        
        if not self.password_var.get():
            messagebox.showerror("Ошибка", "Пароль не может быть пустым!")
            return
        
        self.result = self.password_var.get()
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """Показать диалог и вернуть результат"""
        self.parent.wait_window(self.dialog)
        return self.result

class GroupDialog:
    """Диалог для добавления/редактирования группы"""
    
    def __init__(self, parent, title: str, groupname: str = "", priority: int = 10):
        self.parent = parent
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("350x180")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text="Имя группы:", font=('Arial', 10, 'bold')).pack(pady=5)
        
        self.group_var = tk.StringVar(value=groupname)
        self.group_entry = ttk.Entry(self.dialog, textvariable=self.group_var, width=30)
        self.group_entry.pack(pady=5)
        
        ttk.Label(self.dialog, text="Приоритет по умолчанию:").pack(pady=5)
        self.priority_var = tk.StringVar(value=str(priority))
        self.priority_spinbox = tk.Spinbox(self.dialog, from_=1, to=99, 
                                          textvariable=self.priority_var, width=30)
        self.priority_spinbox.pack(pady=5)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self._center_dialog()
        if not groupname:
            self.group_entry.focus_set()
        else:
            self.priority_spinbox.focus_set()
    
    def _center_dialog(self):
        """Центрирование диалогового окна"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _save(self):
        """Сохранение группы"""
        groupname = self.group_var.get().strip()
        if not groupname:
            messagebox.showerror("Ошибка", "Введите имя группы!")
            return
        
        if len(groupname) > 64:
            messagebox.showerror("Ошибка", "Имя группы не должно превышать 64 символа!")
            return
        
        try:
            priority = int(self.priority_var.get())
            if not 1 <= priority <= 99:
                messagebox.showerror("Ошибка", "Приоритет должен быть от 1 до 99!")
                return
            
            self.result = (groupname, priority)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Приоритет должен быть числом!")
    
    def show(self) -> Optional[Tuple[str, int]]:
        """Показать диалог и вернуть результат"""
        self.parent.wait_window(self.dialog)
        return self.result

class AttributeDialog:
    """Диалог для добавления/редактирования атрибута"""
    
    def __init__(self, parent, title: str, groupname: str, attr_type: str, 
                 attr_values: Tuple[str, str, str] = None):
        self.parent = parent
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text=f"Группа: {groupname}", 
                 font=('Arial', 10, 'bold')).pack(pady=5)
        
        ttk.Label(self.dialog, text="Атрибут:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        self.attr_var = tk.StringVar()
        self.attr_entry = ttk.Entry(self.dialog, textvariable=self.attr_var, width=40)
        self.attr_entry.pack(padx=20, pady=(5, 0))
        
        ttk.Label(self.dialog, text="Оператор:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        self.op_var = tk.StringVar(value=":=" if attr_type == 'check' else "=")
        self.op_combo = ttk.Combobox(self.dialog, textvariable=self.op_var, 
                                    values=["==", ":=", "=", "+=", "-=", "^="],
                                    width=10, state="readonly")
        self.op_combo.pack(anchor=tk.W, padx=20, pady=(5, 0))
        
        ttk.Label(self.dialog, text="Значение:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(self.dialog, textvariable=self.value_var, width=40)
        self.value_entry.pack(padx=20, pady=(5, 0))
        
        # Заполняем значения для редактирования
        if attr_values:
            self.attr_var.set(attr_values[0])
            self.op_var.set(attr_values[1])
            self.value_var.set(attr_values[2])
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Сохранить", command=self._save, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
        self._center_dialog()
        self.attr_entry.focus_set()
    
    def _center_dialog(self):
        """Центрирование диалогового окна"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _save(self):
        """Сохранение атрибута"""
        attribute = self.attr_var.get().strip()
        op = self.op_var.get()
        value = self.value_var.get().strip()
        
        if not attribute or not value:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        self.result = (attribute, op, value)
        self.dialog.destroy()
    
    def show(self) -> Optional[Tuple[str, str, str]]:
        """Показать диалог и вернуть результат"""
        self.parent.wait_window(self.dialog)
        return self.result

class BulkPasswordDialog:
    """Диалог для массового изменения пароля"""
    
    def __init__(self, parent, title: str, user_count: int):
        self.parent = parent
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x180")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text=f"Изменить пароль для {user_count} пользователей", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        ttk.Label(self.dialog, text="Новый пароль:").pack()
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.dialog, textvariable=self.password_var, width=30)
        self.password_entry.pack(pady=5)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Изменить", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self._center_dialog()
        self.password_entry.focus_set()
    
    def _center_dialog(self):
        """Центрирование диалогового окна"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _save(self):
        """Сохранение пароля"""
        if not self.password_var.get():
            messagebox.showerror("Ошибка", "Пароль не может быть пустым!")
            return
        
        self.result = self.password_var.get()
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """Показать диалог и вернуть результат"""
        self.parent.wait_window(self.dialog)
        return self.result
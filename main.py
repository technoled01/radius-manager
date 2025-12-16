#!/usr/bin/env python3
"""
Главный файл приложения RADIUS User Manager
"""

import tkinter as tk
from gui.main_window import RadiusManagerMainWindow

def main():
    """Точка входа в программу"""
    root = tk.Tk()
    
    # Устанавливаем иконку (если есть)
    try:
        root.iconbitmap('icon.ico')
    except:
        try:
            root.iconbitmap('assets/icon.ico')
        except:
            pass
    
    app = RadiusManagerMainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Модуль конфигурации приложения
"""

import configparser
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Конфигурация подключения к базе данных MSSQL"""
    driver: str = 'ODBC Driver 17 for SQL Server'
    server: str = 'localhost'
    port: str = '1433'
    database: str = 'radius'
    username: str = 'sa'
    password: str = ''
    trusted_connection: bool = False
    encrypt: bool = False
    autoconnect: bool = True
    
    def build_connection_string(self) -> str:
        """Построение строки подключения для MSSQL"""
        conn_str = f"DRIVER={{{self.driver}}};SERVER={self.server},{self.port};DATABASE={self.database};"
        
        if self.trusted_connection:
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={self.username};PWD={self.password};"
        
        if self.encrypt:
            conn_str += "Encrypt=yes;TrustServerCertificate=yes;"
        else:
            conn_str += "Encrypt=no;"
        
        return conn_str

@dataclass
class ApplicationConfig:
    """Конфигурация приложения"""
    window_width: int = 1000
    window_height: int = 650
    config_file: str = 'radius_config_mssql.ini'
    log_file: str = 'radius_manager.log'
    theme: str = 'clam'

class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self, config_file: str = 'radius_config_mssql.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.db_config = DatabaseConfig()
        self.app_config = ApplicationConfig()
        self.load()
    
    def load(self) -> bool:
        """Загрузка конфигурации из файла"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                self._load_database_config()
                self._load_application_config()
                return True
            else:
                self.create_default_config()
                return True
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return False
    
    def save(self) -> bool:
        """Сохранение конфигурации в файл"""
        try:
            self._save_database_config()
            self._save_application_config()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def create_default_config(self):
        """Создание конфигурации по умолчанию"""
        self.db_config = DatabaseConfig()
        self.app_config = ApplicationConfig()
        self.save()
    
    def get_database_config(self) -> DatabaseConfig:
        """Получение конфигурации БД"""
        return self.db_config
    
    def get_application_config(self) -> ApplicationConfig:
        """Получение конфигурации приложения"""
        return self.app_config
    
    def update_database_config(self, **kwargs):
        """Обновление конфигурации БД"""
        for key, value in kwargs.items():
            if hasattr(self.db_config, key):
                setattr(self.db_config, key, value)
    
    def update_application_config(self, **kwargs):
        """Обновление конфигурации приложения"""
        for key, value in kwargs.items():
            if hasattr(self.app_config, key):
                setattr(self.app_config, key, value)
    
    def _load_database_config(self):
        """Загрузка конфигурации БД из ConfigParser"""
        if 'DATABASE' not in self.config:
            return
        
        section = self.config['DATABASE']
        
        self.db_config.driver = section.get('driver', 'ODBC Driver 17 for SQL Server')
        self.db_config.server = section.get('server', 'localhost')
        self.db_config.port = section.get('port', '1433')
        self.db_config.database = section.get('database', 'radius')
        self.db_config.username = section.get('username', 'sa')
        self.db_config.password = section.get('password', '')
        self.db_config.trusted_connection = section.getboolean('trusted_connection', False)
        self.db_config.encrypt = section.getboolean('encrypt', False)
        self.db_config.autoconnect = section.getboolean('autoconnect', True)
    
    def _load_application_config(self):
        """Загрузка конфигурации приложения из ConfigParser"""
        if 'APPLICATION' not in self.config:
            return
        
        section = self.config['APPLICATION']
        
        self.app_config.window_width = int(section.get('window_width', '1000'))
        self.app_config.window_height = int(section.get('window_height', '650'))
        self.app_config.config_file = section.get('config_file', 'radius_config_mssql.ini')
        self.app_config.log_file = section.get('log_file', 'radius_manager.log')
        self.app_config.theme = section.get('theme', 'clam')
    
    def _save_database_config(self):
        """Сохранение конфигурации БД в ConfigParser"""
        if 'DATABASE' not in self.config:
            self.config['DATABASE'] = {}
        
        self.config['DATABASE']['driver'] = self.db_config.driver
        self.config['DATABASE']['server'] = self.db_config.server
        self.config['DATABASE']['port'] = self.db_config.port
        self.config['DATABASE']['database'] = self.db_config.database
        self.config['DATABASE']['username'] = self.db_config.username
        self.config['DATABASE']['password'] = self.db_config.password
        self.config['DATABASE']['trusted_connection'] = str(self.db_config.trusted_connection)
        self.config['DATABASE']['encrypt'] = str(self.db_config.encrypt)
        self.config['DATABASE']['autoconnect'] = str(self.db_config.autoconnect)
    
    def _save_application_config(self):
        """Сохранение конфигурации приложения в ConfigParser"""
        if 'APPLICATION' not in self.config:
            self.config['APPLICATION'] = {}
        
        self.config['APPLICATION']['window_width'] = str(self.app_config.window_width)
        self.config['APPLICATION']['window_height'] = str(self.app_config.window_height)
        self.config['APPLICATION']['config_file'] = self.app_config.config_file
        self.config['APPLICATION']['log_file'] = self.app_config.log_file
        self.config['APPLICATION']['theme'] = self.app_config.theme
    
    def restore_defaults(self):
        """Восстановление настроек по умолчанию"""
        self.db_config = DatabaseConfig()
        self.save()
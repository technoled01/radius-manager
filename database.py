#!/usr/bin/env python3
"""
Модуль для работы с базой данных MSSQL RADIUS
"""

import pyodbc
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from config import DatabaseConfig

@dataclass
class User:
    """Модель пользователя RADIUS"""
    username: str
    group: str = 'default'
    status: str = 'Активен'
    last_login: str = 'Никогда'
    password: str = ''
    expiration: str = ''
    simultaneous_use: int = 1
    session_timeout: int = 3600
    idle_timeout: int = 0

@dataclass
class Group:
    """Модель группы RADIUS"""
    name: str
    user_count: int = 0
    default_priority: int = 10

@dataclass
class Attribute:
    """Модель атрибута RADIUS"""
    attribute: str
    op: str
    value: str

class DatabaseManager:
    """Менеджер базы данных MSSQL RADIUS"""
    
    def __init__(self, logger=None):
        self.conn = None
        self.connection_status = False
        self.logger = logger
        self.config = None
    
    def connect(self, config: DatabaseConfig) -> bool:
        """Подключение к базе данных"""
        try:
            if self.conn:
                self.disconnect()
            
            self.config = config
            conn_str = config.build_connection_string()
            
            if self.logger:
                self.logger.log(f"Подключаемся к: {config.server}:{config.port}")
                self.logger.log(f"База данных: {config.database}")
            
            self.conn = pyodbc.connect(conn_str, timeout=10)
            
            # Тестируем подключение
            cursor = self.conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version_info = cursor.fetchone()[0]
            cursor.close()
            
            self.connection_status = True
            
            if self.logger:
                self.logger.log("Успешное подключение к MSSQL")
                self.logger.log(f"Версия сервера: {version_info[:100]}...")
            
            # Проверяем наличие таблиц
            self.check_radius_tables()
            
            return True
            
        except pyodbc.Error as e:
            self.connection_status = False
            error_msg = str(e).replace('\n', ' ')
            if self.logger:
                self.logger.log(f"Ошибка подключения: {error_msg}")
            return False
    
    def disconnect(self) -> bool:
        """Отключение от базы данных"""
        if self.conn:
            try:
                self.conn.close()
                self.connection_status = False
                if self.logger:
                    self.logger.log("Отключено от базы данных MSSQL")
                return True
            except Exception as e:
                if self.logger:
                    self.logger.log(f"Ошибка отключения: {str(e)}")
                return False
        return True
    
    def test_connection(self, config: DatabaseConfig) -> Tuple[bool, str]:
        """Тестирование подключения"""
        try:
            conn_str = config.build_connection_string()
            test_conn = pyodbc.connect(conn_str, timeout=5)
            cursor = test_conn.cursor()
            cursor.execute("SELECT DB_NAME() AS db_name, @@VERSION AS version")
            result = cursor.fetchone()
            
            db_name = result[0]
            version = result[1]
            
            cursor.close()
            test_conn.close()
            
            return True, f"База данных: {db_name}\nСервер: {config.server}:{config.port}"
            
        except pyodbc.Error as e:
            error_msg = str(e).replace('\n', ' ')
            return False, error_msg
    
    def check_radius_tables(self):
        """Проверка наличия необходимых таблиц RADIUS"""
        try:
            cursor = self.conn.cursor()
            
            tables_to_check = ['radcheck', 'radreply', 'radusergroup', 'radacct', 'radgroupcheck', 'radgroupreply']
            missing_tables = []
            
            for table in tables_to_check:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table}'
                """)
                if cursor.fetchone()[0] == 0:
                    missing_tables.append(table)
            
            cursor.close()
            
            if missing_tables:
                if self.logger:
                    self.logger.log(f"ВНИМАНИЕ: Отсутствуют таблицы: {', '.join(missing_tables)}")
            
        except pyodbc.Error as e:
            if self.logger:
                self.logger.log(f"Ошибка проверки таблиц: {str(e)}")
    
    def create_radius_tables(self):
        """Создание стандартных таблиц RADIUS"""
        try:
            cursor = self.conn.cursor()
            
            # Таблица radcheck
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'radcheck')
                CREATE TABLE radcheck (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(64) NOT NULL,
                    attribute NVARCHAR(64) NOT NULL,
                    op CHAR(2) DEFAULT ':=' NOT NULL,
                    value NVARCHAR(253) NOT NULL
                )
            """)
            
            # Таблица radreply
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'radreply')
                CREATE TABLE radreply (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(64) NOT NULL,
                    attribute NVARCHAR(64) NOT NULL,
                    op CHAR(2) DEFAULT '=' NOT NULL,
                    value NVARCHAR(253) NOT NULL
                )
            """)
            
            # Таблица radusergroup
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'radusergroup')
                CREATE TABLE radusergroup (
                    username NVARCHAR(64) NOT NULL,
                    groupname NVARCHAR(64) NOT NULL,
                    priority INT DEFAULT 10
                )
            """)
            
            # Таблица radacct
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'radacct')
                CREATE TABLE radacct (
                    radacctid BIGINT IDENTITY(1,1) PRIMARY KEY,
                    acctsessionid NVARCHAR(64) NOT NULL,
                    acctuniqueid NVARCHAR(32) NOT NULL,
                    username NVARCHAR(64),
                    groupname NVARCHAR(64),
                    realm NVARCHAR(64),
                    nasipaddress NVARCHAR(15) NOT NULL,
                    nasportid NVARCHAR(15),
                    nasporttype NVARCHAR(32),
                    acctstarttime DATETIME,
                    acctstoptime DATETIME,
                    acctsessiontime INT,
                    acctauthentic NVARCHAR(32),
                    connectinfo_start NVARCHAR(50),
                    connectinfo_stop NVARCHAR(50),
                    acctinputoctets BIGINT,
                    acctoutputoctets BIGINT,
                    calledstationid NVARCHAR(50),
                    callingstationid NVARCHAR(50),
                    acctterminatecause NVARCHAR(32),
                    servicetype NVARCHAR(32),
                    framedprotocol NVARCHAR(32),
                    framedipaddress NVARCHAR(15)
                )
            """)
            
            # Таблица radgroupcheck
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'radgroupcheck')
                CREATE TABLE radgroupcheck (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    groupname NVARCHAR(64) NOT NULL,
                    attribute NVARCHAR(64) NOT NULL,
                    op CHAR(2) DEFAULT ':=' NOT NULL,
                    value NVARCHAR(253) NOT NULL
                )
            """)
            
            # Таблица radgroupreply
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'radgroupreply')
                CREATE TABLE radgroupreply (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    groupname NVARCHAR(64) NOT NULL,
                    attribute NVARCHAR(64) NOT NULL,
                    op CHAR(2) DEFAULT '=' NOT NULL,
                    value NVARCHAR(253) NOT NULL
                )
            """)
            
            # Создаем индексы
            try:
                cursor.execute("CREATE INDEX idx_radcheck_username ON radcheck(username)")
                cursor.execute("CREATE INDEX idx_radreply_username ON radreply(username)")
                cursor.execute("CREATE INDEX idx_radusergroup_username ON radusergroup(username)")
                cursor.execute("CREATE INDEX idx_radacct_username ON radacct(username)")
                cursor.execute("CREATE INDEX idx_radacct_acctstarttime ON radacct(acctstarttime)")
                cursor.execute("CREATE INDEX idx_radgroupcheck_groupname ON radgroupcheck(groupname)")
                cursor.execute("CREATE INDEX idx_radgroupreply_groupname ON radgroupreply(groupname)")
            except:
                pass  # Индексы уже могут существовать
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log("Таблицы RADIUS успешно созданы")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка создания таблиц: {str(e)}")
            return False
    
    # Методы для работы с пользователями
    def get_users(self) -> List[User]:
        """Получение списка всех пользователей"""
        if not self.connection_status:
            return []
        
        try:
            cursor = self.conn.cursor()
            
            query = """
            SELECT 
                rc.username,
                COALESCE(rug.groupname, 'default') as groupname,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM radcheck rc2 
                        WHERE rc2.username = rc.username 
                        AND rc2.attribute = 'Login-Time' 
                        AND rc2.value = 'Never'
                    ) THEN 'Заблокирован'
                    ELSE 'Активен'
                END as status,
                COALESCE(
                    CONVERT(VARCHAR(16), MAX(ra.acctstarttime), 120),
                    'Никогда'
                ) as last_login
            FROM radcheck rc
            LEFT JOIN radusergroup rug ON rc.username = rug.username
            LEFT JOIN radacct ra ON rc.username = ra.username
            WHERE rc.attribute = 'Cleartext-Password'
            GROUP BY rc.username, rug.groupname
            ORDER BY rc.username
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            users = []
            for row in rows:
                users.append(User(
                    username=row[0] if row[0] else '',
                    group=row[1] if row[1] else 'default',
                    status=row[2] if row[2] else 'Активен',
                    last_login=row[3] if row[3] else 'Никогда'
                ))
            
            return users
            
        except pyodbc.Error as e:
            if self.logger:
                self.logger.log(f"Ошибка получения пользователей: {str(e)}")
            return []
    
    def user_exists(self, username: str) -> bool:
        """Проверка существования пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM radcheck WHERE username = ? AND attribute = 'Cleartext-Password'",
                (username,)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
        except:
            return False
    
    def add_user(self, user: User, extra_attributes: List[Attribute] = None) -> bool:
        """Добавление нового пользователя"""
        try:
            cursor = self.conn.cursor()
            
            # Добавляем пароль (правильный порядок: UserName, Attribute, Value, op)
            cursor.execute(
                "INSERT INTO radcheck (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                (user.username, 'Cleartext-Password', user.password, ':=')
            )
            
            # Добавляем в группу
            cursor.execute(
                "INSERT INTO radusergroup (username, groupname, priority) VALUES (?, ?, ?)",
                (user.username, user.group, 10)
            )
            
            # Срок действия
            if user.expiration:
                cursor.execute(
                    "INSERT INTO radcheck (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                    (user.username, 'Expiration', user.expiration, ':=')
                )
            
            # Ограничение одновременных сессий
            if user.simultaneous_use and int(user.simultaneous_use) > 1:
                cursor.execute(
                    "INSERT INTO radcheck (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                    (user.username, 'Simultaneous-Use', user.simultaneous_use, ':=')
                )
            
            # Session-Timeout (для radreply тоже проверяем порядок)
            if user.session_timeout and int(user.session_timeout) != 3600:
                cursor.execute(
                    "INSERT INTO radreply (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                    (user.username, 'Session-Timeout', user.session_timeout, '=')
                )
            
            # Idle-Timeout
            if user.idle_timeout and int(user.idle_timeout) != 0:
                cursor.execute(
                    "INSERT INTO radreply (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                    (user.username, 'Idle-Timeout', user.idle_timeout, '=')
                )
            
            # Дополнительные атрибуты
            if extra_attributes:
                for attr in extra_attributes:
                    cursor.execute(
                        "INSERT INTO radreply (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                        (user.username, attr.attribute, attr.value, attr.op)
                    )
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Добавлен пользователь: {user.username}")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка добавления пользователя: {str(e)}")
            return False
    
    def update_user_password(self, username: str, new_password: str) -> bool:
        """Обновление пароля пользователя"""
        try:
            cursor = self.conn.cursor()
            
            # Удаляем старые пароли
            cursor.execute(
                "DELETE FROM radcheck WHERE UserName = ? AND Attribute LIKE '%Password'",
                (username,)
            )
            
            # Добавляем новый пароль (правильный порядок)
            cursor.execute(
                "INSERT INTO radcheck (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                (username, 'Cleartext-Password', new_password, ':=')
            )
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Изменен пароль для: {username}")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка изменения пароля: {str(e)}")
            return False
    
    def block_user(self, username: str, block: bool = True) -> bool:
        """Блокировка/разблокировка пользователя"""
        try:
            cursor = self.conn.cursor()
            
            if block:
                # Добавляем атрибут блокировки
                cursor.execute(
                    "INSERT INTO radcheck (username, attribute, op, value) VALUES (?, ?, ?, ?)",
                    (username, 'Login-Time', ':=', 'Never')
                )
            else:
                # Удаляем атрибут блокировки
                cursor.execute(
                    "DELETE FROM radcheck WHERE username = ? AND attribute = 'Login-Time' AND value = 'Never'",
                    (username,)
                )
            
            self.conn.commit()
            cursor.close()
            
            action = "заблокирован" if block else "разблокирован"
            if self.logger:
                self.logger.log(f"Пользователь {username} {action}")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка блокировки: {str(e)}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """Удаление пользователя"""
        try:
            cursor = self.conn.cursor()
            
            # Удаляем из всех таблиц RADIUS
            tables = ['radcheck', 'radreply', 'radusergroup', 'radacct']
            for table in tables:
                try:
                    cursor.execute(f"DELETE FROM {table} WHERE username = ?", (username,))
                except:
                    pass  # Игнорируем ошибки если таблицы не существует
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Удален пользователь: {username}")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка удаления: {str(e)}")
            return False
    
    # Методы для работы с группами
    def get_groups(self) -> List[Group]:
        """Получение списка групп"""
        if not self.connection_status:
            return []
        
        try:
            cursor = self.conn.cursor()
            
            query = """
            SELECT 
                groupname,
                COUNT(DISTINCT username) as user_count,
                MIN(priority) as default_priority
            FROM radusergroup
            GROUP BY groupname
            ORDER BY groupname
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            groups = []
            for row in rows:
                groups.append(Group(
                    name=row[0] if row[0] else '',
                    user_count=row[1] if row[1] else 0,
                    default_priority=row[2] if row[2] else 10
                ))
            
            return groups
            
        except pyodbc.Error as e:
            if self.logger:
                self.logger.log(f"Ошибка получения групп: {str(e)}")
            return []
    
    def add_group(self, group: Group) -> bool:
        """Добавление новой группы"""
        try:
            cursor = self.conn.cursor()
            
            # Создаем фиктивного пользователя для группы
            fake_username = f"_group_{group.name}"
            cursor.execute(
                "INSERT INTO radusergroup (username, groupname, priority) VALUES (?, ?, ?)",
                (fake_username, group.name, group.default_priority)
            )
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Добавлена группа: {group.name}")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка добавления группы: {str(e)}")
            return False
    
    def delete_group(self, groupname: str) -> bool:
        """Удаление группы"""
        try:
            cursor = self.conn.cursor()
            
            # Удаляем всех пользователей из этой группы
            cursor.execute("DELETE FROM radusergroup WHERE groupname = ?", (groupname,))
            
            # Удаляем атрибуты группы
            cursor.execute("DELETE FROM radgroupcheck WHERE groupname = ?", (groupname,))
            cursor.execute("DELETE FROM radgroupreply WHERE groupname = ?", (groupname,))
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Удалена группа: {groupname}")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка удаления группы: {str(e)}")
            return False
    
    def get_group_attributes(self, groupname: str) -> Tuple[List[Attribute], List[Attribute]]:
        """Получение атрибутов группы"""
        check_attrs = []
        reply_attrs = []
        
        if not self.connection_status:
            return check_attrs, reply_attrs
        
        try:
            cursor = self.conn.cursor()
            
            # Check атрибуты
            cursor.execute("""
                SELECT attribute, op, value 
                FROM radgroupcheck 
                WHERE groupname = ? 
                ORDER BY attribute
            """, (groupname,))
            
            for row in cursor.fetchall():
                check_attrs.append(Attribute(
                    attribute=row[0],  # attribute
                    op=row[1],         # op
                    value=row[2]       # value
                ))
            
            # Reply атрибуты
            cursor.execute("""
                SELECT attribute, op, value 
                FROM radgroupreply 
                WHERE groupname = ? 
                ORDER BY attribute
            """, (groupname,))
            
            for row in cursor.fetchall():
                reply_attrs.append(Attribute(
                    attribute=row[0],  # attribute
                    op=row[1],         # op
                    value=row[2]       # value
                ))
            
            cursor.close()
            
        except pyodbc.Error as e:
            if self.logger:
                self.logger.log(f"Ошибка получения атрибутов группы: {str(e)}")
        
        return check_attrs, reply_attrs
    
    def add_group_attribute(self, groupname: str, attr: Attribute, attr_type: str = 'check') -> bool:
        """Добавление атрибута группы"""
        try:
            cursor = self.conn.cursor()
            
            if attr_type == 'check':
                table = 'radgroupcheck'
            else:
                table = 'radgroupreply'
            
            # Преобразуем к строкам
            attribute_str = str(attr.attribute)
            value_str = str(attr.value)
            
            cursor.execute(
                f"INSERT INTO {table} (groupname, attribute, value, op) VALUES (?, ?, ?, ?)",
                (groupname, attribute_str, value_str, attr.op)
            )
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Добавлен {attr_type} атрибут '{attr.attribute}' для группы '{groupname}'")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка добавления атрибута: {str(e)}")
            return False
    
    def delete_group_attribute(self, groupname: str, attr: Attribute, attr_type: str = 'check') -> bool:
        """Удаление атрибута группы"""
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            if attr_type == 'check':
                table = 'radgroupcheck'
            else:
                table = 'radgroupreply'
            
            # Преобразуем к строкам
            attribute_str = str(attr.attribute)
            value_str = str(attr.value)
            
            cursor.execute(
                f"DELETE FROM {table} WHERE groupname = ? AND attribute = ? AND value = ? AND op = ?",
                (groupname, attribute_str, value_str, attr.op)
            )
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Удален {attr_type} атрибут '{attr.attribute}' для группы '{groupname}'")
            
            return True
            
        except pyodbc.Error as e:
            if cursor:
                self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка удаления атрибута: {str(e)}")
            return False
    
    # Методы для массовых операций
    def bulk_add_users(self, users: List[User]) -> Tuple[int, List[str]]:
        """Массовое добавление пользователей"""
        added = 0
        errors = []
        
        for user in users:
            try:
                if self.add_user(user):
                    added += 1
            except Exception as e:
                errors.append(f"{user.username}: {str(e)}")
        
        return added, errors
    
    def export_users_to_csv(self, filename: str) -> int:
        """Экспорт пользователей в CSV"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT rc.username, rc.value as password, 
                       COALESCE(rug.groupname, 'default') as groupname,
                       (SELECT TOP 1 value FROM radcheck WHERE username = rc.username AND attribute = 'Expiration') as expiration
                FROM radcheck rc
                LEFT JOIN radusergroup rug ON rc.username = rug.username
                WHERE rc.attribute = 'Cleartext-Password'
                ORDER BY rc.username
            """)
            
            users = cursor.fetchall()
            cursor.close()
            
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Username', 'Password', 'Group', 'Expiration'])
                
                for user in users:
                    writer.writerow([
                        user[0] if user[0] else '',
                        user[1] if user[1] else '',
                        user[2] if user[2] else '',
                        user[3] if user[3] else ''
                    ])
            
            if self.logger:
                self.logger.log(f"Экспорт CSV: {len(users)} пользователей")
            
            return len(users)
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"Ошибка экспорта CSV: {str(e)}")
            return 0
       
        # Методы для работы с атрибутами пользователя
    def get_user_attributes(self, username: str) -> Tuple[List[Attribute], List[Attribute]]:
        """Получение атрибутов пользователя"""
        check_attrs = []
        reply_attrs = []
        
        if not self.connection_status:
            return check_attrs, reply_attrs
        
        try:
            cursor = self.conn.cursor()
            
            # Check атрибуты (исключаем пароль из списка)
            # Исправленный порядок: Attribute, op, Value
            cursor.execute("""
                SELECT Attribute, op, Value 
                FROM radcheck 
                WHERE UserName = ? 
                AND Attribute != 'Cleartext-Password'  -- Не показываем пароль
                ORDER BY Attribute
            """, (username,))
            
            for row in cursor.fetchall():
                check_attrs.append(Attribute(
                    attribute=row[0],  # Attribute
                    op=row[1],         # op
                    value=row[2]       # Value
                ))
            
            # Reply атрибуты
            cursor.execute("""
                SELECT Attribute, op, Value 
                FROM radreply 
                WHERE UserName = ? 
                ORDER BY Attribute
            """, (username,))
            
            for row in cursor.fetchall():
                reply_attrs.append(Attribute(
                    attribute=row[0],  # Attribute
                    op=row[1],         # op
                    value=row[2]       # Value
                ))
            
            cursor.close()
            
        except pyodbc.Error as e:
            if self.logger:
                self.logger.log(f"Ошибка получения атрибутов пользователя: {str(e)}")
        
        return check_attrs, reply_attrs
    
    def add_user_attribute(self, username: str, attr: Attribute, attr_type: str = 'check') -> bool:
        """Добавление атрибута пользователя"""
        try:
            cursor = self.conn.cursor()
            
            if attr_type == 'check':
                table = 'radcheck'
            else:
                table = 'radreply'
            
            # Преобразуем к строкам
            attribute_str = str(attr.attribute)
            value_str = str(attr.value)
            
            cursor.execute(
                f"INSERT INTO {table} (UserName, Attribute, Value, op) VALUES (?, ?, ?, ?)",
                (username, attribute_str, value_str, attr.op)
            )
            
            self.conn.commit()
            cursor.close()
            
            if self.logger:
                self.logger.log(f"Добавлен {attr_type} атрибут '{attr.attribute}' для пользователя '{username}'")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка добавления атрибута пользователя: {str(e)}")
            return False
    
    def delete_user_attribute(self, username: str, attr: Attribute, attr_type: str = 'check') -> bool:
        """Удаление атрибута пользователя"""
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            if attr_type == 'check':
                table = 'radcheck'
            else:
                table = 'radreply'
            
            # ВАЖНО: Преобразуем все значения к строкам
            attribute_str = str(attr.attribute)
            value_str = str(attr.value)
            
            # Отладочная информация
            print(f"DEBUG delete_user_attribute:")
            print(f"  Username: {username}")
            print(f"  Attribute (orig): {attr.attribute}, type: {type(attr.attribute)}")
            print(f"  Attribute (str): {attribute_str}, type: {type(attribute_str)}")
            print(f"  Value (orig): {attr.value}, type: {type(attr.value)}")
            print(f"  Value (str): {value_str}, type: {type(value_str)}")
            print(f"  Op: {attr.op}")
            
            # Выполняем DELETE с преобразованными строками
            cursor.execute(
                f"DELETE FROM {table} WHERE UserName = ? AND Attribute = ? AND Value = ? AND op = ?",
                (username, attribute_str, value_str, attr.op)
            )
            
            rows_deleted = cursor.rowcount
            print(f"  Rows deleted: {rows_deleted}")
            
            self.conn.commit()
            cursor.close()
            
            if self.logger and rows_deleted > 0:
                self.logger.log(f"Удален {attr_type} атрибут '{attr.attribute}' для пользователя '{username}'")
            
            return rows_deleted > 0
            
        except pyodbc.Error as e:
            if cursor:
                self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка удаления атрибута пользователя: {str(e)}")
            return False
        except Exception as e:
            if cursor:
                self.conn.rollback()
            if self.logger:
                self.logger.log(f"Неожиданная ошибка при удалении атрибута: {str(e)}")
            return False
    
    def update_user_attribute(self, username: str, old_attr: Attribute, new_attr: Attribute, attr_type: str = 'check') -> bool:
        """Обновление атрибута пользователя"""
        try:
            # Преобразуем старые значения к строкам
            old_attribute_str = str(old_attr.attribute)
            old_value_str = str(old_attr.value)
            
            # Преобразуем новые значения к строкам
            new_attribute_str = str(new_attr.attribute)
            new_value_str = str(new_attr.value)
            
            # Удаляем старый атрибут
            if not self.delete_user_attribute(username, old_attr, attr_type):
                return False
            
            # Добавляем новый атрибут
            if not self.add_user_attribute(username, new_attr, attr_type):
                # Пытаемся восстановить старый атрибут
                self.add_user_attribute(username, old_attr, attr_type)
                return False
            
            if self.logger:
                self.logger.log(f"Обновлен {attr_type} атрибут для пользователя '{username}'")
            
            return True
            
        except pyodbc.Error as e:
            self.conn.rollback()
            if self.logger:
                self.logger.log(f"Ошибка обновления атрибута пользователя: {str(e)}")
            return False
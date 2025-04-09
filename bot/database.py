import sqlite3
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name="bot_data.db"):
        self.db_name = db_name
        self.lock = threading.Lock()
        
    def init(self):
        """Инициализация базы данных."""
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # Создаем таблицу для хранения использования
            c.execute('''
                CREATE TABLE IF NOT EXISTS user_usage (
                    user_id INTEGER PRIMARY KEY,
                    photo_count INTEGER DEFAULT 0,
                    last_reset TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
    def get_user_count(self, user_id):
        """Получить количество обработанных фото пользователя за сегодня."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # Получаем данные пользователя
            c.execute('SELECT photo_count, last_reset FROM user_usage WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            
            if not result:
                # Если пользователя нет, создаем запись
                c.execute(
                    'INSERT INTO user_usage (user_id, photo_count, last_reset) VALUES (?, 0, ?)',
                    (user_id, today)
                )
                conn.commit()
                conn.close()
                return 0
                
            count, last_reset = result
            
            # Если последний сброс был не сегодня, обнуляем счетчик
            if last_reset != today:
                c.execute(
                    'UPDATE user_usage SET photo_count = 0, last_reset = ? WHERE user_id = ?',
                    (today, user_id)
                )
                conn.commit()
                conn.close()
                return 0
                
            conn.close()
            return count
            
    def increment_user_count(self, user_id):
        """Увеличить счетчик обработанных фото пользователя."""
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            c.execute(
                'UPDATE user_usage SET photo_count = photo_count + 1 WHERE user_id = ?',
                (user_id,)
            )
            
            conn.commit()
            conn.close()
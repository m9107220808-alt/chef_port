import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "shop.db")

def migrate():
    """Создать таблицу user_addresses"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Создаём таблицу адресов
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            address_label TEXT,
            full_address TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Таблица user_addresses создана!")

if __name__ == "__main__":
    migrate()

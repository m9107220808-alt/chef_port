import sqlite3
import os
from datetime import datetime

# ✅ Используем абсолютный путь к корню проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shop.db")

print(f"📂 Путь к БД: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Проверяем, есть ли записи с NULL в created_at
cur.execute("SELECT COUNT(*) FROM user_profiles WHERE created_at IS NULL")
count = cur.fetchone()[0]

if count > 0:
    print(f"⚠️  Найдено {count} профилей с пустыми created_at/updated_at")
    now_ts = int(datetime.now().timestamp())
    
    cur.execute("""
        UPDATE user_profiles
        SET created_at = ?, updated_at = ?
        WHERE created_at IS NULL OR updated_at IS NULL
    """, (now_ts, now_ts))
    
    conn.commit()
    print("✅ Миграция завершена. Теперь все профили имеют timestamp.")
else:
    print("✅ Все профили уже имеют корректные timestamp.")

conn.close()

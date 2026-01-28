import sqlite3
import os

# ✅ Используем абсолютный путь к корню проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shop.db")

print(f"📂 Путь к БД: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Проверяем структуру user_profiles
cur.execute("PRAGMA table_info(user_profiles)")
columns = [row[1] for row in cur.fetchall()]

print("✅ Колонки user_profiles:", columns)

if "consent_pd" not in columns:
    print("➕ Добавляем consent_pd...")
    cur.execute(
        "ALTER TABLE user_profiles ADD COLUMN consent_pd INTEGER NOT NULL DEFAULT 0"
    )

if "consent_marketing" not in columns:
    print("➕ Добавляем consent_marketing...")
    cur.execute(
        "ALTER TABLE user_profiles ADD COLUMN consent_marketing INTEGER NOT NULL DEFAULT 0"
    )

conn.commit()
print("✅ Миграция завершена.")
conn.close()

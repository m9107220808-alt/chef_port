import sqlite3
import os

# Ищем путь к БД
db_path = "/root/chefport-bot/chefport.db" 
if not os.path.exists(db_path):
    # Попробуем найти в .env
    with open("/root/chefport-bot/.env") as f:
        for line in f:
            if line.startswith("DATABASE_URL"):
                # sqlite+aiosqlite:///./chefport.db -> chefport.db
                part = line.split("///")[-1].strip()
                if part.startswith("./"): part = part[2:]
                db_path = f"/root/chefport-bot/{part}"
                break

print(f"DB Path: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Проверяем колонки
    cur.execute("PRAGMA table_info(products)")
    cols = [r[1] for r in cur.fetchall()]
    print("Columns:", cols)
    
    if "discount_percent" not in cols:
        print("Adding discount_percent...")
        cur.execute("ALTER TABLE products ADD COLUMN discount_percent INTEGER DEFAULT 0")
        conn.commit()
    else:
        print("discount_percent exists")

    if "categoryid" not in cols:
         # Это странно, если его нет, но добавим 
         pass # Мы видели его в логах SELECT
            
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals(): conn.close()

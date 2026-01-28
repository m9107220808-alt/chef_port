import sqlite3

DB_PATH = "shop.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row for row in cur.fetchall()]
print("Таблицы в БД:", tables)

conn.close()

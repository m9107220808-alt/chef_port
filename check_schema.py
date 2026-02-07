import sqlite3

conn = sqlite3.connect('shop.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(products)")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()

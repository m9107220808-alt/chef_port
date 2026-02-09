import sqlite3

def add_discount_column():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_discount' not in columns:
            print("Adding 'is_discount' column...")
            cursor.execute("ALTER TABLE products ADD COLUMN is_discount BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ 'is_discount' added to products.")
        else:
            print("ℹ️ 'is_discount' already exists.")

        # Check categories table
        cursor.execute("PRAGMA table_info(categories)")
        cat_columns = [info[1] for info in cursor.fetchall()]

        if 'image_url' not in cat_columns:
             print("Adding 'image_url' column to categories...")
             cursor.execute("ALTER TABLE categories ADD COLUMN image_url TEXT")
             conn.commit()
             print("✅ 'image_url' added to categories.")
        else:
             print("ℹ️ 'image_url' already exists in categories.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_discount_column()

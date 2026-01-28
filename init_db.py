import sqlite3

def init_database():
    """Создание базы данных и всех таблиц"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    # 1. Таблица категорий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    """)
    
    # 2. Таблица товаров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price_per_kg REAL NOT NULL,
            is_weighted INTEGER DEFAULT 0,
            min_weight_kg REAL DEFAULT 0.5,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    
    # 3. Таблица корзины
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_code TEXT NOT NULL,
            quantity REAL NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 4. Таблица профилей пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            street TEXT NOT NULL,
            house TEXT NOT NULL,
            flat TEXT NOT NULL,
            entrance TEXT,
            floor TEXT,
            delivery_type TEXT DEFAULT 'delivery',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. ✅ НОВАЯ таблица заказов (для checkout)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_number TEXT UNIQUE NOT NULL,
            
            -- Данные клиента
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            
            -- Способ получения
            delivery_method TEXT NOT NULL,
            delivery_address TEXT,
            
            -- Оплата
            payment_method TEXT NOT NULL,
            
            -- Заказ
            items_json TEXT NOT NULL,
            total_amount REAL NOT NULL,
            comment TEXT,
            
            -- Статусы
            status TEXT DEFAULT 'new',
            
            -- Временные метки
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 6. Таблица позиций заказов (оставляем для совместимости)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)
    
    conn.commit()
    print("✅ База данных создана: shop.db")
    
    # Добавляем тестовые данные
    add_sample_data(cursor, conn)
    
    conn.close()


def add_sample_data(cursor, conn):
    """Добавление тестовых категорий и товаров"""
    
    # Проверяем, есть ли уже данные
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] > 0:
        print("⚠️ Данные уже существуют, пропускаем добавление")
        return
    
    # Добавляем категории
    categories = [
        ('fish', 'Рыба', 1),
        ('seafood', 'Морепродукты', 2),
        ('caviar', 'Икра', 3),
        ('frozen', 'Замороженные продукты', 4),
    ]
    
    cursor.executemany("""
        INSERT INTO categories (code, name, sort_order)
        VALUES (?, ?, ?)
    """, categories)
    
    # Добавляем товары
    products = [
        # Рыба (category_id=1)
        (1, 'salmon_fresh', 'Лосось свежий', 850.0, 1, 0.5, 'Свежий охлаждённый лосось'),
        (1, 'trout', 'Форель', 720.0, 1, 0.5, 'Свежая форель'),
        (1, 'seabass', 'Сибас', 680.0, 1, 0.4, 'Охлаждённый сибас'),
        
        # Морепродукты (category_id=2)
        (2, 'shrimp_tiger', 'Креветки тигровые', 1200.0, 1, 0.5, 'Королевские тигровые креветки'),
        (2, 'mussels', 'Мидии', 450.0, 1, 0.5, 'Свежие мидии'),
        (2, 'squid', 'Кальмары', 380.0, 1, 0.5, 'Очищенные кальмары'),
        
        # Икра (category_id=3)
        (3, 'caviar_red', 'Икра красная', 2800.0, 0, 0, 'Икра горбуши, 200г банка'),
        (3, 'caviar_black', 'Икра чёрная', 8500.0, 0, 0, 'Икра осетра, 100г банка'),
        
        # Замороженные (category_id=4)
        (4, 'salmon_frozen', 'Лосось замороженный', 650.0, 1, 1.0, 'Замороженное филе лосося'),
        (4, 'shrimp_frozen', 'Креветки замороженные', 890.0, 1, 0.5, 'Креветки варено-мороженные'),
    ]
    
    cursor.executemany("""
        INSERT INTO products 
        (category_id, code, name, price_per_kg, is_weighted, min_weight_kg, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, products)
    
    conn.commit()
    print("✅ Добавлено тестовых категорий: 4")
    print("✅ Добавлено тестовых товаров: 10")


if __name__ == "__main__":
    init_database()
    print("\n🎉 Инициализация завершена! Теперь запусти: python bot_complete.py")

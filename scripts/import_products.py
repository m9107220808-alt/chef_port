#!/usr/bin/env python3
"""
Импорт товаров Chef Port в PostgreSQL
Категории: Рыба, Морепродукты, Овощи, Соусы, Гарниры
"""
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chefport_user:mA2kDs5jk@localhost:5432/chefport_db")

PRODUCTS = [
    # === РЫБА (Группа A - топ продаж) ===
    {"name": "Филе лосося охлаждённое", "category": "Рыба", "price": 1200.00, "weight": 1.0, 
     "description": "Свежее филе премиум качества из Норвегии", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/FF6B6B/fff?text=Лосось"},

    {"name": "Стейк тунца", "category": "Рыба", "price": 1580.00, "weight": 0.5,
     "description": "Охлаждённый стейк для гриля", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/E17055/fff?text=Тунец"},

    {"name": "Филе дорадо", "category": "Рыба", "price": 890.00, "weight": 0.4,
     "description": "Средиземноморская рыба, идеально для запекания", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/FD79A8/fff?text=Дорадо"},

    {"name": "Сибас целый", "category": "Рыба", "price": 750.00, "weight": 0.6,
     "description": "Свежий сибас для гриля или духовки", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/A29BFE/fff?text=Сибас"},

    # === МОРЕПРОДУКТЫ (Группа A/B) ===
    {"name": "Креветки королевские 16/20", "category": "Морепродукты", "price": 890.00, "weight": 0.5,
     "description": "Замороженные неочищенные, Аргентина", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/4ECDC4/fff?text=Креветки"},

    {"name": "Гребешок морской", "category": "Морепродукты", "price": 1450.00, "weight": 0.3,
     "description": "Очищенный, заморозка -18°C", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/45B7D1/fff?text=Гребешок"},

    {"name": "Мидии в раковине", "category": "Морепродукты", "price": 450.00, "weight": 1.0,
     "description": "Живые мидии, Чёрное море", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/96CEB4/fff?text=Мидии"},

    {"name": "Кальмар тушка", "category": "Морепродукты", "price": 520.00, "weight": 0.5,
     "description": "Очищенный, без головы", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/FFEAA7/fff?text=Кальмар"},

    {"name": "Осьминог варёно-мороженый", "category": "Морепродукты", "price": 780.00, "weight": 1.0,
     "description": "Целая тушка 800-1200г", "abc_group": "C",
     "image_url": "https://via.placeholder.com/400x300/DFE6E9/fff?text=Осьминог"},

    # === ИКРА (Группа B/C) ===
    {"name": "Икра трески", "category": "Икра", "price": 320.00, "weight": 0.25,
     "description": "Охлаждённая, 250г", "abc_group": "C",
     "image_url": "https://via.placeholder.com/400x300/FAB1A0/fff?text=Икра+трески"},

    {"name": "Икра лососевая красная", "category": "Икра", "price": 2500.00, "weight": 0.5,
     "description": "Горбуша, 1 сорт, 500г", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/FF7675/fff?text=Красная+икра"},

    # === ОВОЩИ (для гарнира) ===
    {"name": "Лимон свежий", "category": "Овощи", "price": 80.00, "weight": 0.15,
     "description": "Для подачи с рыбой", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/FDCB6E/fff?text=Лимон"},

    {"name": "Спаржа зелёная", "category": "Овощи", "price": 450.00, "weight": 0.3,
     "description": "Свежая, для гриля", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/00B894/fff?text=Спаржа"},

    {"name": "Овощи гриль микс", "category": "Овощи", "price": 320.00, "weight": 0.5,
     "description": "Цукини, баклажан, перец", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/6C5CE7/fff?text=Овощи+гриль"},

    {"name": "Рукола свежая", "category": "Овощи", "price": 120.00, "weight": 0.1,
     "description": "Для салатов и подачи", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/55EFC4/fff?text=Рукола"},

    # === СОУСЫ ===
    {"name": "Соус терияки", "category": "Соусы", "price": 180.00, "weight": 0.25,
     "description": "Классический японский соус", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/2D3436/fff?text=Терияки"},

    {"name": "Соус тар-тар", "category": "Соусы", "price": 150.00, "weight": 0.2,
     "description": "Для рыбы и морепродуктов", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/B2BEC3/fff?text=Тар-тар"},

    {"name": "Соевый соус премиум", "category": "Соусы", "price": 220.00, "weight": 0.3,
     "description": "Натурально сваренный", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/636E72/fff?text=Соевый"},

    {"name": "Чесночный соус", "category": "Соусы", "price": 140.00, "weight": 0.2,
     "description": "Домашний рецепт", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/DFE6E9/fff?text=Чесночный"},

    # === ГАРНИРЫ ===
    {"name": "Рис жасмин премиум", "category": "Гарниры", "price": 280.00, "weight": 0.5,
     "description": "Тайский рис, 500г", "abc_group": "A",
     "image_url": "https://via.placeholder.com/400x300/F1F2F6/fff?text=Рис"},

    {"name": "Киноа белая", "category": "Гарниры", "price": 420.00, "weight": 0.4,
     "description": "Суперфуд, готовить 15 мин", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/FFEAA7/fff?text=Киноа"},

    {"name": "Картофель молодой", "category": "Гарниры", "price": 150.00, "weight": 0.6,
     "description": "Для запекания с розмарином", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/F3A683/fff?text=Картофель"},

    {"name": "Паста феттучини", "category": "Гарниры", "price": 180.00, "weight": 0.4,
     "description": "Итальянская, 400г", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/FAD390/fff?text=Паста"},

    # === ДОПОЛНИТЕЛЬНО ===
    {"name": "Масло оливковое Extra Virgin", "category": "Масла", "price": 650.00, "weight": 0.5,
     "description": "Испания, первый холодный отжим", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/F8B500/fff?text=Оливковое"},

    {"name": "Специи для рыбы микс", "category": "Специи", "price": 120.00, "weight": 0.05,
     "description": "Лимонный перец, укроп, чеснок", "abc_group": "B",
     "image_url": "https://via.placeholder.com/400x300/6C5CE7/fff?text=Специи"},
]

async def import_products():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("🗑️  Очистка старых товаров...")
        await conn.execute("TRUNCATE products RESTART IDENTITY CASCADE")

        imported = 0
        for p in PRODUCTS:
            await conn.execute("""
                INSERT INTO products (name, description, price, weight, category, image_url, in_stock, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, true, true)
            """, p["name"], p["description"], p["price"], p["weight"], p["category"], p["image_url"])

            print(f"✅ [{p['abc_group']}] {p['category']:15} | {p['name']:40} | {p['price']:7.2f}₽")
            imported += 1

        total = await conn.fetchval("SELECT COUNT(*) FROM products")
        print(f"\n🎉 Импортировано {imported} товаров! Всего в БД: {total}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(import_products())

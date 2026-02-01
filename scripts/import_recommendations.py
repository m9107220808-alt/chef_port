#!/usr/bin/env python3
"""
Импорт рекомендаций товаров (cross-sell)
"С этим товаром покупают"
"""
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chefport_user:mA2kDs5jk@localhost:5432/chefport_db")

# Связки товаров: [товар, рекомендации]
RECOMMENDATIONS = {
    "Филе лосося охлаждённое": [
        "Лимон свежий", "Соус терияки", "Рис жасмин премиум", 
        "Спаржа зелёная", "Масло оливковое Extra Virgin"
    ],
    "Стейк тунца": [
        "Соевый соус премиум", "Овощи гриль микс", "Рукола свежая",
        "Лимон свежий"
    ],
    "Креветки королевские 16/20": [
        "Чесночный соус", "Соус тар-тар", "Лимон свежий",
        "Паста феттучини", "Рукола свежая"
    ],
    "Гребешок морской": [
        "Соус тар-тар", "Лимон свежий", "Рис жасмин премиум",
        "Рукола свежая"
    ],
    "Мидии в раковине": [
        "Чесночный соус", "Лимон свежий", "Паста феттучини"
    ],
    "Кальмар тушка": [
        "Соевый соус премиум", "Овощи гриль микс", "Рис жасмин премиум"
    ],
    "Филе дорадо": [
        "Лимон свежий", "Овощи гриль микс", "Картофель молодой",
        "Масло оливковое Extra Virgin"
    ],
    "Сибас целый": [
        "Лимон свежий", "Спаржа зелёная", "Картофель молодой",
        "Специи для рыбы микс"
    ],
}

async def import_recommendations():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("🗑️  Очистка старых рекомендаций...")
        await conn.execute("TRUNCATE product_recommendations RESTART IDENTITY")

        imported = 0
        for product_name, recommended_names in RECOMMENDATIONS.items():
            # Получаем ID основного товара
            product_id = await conn.fetchval(
                "SELECT id FROM products WHERE name = $1", product_name
            )

            if not product_id:
                print(f"⚠️  Товар не найден: {product_name}")
                continue

            # Добавляем рекомендации
            for rec_name in recommended_names:
                rec_id = await conn.fetchval(
                    "SELECT id FROM products WHERE name = $1", rec_name
                )

                if rec_id:
                    await conn.execute("""
                        INSERT INTO product_recommendations (product_id, recommended_product_id, recommendation_type, priority)
                        VALUES ($1, $2, 'cross-sell', 1)
                        ON CONFLICT DO NOTHING
                    """, product_id, rec_id)
                    imported += 1

            print(f"✅ {product_name:40} → {len(recommended_names)} рекомендаций")

        total = await conn.fetchval("SELECT COUNT(*) FROM product_recommendations")
        print(f"\n🎉 Импортировано {imported} связей! Всего в БД: {total}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(import_recommendations())

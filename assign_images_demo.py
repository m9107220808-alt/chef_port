#!/usr/bin/env python3
"""
Временное решение: присваиваем изображения товарам для демонстрации
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:mA2kDs5jk@localhost:5432/chefport_db"
IMAGES_DIR = "/root/chefport-bot/web/images/products"

def main():
    engine = create_engine(DATABASE_URL)
    
    # Получаем список всех изображений
    images = []
    for filename in os.listdir(IMAGES_DIR):
        if filename.endswith(('.jpg', '.png', '.webp', '.jpeg')):
            images.append(f"/web/images/products/{filename}")
    
    print(f"Найдено {len(images)} изображений")
    
    # Получаем товары и присваиваем изображения
    with engine.connect() as conn:
        products = conn.execute(text("SELECT id FROM products ORDER BY id"))
        product_ids = [row[0] for row in products]
        
        print(f"Найдено {len(product_ids)} товаров")
        
        # Присваиваем изображения по кругу
        for i, product_id in enumerate(product_ids):
            image_url = images[i % len(images)]
            conn.execute(
                text("UPDATE products SET image_url = :img WHERE id = :id"),
                {"img": image_url, "id": product_id}
            )
            conn.commit()
        
        print(f"✅ Обновлено {len(product_ids)} товаров")
        
        # Проверяем результат
        result = conn.execute(text("SELECT COUNT(*) FROM products WHERE image_url IS NOT NULL"))
        count = result.scalar()
        print(f"✅ Товаров с изображениями: {count}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Скрипт для обновления image_url в базе данных на основе файлов в /web/images/
"""
import os
import re
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:mA2kDs5jk@localhost:5432/chefport_db"
IMAGES_DIR = "/root/chefport-bot/web/images"

def normalize_name(name):
    """Нормализует название для сравнения"""
    # Убираем спецсимволы, приводим к нижнему регистру
    name = re.sub(r'[^\w\s]', '', name.lower())
    name = re.sub(r'\s+', '_', name.strip())
    return name

def main():
    engine = create_engine(DATABASE_URL)
    
    # Обновляем категории
    print("=== UPDATING CATEGORIES ===")
    category_images = {
        'икра': '/web/images/category_caviar.png',
        'рыба': '/web/images/category_fish.png',
        'морепродукты': '/web/images/category_seafood.png',
        'свежая рыба': '/web/images/category_fish.png',
        'замороженные': '/web/images/category_seafood.png',
    }
    
    with engine.connect() as conn:
        for keyword, image_path in category_images.items():
            result = conn.execute(
                text("UPDATE categories SET image_url = :img WHERE LOWER(name) LIKE :pattern"),
                {"img": image_path, "pattern": f"%{keyword}%"}
            )
            conn.commit()
            print(f"Updated {result.rowcount} categories matching '{keyword}' with {image_path}")
    
    # Обновляем товары
    print("\n=== UPDATING PRODUCTS ===")
    products_dir = os.path.join(IMAGES_DIR, "products")
    
    if os.path.exists(products_dir):
        # Получаем список всех изображений товаров
        image_files = {}
        for filename in os.listdir(products_dir):
            if filename.endswith(('.jpg', '.png', '.webp')):
                # Извлекаем название из имени файла
                name_part = filename.rsplit('.', 1)[0]
                normalized = normalize_name(name_part)
                image_files[normalized] = f"/web/images/products/{filename}"
        
        print(f"Found {len(image_files)} product images")
        
        # Получаем все товары из БД
        with engine.connect() as conn:
            products = conn.execute(text("SELECT id, name FROM products"))
            updated_count = 0
            
            for product_id, product_name in products:
                normalized_name = normalize_name(product_name)
                
                # Ищем совпадение по названию
                for img_name, img_path in image_files.items():
                    if img_name in normalized_name or normalized_name in img_name:
                        conn.execute(
                            text("UPDATE products SET image_url = :img WHERE id = :id"),
                            {"img": img_path, "id": product_id}
                        )
                        conn.commit()
                        print(f"✓ {product_name} -> {img_path}")
                        updated_count += 1
                        break
            
            print(f"\nUpdated {updated_count} products with images")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()

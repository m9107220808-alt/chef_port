#!/usr/bin/env python3
"""
Улучшенный скрипт для сопоставления изображений с товарами
"""
import os
import re
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:mA2kDs5jk@localhost:5432/chefport_db"
IMAGES_DIR = "/root/chefport-bot/web/images/products"

def clean_name(name):
    """Очищает название для сопоставления"""
    # Убираем все кроме букв и цифр, приводим к нижнему регистру
    name = name.lower()
    name = re.sub(r'[^а-яa-z0-9]', '', name)
    return name

def main():
    engine = create_engine(DATABASE_URL)
    
    # Получаем список изображений
    image_map = {}
    for filename in os.listdir(IMAGES_DIR):
        if filename.endswith(('.jpg', '.png', '.webp')):
            # Извлекаем название без расширения и чисел в конце
            name_part = filename.rsplit('.', 1)[0]
            # Убираем числа в конце (например, _1480)
            name_part = re.sub(r'_\d+$', '', name_part)
            cleaned = clean_name(name_part)
            image_map[cleaned] = f"/web/images/products/{filename}"
    
    print(f"Найдено {len(image_map)} изображений")
    print(f"Примеры очищенных названий: {list(image_map.keys())[:5]}")
    
    # Получаем товары и сопоставляем
    with engine.connect() as conn:
        products = conn.execute(text("SELECT id, name FROM products"))
        updated = 0
        not_found = []
        
        for product_id, product_name in products:
            cleaned_product = clean_name(product_name)
            
            # Ищем точное совпадение
            if cleaned_product in image_map:
                img_path = image_map[cleaned_product]
                conn.execute(
                    text("UPDATE products SET image_url = :img WHERE id = :id"),
                    {"img": img_path, "id": product_id}
                )
                conn.commit()
                print(f"✓ {product_name}")
                updated += 1
            else:
                # Ищем частичное совпадение
                found = False
                for img_name, img_path in image_map.items():
                    if len(cleaned_product) > 5 and cleaned_product in img_name:
                        conn.execute(
                            text("UPDATE products SET image_url = :img WHERE id = :id"),
                            {"img": img_path, "id": product_id}
                        )
                        conn.commit()
                        print(f"✓ {product_name} (частичное)")
                        updated += 1
                        found = True
                        break
                
                if not found:
                    not_found.append(product_name)
        
        print(f"\n✅ Обновлено: {updated}")
        print(f"❌ Не найдено: {len(not_found)}")
        if not_found[:5]:
            print("Примеры не найденных:")
            for name in not_found[:5]:
                print(f"  - {name}")

if __name__ == "__main__":
    main()

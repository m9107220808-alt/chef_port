"""
Скрипт для обновления поля image_url в базе данных
на основе маппинга из product_images.json
"""
import json
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import SessionLocal
from api.models.product import Product


def main():
    print("=" * 70)
    print("💾 ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ: image_url для товаров")
    print("=" * 70)
    print()
    
    # Путь к файлу маппинга
    mapping_file = Path(__file__).parent.parent / "web" / "images" / "products" / "product_images.json"
    
    if not mapping_file.exists():
        print(f"❌ Файл маппинга не найден: {mapping_file}")
        print("   Сначала запустите: python scripts\\create_image_mapping.py")
        return
    
    # Загружаем маппинг
    with open(mapping_file, 'r', encoding='utf-8') as f:
        product_images = json.load(f)
    
    print(f"📝 Загружено записей маппинга: {len(product_images)}")
    print()
    
    # Подключаемся к БД
    db = SessionLocal()
    try:
        # Получаем все товары
        products = db.query(Product).all()
        print(f"📦 Товаров в базе данных: {len(products)}")
        print()
        
        updated = 0
        not_found = 0
        
        print("🔄 Обновление товаров...")
        for product in products:
            if product.name in product_images:
                product.image_url = product_images[product.name]
                updated += 1
                if updated <= 5:  # Показываем первые 5
                    print(f"  ✅ {product.name[:40]:<40} → {product.image_url}")
            else:
                not_found += 1
        
        if updated > 5:
            print(f"  ... и ещё {updated - 5} товаров")
        
        # Сохраняем изменения
        db.commit()
        
        print()
        print(f"📊 Результаты:")
        print(f"  ✅ Обновлено: {updated}")
        print(f"  ❌ Не найдено фото: {not_found}")
        print(f"  📈 Успешность: {updated / len(products) * 100:.1f}%")
        
        print("\n" + "=" * 70)
        print("✅ БАЗА ДАННЫХ ОБНОВЛЕНА!")
        print("\nТеперь можно:")
        print("  1. Запустить сервер: python -m bot.main")
        print("  2. Открыть Mini App и проверить отображение фото")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

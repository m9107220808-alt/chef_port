"""
Скрипт для создания маппинга между названиями товаров и локальными файлами
После скачивания фото из Google Drive
"""
import json
import re
from pathlib import Path

# Пути к файлам
IMAGES_DIR = Path(__file__).parent.parent / "web" / "images" / "products"
PRODUCTS_FILE = Path(__file__).parent.parent / "products_with_photos.json"
OUTPUT_MAPPING = IMAGES_DIR / "product_images.json"


def sanitize_filename(name: str) -> str:
    """Очищает имя файла (такая же логика как в download_photos.py)"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.replace(' ', '_')
    
    translit = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    result = ''
    for char in name.lower():
        result += translit.get(char, char)
    return result[:50]


def find_image_for_product(product_name: str, image_files: list) -> str | None:
    """Ищет файл изображения для товара"""
    # Пробуем точное совпадение по sanitized имени
    sanitized = sanitize_filename(product_name)
    
    for img_file in image_files:
        img_name = img_file.stem.lower()  # имя без расширения
        
        # Точное совпадение
        if img_name == sanitized:
            return f"/images/products/{img_file.name}"
        
        # Частичное совпадение (если название файла содержит sanitized)
        if sanitized in img_name or img_name in sanitized:
            return f"/images/products/{img_file.name}"
    
    return None


def main():
    print("=" * 70)
    print("🗺️ СОЗДАНИЕ МАППИНГА ТОВАРОВ → ФОТОГРАФИИ")
    print("=" * 70)
    print()
    
    # Проверяем наличие папки с фото
    if not IMAGES_DIR.exists():
        print(f"❌ Папка {IMAGES_DIR} не существует!")
        print("   Сначала запустите: python scripts\\download_from_gdrive.py")
        return
    
    # Собираем все изображения
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG']:
        image_files.extend(IMAGES_DIR.glob(f"**/*{ext}"))
    
    print(f"📁 Найдено изображений в папке: {len(image_files)}")
    
    if len(image_files) == 0:
        print("❌ В папке нет изображений!")
        return
    
    # Загружаем данные о товарах
    if not PRODUCTS_FILE.exists():
        print(f"❌ Файл {PRODUCTS_FILE} не найден!")
        return
    
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📦 Загружено товаров из JSON: {len(products)}")
    print()
    
    # Создаём маппинг
    product_images = {}
    matched = 0
    not_matched = 0
    
    print("🔍 Сопоставление товаров с фото...")
    for product in products:
        name = product.get('name', '')
        if not name:
            continue
        
        image_path = find_image_for_product(name, image_files)
        if image_path:
            product_images[name] = image_path
            matched += 1
        else:
            not_matched += 1
    
    print(f"\n📊 Результаты:")
    print(f"  ✅ Найдено соответствий: {matched}")
    print(f"  ❌ Не найдено: {not_matched}")
    print(f"  📈 Успешность: {matched / len(products) * 100:.1f}%")
    
    # Сохраняем маппинг
    with open(OUTPUT_MAPPING, 'w', encoding='utf-8') as f:
        json.dump(product_images, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 Маппинг сохранён: {OUTPUT_MAPPING}")
    
    # Показываем примеры
    print(f"\n✨ Примеры маппинга:")
    for i, (name, path) in enumerate(list(product_images.items())[:5], 1):
        print(f"  {i}. '{name}' → '{path}'")
    
    print("\n" + "=" * 70)
    print("✅ ГОТОВО! Следующий шаг:")
    print("   python scripts\\update_database_images.py")
    print("=" * 70)


if __name__ == "__main__":
    main()

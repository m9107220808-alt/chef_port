"""
Скрипт для скачивания фото товаров с Google Drive
и сохранения их локально
"""
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

# Папка для сохранения изображений
IMAGES_DIR = Path(__file__).parent.parent / "web" / "images"
PRODUCTS_FILE = Path(__file__).parent.parent / "products_with_photos.json"


def extract_gdrive_id(url: str) -> str | None:
    """Извлекает ID файла из Google Drive URL"""
    patterns = [
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
        r'open\?id=([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def download_gdrive_file(file_id: str, output_path: Path) -> bool:
    """Скачивает файл с Google Drive"""
    # URL для прямого скачивания
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
            
            # Проверяем, что это изображение (не HTML ошибка)
            if b'<!DOCTYPE' in content[:100] or b'<html' in content[:100]:
                print(f"  ⚠️ Получен HTML вместо изображения")
                return False
            
            with open(output_path, 'wb') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"  ❌ Ошибка скачивания: {e}")
        return False


def sanitize_filename(name: str) -> str:
    """Очищает имя файла от недопустимых символов"""
    # Заменяем недопустимые символы
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Заменяем пробелы на подчеркивания
    name = name.replace(' ', '_')
    # Транслитерация кириллицы
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
    return result[:50]  # Ограничиваем длину


def main():
    # Создаём папку для изображений
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Папка для изображений: {IMAGES_DIR}")
    
    # Загружаем данные о продуктах
    if not PRODUCTS_FILE.exists():
        print(f"❌ Файл {PRODUCTS_FILE} не найден!")
        return
    
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📦 Найдено {len(products)} товаров")
    
    # Результаты
    downloaded = 0
    failed = 0
    skipped = 0
    
    # Маппинг: имя товара -> локальный файл
    product_images = {}
    
    for product in products:
        name = product.get('name', 'unknown')
        photo_url = product.get('photo_url', '')
        
        if not photo_url:
            print(f"⏭️ {name}: нет фото")
            skipped += 1
            continue
        
        file_id = extract_gdrive_id(photo_url)
        if not file_id:
            print(f"⏭️ {name}: не удалось извлечь ID из URL")
            skipped += 1
            continue
        
        # Генерируем имя файла
        safe_name = sanitize_filename(name)
        output_file = IMAGES_DIR / f"{safe_name}.jpg"
        
        # Проверяем, не скачан ли уже
        if output_file.exists():
            print(f"✅ {name}: уже существует")
            product_images[name] = f"/images/{safe_name}.jpg"
            downloaded += 1
            continue
        
        print(f"⬇️ {name}...")
        if download_gdrive_file(file_id, output_file):
            print(f"  ✅ Сохранено: {output_file.name}")
            product_images[name] = f"/images/{safe_name}.jpg"
            downloaded += 1
        else:
            failed += 1
    
    print(f"\n📊 Результаты:")
    print(f"  ✅ Скачано: {downloaded}")
    print(f"  ❌ Ошибки: {failed}")
    print(f"  ⏭️ Пропущено: {skipped}")
    
    # Сохраняем маппинг
    mapping_file = IMAGES_DIR / "product_images.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(product_images, f, ensure_ascii=False, indent=2)
    print(f"\n📝 Маппинг сохранён: {mapping_file}")


if __name__ == "__main__":
    main()

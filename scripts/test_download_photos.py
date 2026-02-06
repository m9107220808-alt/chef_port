"""
Тестовый скрипт для скачивания первых 10 фото товаров
Проверяет доступность Google Drive перед полным запуском
"""
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

# Папка для сохранения изображений
IMAGES_DIR = Path(__file__).parent.parent / "web" / "images" / "products"
PRODUCTS_FILE = Path(__file__).parent.parent / "products_with_photos.json"
MAX_PRODUCTS = 10  # Тестируем только на 10 товарах


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
            
            # Проверяем размер (должен быть больше 1KB)
            if len(content) < 1024:
                print(f"  ⚠️ Файл слишком маленький ({len(content)} байт)")
                return False
            
            with open(output_path, 'wb') as f:
                f.write(content)
            print(f"  ✅ Сохранено: {output_path.name} ({len(content)} байт)")
            return True
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP ошибка {e.code}: {e.reason}")
        return False
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
    print("🧪 ТЕСТОВЫЙ РЕЖИМ: скачивание первых 10 фото")
    print("=" * 60)
    
    # Создаём папку для изображений
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Папка для изображений: {IMAGES_DIR}")
    
    # Загружаем данные о продуктах
    if not PRODUCTS_FILE.exists():
        print(f"❌ Файл {PRODUCTS_FILE} не найден!")
        return
    
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📦 Всего товаров: {len(products)}")
    print(f"🎯 Тестируем на первых {MAX_PRODUCTS} товарах\n")
    
    # Результаты
    downloaded = 0
    failed = 0
    skipped = 0
    
    # Маппинг: имя товара -> локальный файл
    product_images = {}
    
    for idx, product in enumerate(products[:MAX_PRODUCTS], 1):
        name = product.get('name', 'unknown')
        photo_url = product.get('photo_url', '')
        
        print(f"[{idx}/{MAX_PRODUCTS}] {name}")
        
        if not photo_url:
            print(f"  ⏭️ Нет фото URL")
            skipped += 1
            continue
        
        file_id = extract_gdrive_id(photo_url)
        if not file_id:
            print(f"  ⏭️ Не удалось извлечь ID из URL")
            skipped += 1
            continue
        
        # Генерируем имя файла
        safe_name = sanitize_filename(name)
        output_file = IMAGES_DIR / f"{safe_name}.jpg"
        
        # Проверяем, не скачан ли уже
        if output_file.exists():
            print(f"  ✅ Уже существует")
            product_images[name] = f"/images/products/{safe_name}.jpg"
            downloaded += 1
            continue
        
        if download_gdrive_file(file_id, output_file):
            product_images[name] = f"/images/products/{safe_name}.jpg"
            downloaded += 1
        else:
            failed += 1
        
        print()  # Пустая строка между товарами
    
    print("=" * 60)
    print(f"\n📊 Результаты тестирования:")
    print(f"  ✅ Успешно скачано: {downloaded}")
    print(f"  ❌ Ошибки: {failed}")
    print(f"  ⏭️ Пропущено: {skipped}")
    
    if downloaded > 0:
        # Сохраняем маппинг
        mapping_file = IMAGES_DIR / "product_images_test.json"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(product_images, f, ensure_ascii=False, indent=2)
        print(f"\n📝 Маппинг сохранён: {mapping_file}")
        
    # Выводим рекомендацию
    print("\n" + "=" * 60)
    if failed == 0 and downloaded > 0:
        print("✅ ТЕСТ УСПЕШЕН! Можно запускать полное скачивание.")
        print("Команда: python scripts\\download_photos.py")
    elif failed > 0 and downloaded > 0:
        print(f"⚠️ ЧАСТИЧНЫЙ УСПЕХ: {downloaded} из {downloaded+failed} скачано.")
        print("Рекомендуется проверить ошибки перед полным запуском.")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН! Нужен альтернативный подход:")
        print("  - Проверить права доступа к Google Drive")
        print("  - Использовать библиотеку gdown")
        print("  - Скачать фото вручную ZIP-архивом")


if __name__ == "__main__":
    main()

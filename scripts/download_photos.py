"""
ПОЛНЫЙ СКРИПТ: Скачивание фото → Загрузка в Google Drive
Решение проблемы с фотографиями товаров
"""
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path
import time

# Папка для сохранения изображений
IMAGES_DIR = Path(__file__).parent.parent / "web" / "images" / "products"
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
    # Пробуем разные варианты URL
    urls = [
        f"https://drive.google.com/uc?export=download&id={file_id}",
        f"https://drive.google.com/uc?id={file_id}&export=download",
    ]
    
    for url in urls:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                
                # Проверяем, что это изображение
                if b'<!DOCTYPE' in content[:100] or b'<html' in content[:100]:
                    continue  # Пробуем следующий URL
                
                # Проверяем размер
                if len(content) < 1024:
                    continue
                
                # Сохраняем
                with open(output_path, 'wb') as f:
                    f.write(content)
                return True
                
        except Exception:
            continue
    
    return False


def sanitize_filename(name: str) -> str:
    """Очищает имя файла"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.replace(' ', '_')
    name = name.replace('.', '_')
    
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


def main():
    print("=" * 70)
    print("📸 СКАЧИВАНИЕ ФОТОГРАФИЙ ТОВАРОВ")
    print("=" * 70)
    print()
    
    # Создаём папку
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Папка: {IMAGES_DIR}")
    
    # Загружаем продукты
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📦 Всего товаров: {len(products)}")
    print()
    
    # Результаты
    downloaded = 0
    failed = 0
    skipped = 0
    product_images = {}
    
    print("⬇️ Начинаю скачивание...\n")
    
    for idx, product in enumerate(products, 1):
        name = product.get('name', 'unknown')
        photo_url = product.get('photo_url', '')
        
        # Показываем прогресс каждые 10 товаров
        if idx % 10 == 0:
            print(f"  [{idx}/{len(products)}] Обработано: {downloaded} ✅ | {failed} ❌ | {skipped} ⏭️")
        
        if not photo_url:
            skipped += 1
            continue
        
        file_id = extract_gdrive_id(photo_url)
        if not file_id:
            skipped += 1
            continue
        
        # Генерируем имя файла
        safe_name = sanitize_filename(name)
        output_file = IMAGES_DIR / f"{safe_name}.jpg"
        
        # Проверяем, не скачан ли уже
        if output_file.exists():
            product_images[name] = f"/images/products/{safe_name}.jpg"
            downloaded += 1
            continue
        
        # Скачиваем
        if download_gdrive_file(file_id, output_file):
            product_images[name] = f"/images/products/{safe_name}.jpg"
            downloaded += 1
        else:
            failed += 1
        
        # Небольшая задержка чтобы не перегружать Google Drive
        time.sleep(0.1)
    
    print("\n" + "=" * 70)
    print(f"📊 Результаты:")
    print(f"  ✅ Скачано: {downloaded}")
    print(f"  ❌ Ошибки: {failed}")
    print(f"  ⏭️ Пропущено (нет URL): {skipped}")
    print(f"  📈 Успешность: {downloaded / (len(products) - skipped) * 100:.1f}%" if (len(products) - skipped) > 0 else "")
    
    # Сохраняем маппинг
    if downloaded > 0:
        mapping_file = IMAGES_DIR / "product_images.json"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(product_images, f, ensure_ascii=False, indent=2)
        print(f"\n📝 Маппинг сохранён: {mapping_file}")
    
    print("\n" + "=" * 70)
    
    if downloaded > 0:
        print("✅ СКАЧИВАНИЕ ЗАВЕРШЕНО!\n")
        print("📂 Фотографии находятся в:")
        print(f"   {IMAGES_DIR}\n")
        print("🚀 Следующие шаги:")
        print("   1. Проверьте папку с фото")
        print("   2. Загрузите фото в Google Drive вручную:")
        print("      https://drive.google.com/drive/folders/19DSNmigpdhXl3IU12wfOn2Fmnb0480S5")
        print("   3. Или запустите: python scripts\\update_database_images.py")
        print("      (если хотите использовать локальные фото)")
    else:
        print("❌ НЕ УДАЛОСЬ СКАЧАТЬ ФОТО!")
        print("\nВозможные причины:")
        print("  - Файлы на Google Drive были удалены или перемещены")
        print("  - Нет прав доступа к файлам")
        print("  - Проблемы с интернетом")
    
    print("=" * 70)


if __name__ == "__main__":
    main()

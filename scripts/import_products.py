import pandas as pd
import urllib.request
import os
import time
import re
import json  # ДОБАВЛЕНО ДЛЯ ПРАВИЛЬНОГО JSON

# Конфигурация
EXCEL_FILE = "Заказ ИП Город (2).xlsx"
IMAGES_DIR = "web/images/products"
JSON_OUTPUT = "web/products_data.js" # Сгенерируем JS файл с данными

def download_image(url, filename):
    if not isinstance(url, str) or 'http' not in url:
        return None
    
    # Преобразуем Google Drive ссылки в прямые (для скачивания)
    file_id = None
    if 'drive.google.com' in url:
        if '/d/' in url:
            file_id = url.split('/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
    
    if file_id:
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
    else:
        download_url = url

    try:
        path = os.path.join(IMAGES_DIR, filename)
        if os.path.exists(path):
            return f"/images/products/{filename}"
            
        print(f"Downloading {filename}...")
        # Используем urllib вместо requests
        with urllib.request.urlopen(download_url, timeout=15) as response:
            if response.status == 200:
                with open(path, 'wb') as f:
                    f.write(response.read())
                return f"/images/products/{filename}"
            else:
                print(f"❌ Failed to download {url}: Status {response.status}")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
    return None

def main():
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

    # Читаем данные, пропуская шапку (строка 11 - это индексы 0..10. Значит header=11)
    df = pd.read_excel(EXCEL_FILE, header=11)
    
    # Переименуем колонки по индексам для удобства
    # 0: Category, 1: Name, 2: Unit, 4: Price, 8: Photo
    df.columns = ['Category', 'Name', 'Unit', 'Col3', 'Price', 'Col5', 'Col6', 'Col7', 'Photo', 'Col9', 'Col10']
    
    # Заполняем пустоты в категории (forward fill)
    df['Category'] = df['Category'].ffill()
    
    # Фильтруем пустые строки (где нет названия)
    df = df[df['Name'].notna()]

    products = []
    
    # Маппинг категорий в ID (как у нас в Mini App)
    # У нас было: 1: fish, 2: seafood, 3: caviar, 4: other
    # Нужно понять соответствие.
    # Создадим маппинг на лету или используем эвристику.
    
    category_map = {
        'Рыба': 1,
        'Морепродукты': 2,
        'Икра': 3,
        'Бакалея': 4,
        'Блины': 4, # Бакалея/Полуфабрикаты
        'Блюда фаршированные': 4 # Полуфабрикаты
    }
    
    # Если категории нет в мапе, добавим её в 'other' или попробуем угадать
    
    count = 0
    for i, row in df.iterrows():
        cat_name = str(row['Category']).strip()
        cat_id = category_map.get(cat_name)
        if not cat_id:
            # Простейшая эвристика
            if 'Рыба' in cat_name: cat_id = 1
            elif 'Икра' in cat_name: cat_id = 3
            elif 'Морепродукты' in cat_name or 'Креветки' in cat_name: cat_id = 2
            else: cat_id = 4 # Other / Полуфабрикаты

        name = str(row['Name']).strip()
        price = row['Price']
        unit = str(row['Unit']).strip()
        photo_url = row['Photo']
        
        # Скачивание фото
        local_image = None
        if isinstance(photo_url, str) and 'http' in photo_url:
            # Генерируем простое имя файла на основе ID, чтобы избежать проблем с кодировкой
            filename = f"product_{i + 100}.jpg"
            print(f"[{i+100}] Found photo URL for '{name}': {photo_url}")
            local_image = download_image(photo_url, filename)
            
        is_weighted = unit.lower() in ['кг', 'kg']
        
        products.append({
            'id': i + 100, # Начинаем с 100, чтобы не пересекаться с демо
            'categoryid': cat_id,
            'name': name,
            'priceperkg': float(price) if pd.notnull(price) else 0,
            'is_weighted': is_weighted,
            'is_hit': False, # Пока нет данных о хитах
            'image_url': local_image
        })
        
        count += 1
        # if count > 5: break # Debug limit
        time.sleep(0.5) # Пауза чтобы не забанил гугл

    # Генерируем JS файл, который можно подключить в miniapp_client.html
    # Он заменит DEMO_PRODUCTS
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: используем json.dumps вместо str(products) для правильного JS-синтаксиса
    js_content = f"const IMPORTED_PRODUCTS = {json.dumps(products, ensure_ascii=False, indent=2)};\n"
    
    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Processed {len(products)} products. Data saved to {JSON_OUTPUT}")
    print(f"Images downloaded to {IMAGES_DIR}")

if __name__ == "__main__":
    main()

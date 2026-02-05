import pandas as pd
import json

# Читаем Excel файл
df = pd.read_excel('Заказ ИП Город (2).xlsx', header=None)

# Извлекаем названия товаров (колонка 1) и ссылки на фото (колонка 8)
products = []
for idx, row in df.iterrows():
    if idx < 3:  # Пропускаем заголовки
        continue
    
    name = str(row[1]).strip() if pd.notna(row[1]) else ''
    photo_url = str(row[8]).strip() if pd.notna(row[8]) else ''
    price = row[5] if pd.notna(row[5]) else 0
    
    if name and name != 'nan':
        # Преобразуем Google Drive ссылку в прямую ссылку
        direct_url = ''
        if photo_url and 'drive.google.com' in photo_url:
            # Извлекаем file ID из ссылки
            if '/d/' in photo_url:
                file_id = photo_url.split('/d/')[1].split('/')[0]
                direct_url = f'https://drive.google.com/uc?export=view&id={file_id}'
        
        products.append({
            'name': name,
            'price': int(price) if price else 0,
            'photo_url': direct_url,
            'original_url': photo_url
        })

# Выводим результат в UTF-8
print(f'Найдено {len(products)} товаров с фото:')
for p in products[:30]:
    print(f"  {p['name']}: {p['price']} руб | {p['photo_url'][:60] if p['photo_url'] else 'нет фото'}")

# Сохраняем в JSON
with open('products_with_photos.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f'\nСохранено в products_with_photos.json')

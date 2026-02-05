import pandas as pd
import asyncio
from bot.db_postgres import async_session, engine
from api.models.product import Product
from api.models.category import Category
from sqlalchemy import select, delete

# Настройки наценки (Маржа)
MARGIN_DEFAULT = 1.30  # +30%
MARGIN_CATEGORY = {
    # 'fresh_fish': 1.25, # пример: на свежую рыбу +25%
}

async def import_data():
    print(">> Starting import...")
    
    # 1. Читаем файлы
    print(">> Reading Excel...")
    try:
        df_products = pd.read_excel("Заказ ИП Город (2).xlsx", engine='openpyxl', skiprows=7)
        # Для простоты берем нужные колонки по индексу (так надежнее, если имена кривые)
        # Col 1: Название (B)
        # Col 2: Ед. изм (C)
        # Col 4: Цена закупки (E)
        # Col 8: Ссылка на фото (I)
        
        df_abc = pd.read_excel("АВС анализ продаж.xls", engine='xlrd', skiprows=7)
        # Col 1: Название
        # Col 6: Группа (A/B/C)
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
        return

    # Создаем словарь ABC для быстрого поиска
    abc_map = {}
    for _, row in df_abc.iterrows():
        try:
            name = str(row.iloc[1]).strip()
            group = str(row.iloc[6]).strip()
            if name != 'nan':
                abc_map[name] = group
        except:
            pass
            
    async with async_session() as session:
        # 2. Очистка старых товаров (опционально, но для чистоты лучше)
        # await session.execute(delete(Product))
        # await session.execute(delete(Category))
        # print("🧹 База очищена")

        # 3. Создаем категории (базовые)
        categories = {
            "fish": Category(code="fish", name="Рыба", sort_order=1),
            "seafood": Category(code="seafood", name="Морепродукты", sort_order=2),
            "caviar": Category(code="caviar", name="Икра", sort_order=3),
            "other": Category(code="other", name="Бакалея / Другое", sort_order=10),
        }
        
        # 3. Создаем категории (базовые)
        try:
            categories_to_add = []
            for code, cat in categories.items():
                # Проверяем существование
                res = await session.execute(select(Category).where(Category.code == code))
                if not res.scalar_one_or_none():
                    session.add(cat)
            await session.commit()
        except Exception as e:
            print(f"ERR: Category init failed: {e}")
            await session.rollback()
        
        # Обновляем ID
        cat_ids = {}
        for code, cat in categories.items():
            res = await session.execute(select(Category).where(Category.code == code))
            db_cat = res.scalar_one()
            cat_ids[code] = db_cat.id

        print(">> Importing products...")
        count = 0
        for idx, row in df_products.iterrows():
            try:
                # Используем begin_nested() для изоляции ошибок каждого товара
                async with session.begin_nested():
                    name = str(row.iloc[1]).strip()
                    unit = str(row.iloc[2]).strip()
                    price_buy = row.iloc[4]
                    photo_url = str(row.iloc[8]).strip()
                    
                    if name == 'nan' or not price_buy or str(price_buy) == 'nan':
                        continue

                    # Очистка цены
                    try:
                        if isinstance(price_buy, str):
                            price_buy = float(price_buy.replace(',', '').replace(' ', ''))
                        else:
                            price_buy = float(price_buy)
                    except:
                        continue
                        
                    # Определение категории (по названию)
                    cat_code = "other"
                    name_lower = name.lower()
                    if "икра" in name_lower:
                        cat_code = "caviar"
                    elif any(x in name_lower for x in ["креветк", "краб", "мидии", "кальмар", "гребешок"]):
                        cat_code = "seafood"
                    elif any(x in name_lower for x in ["лосось", "форель", "семга", "палтус", "окунь", "треска", "сибас", "дорадо"]):
                        cat_code = "fish"
                    
                    # Наценка
                    margin = MARGIN_CATEGORY.get(cat_code, MARGIN_DEFAULT)
                    price_sell = round(price_buy * margin, -1) # Округляем до 10
                    
                    # ABC
                    abc_group = abc_map.get(name, "C")
                    is_hit = (abc_group == "A")
                    
                    # Фото
                    if "drive.google.com" in photo_url:
                        pass
                    else:
                        photo_url = None

                    # Весовой?
                    is_weighted = "кг" in str(unit).lower()
                    min_weight = 1.0 if is_weighted else 1.0
                    
                    # Код (транслит или id)
                    # Используем простой код, чтобы не мучиться с транслитом
                    code = f"p_{idx}"
                    
                    # Проверка дублей по имени
                    res = await session.execute(select(Product).where(Product.name == name))
                    existing = res.scalar_one_or_none()
                    
                    if existing:
                        existing.priceperkg = price_sell
                        existing.is_hit = is_hit
                        existing.is_weighted = is_weighted
                        existing.image_url = photo_url
                        # Не меняем категорию, если она уже есть? Или меняем? 
                        # existing.categoryid = cat_ids[cat_code] 
                    else:
                        new_prod = Product(
                            categoryid=cat_ids[cat_code],
                            code=code,
                            name=name,
                            priceperkg=price_sell,
                            is_weighted=is_weighted,
                            min_weight=min_weight,
                            image_url=photo_url,
                            is_hit=is_hit,
                            description=f"Группа: {abc_group}"
                        )
                        session.add(new_prod)
                    
                    count += 1
            except Exception as e:
                # begin_nested() сделает rollback автоматически для этого блока
                print(f"ERR: Row {idx} error: {e}")
                
        await session.commit()
        print(f"DONE: Imported/Updated products: {count}")

if __name__ == "__main__":
    asyncio.run(import_data())

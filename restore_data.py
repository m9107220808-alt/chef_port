import asyncio
import json
import ast
from sqlalchemy import select
from bot.db_postgres import async_session
from api.models.product import Product

async def restore_data():
    print("🚀 Starting Data Restoration...")

    # 1. Load Prices from products_data.js
    print("📖 Reading prices from web/products_data.js...")
    try:
        with open("web/products_data.js", "r", encoding="utf-8") as f:
            content = f.read()
            # Strip "const IMPORTED_PRODUCTS = " and ";"
            content = content.replace("const IMPORTED_PRODUCTS = ", "").replace(";", "")
            # Parse as Python list (since the format looks like Python list of dicts)
            products_with_prices = ast.literal_eval(content)
            print(f"✅ Loaded {len(products_with_prices)} products with prices.")
    except Exception as e:
        print(f"❌ Error reading products_data.js: {e}")
        return

    # 2. Load Photos from products_with_photos.json
    print("📖 Reading photos from products_with_photos.json...")
    try:
        with open("products_with_photos.json", "r", encoding="utf-8") as f:
            products_with_photos = json.load(f)
            print(f"✅ Loaded {len(products_with_photos)} products with photos.")
    except Exception as e:
        print(f"❌ Error reading products_with_photos.json: {e}")
        return

    # 3. Build lookup maps
    price_map = {p['name'].strip(): p['priceperkg'] for p in products_with_prices}
    photo_map = {p['name'].strip(): p['photo_url'] for p in products_with_photos if p.get('photo_url')}
    
    # 4. Update Database
    print("💾 Updating Database...")
    async with async_session() as session:
        result = await session.execute(select(Product))
        db_products = result.scalars().all()
        
        updated_count = 0
        
        for product in db_products:
            name = product.name.strip()
            
            # Update Price
            if name in price_map:
                new_price = price_map[name]
                if new_price > 0:
                    product.priceperkg = new_price
            
            # Update Photo
            if name in photo_map:
                new_photo = photo_map[name]
                if new_photo:
                     # Fix Google Drive links if needed (already handled in frontend but good to store clean)
                    product.image_url = new_photo
            
            # Ensure Active
            product.is_active = True
            
            updated_count += 1
            
        await session.commit()
        print(f"✅ Updated {updated_count} products in Database.")

if __name__ == "__main__":
    asyncio.run(restore_data())

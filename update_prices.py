import asyncio
import ast
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from api.config import settings

def normalize_name(s):
    return s.strip().lower().replace("  ", " ")

async def main():
    # 1. Read the data file
    data_path = "/root/chefport-bot/web/products_data.js"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File {data_path} not found!")
        return

    # 2. Parse content
    start_marker = "const IMPORTED_PRODUCTS = "
    if start_marker in content:
        content = content.split(start_marker)[1].strip()
        if content.endswith(";"):
            content = content[:-1]
    
    try:
        products_data = ast.literal_eval(content)
        print(f"Loaded {len(products_data)} products from {data_path}")
    except Exception as e:
        print(f"Error parsing data: {e}")
        return

    # 3. Connect to DB
    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        updated = 0
        not_found = 0
        
        for p in products_data:
            name = p.get('name')
            price = p.get('priceperkg')
            
            if name and price is not None:
                # Update by NAME
                result = await conn.execute(
                    text("UPDATE products SET priceperkg = :price WHERE name = :name"),
                    {"price": price, "name": name}
                )
                if result.rowcount > 0:
                    updated += result.rowcount
                else:
                    # Try normalized name?
                    # let's try strict first
                    not_found += 1
                    # print(f"Product not found in DB: {name}")
                
    print(f"Finished. Updated prices for {updated} products. Not found: {not_found}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in os.sys.path:
        os.sys.path.append(current_dir)
        
    asyncio.run(main())

import asyncio
import sys
import os

# Добавляем корневую директорию в путь импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from api.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Starting migration...")
        
        # 1. PRODUCTS: Add is_hit column
        try:
            print("Checking products table...")
            await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_hit BOOLEAN DEFAULT FALSE;"))
            print("Added column 'is_hit' to products.")
        except Exception as e:
            print(f"Error updating products: {e}")

        # 2. CATEGORIES: Handle sort_order
        try:
            print("Checking categories table...")
            # Check if sortorder exists to rename it, otherwise just add sort_order
            # But simpler approach: trying to add sort_order. 
            # If sortorder exists, we might want to copy data locally or just ignore.
            # Let's try to rename first if possible, or just add.
            # Postgres supports RENAME COLUMN IF EXISTS in newer versions, but let's be safe.
            
            # Try to rename sortorder -> sort_order
            try:
                await conn.execute(text("ALTER TABLE categories RENAME COLUMN sortorder TO sort_order;"))
                print("Renamed 'sortorder' to 'sort_order' in categories.")
            except Exception as e:
                # If rename failed (maybe sortorder doesn't exist), try adding sort_order
                print(f"Rename failed (probably column doesn't exist): {e}")
                await conn.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;"))
                print("Added column 'sort_order' to categories.")
                
        except Exception as e:
            print(f"Error updating categories: {e}")

        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())

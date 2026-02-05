from sqlalchemy import text
from bot.db_postgres import engine
import asyncio

async def run_migration():
    async with engine.begin() as conn:
        print(">> Adding columns to `products`...")
        try:
            await conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR;"))
            print("OK: Added image_url")
        except Exception as e:
            print(f"WARN: image_url error (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE products ADD COLUMN is_hit BOOLEAN DEFAULT FALSE;"))
            print("OK: Added is_hit")
        except Exception as e:
            print(f"WARN: is_hit error (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE products ADD COLUMN min_weight FLOAT DEFAULT 1.0;"))
            print("OK: Added min_weight")
        except Exception as e:
            print(f"WARN: min_weight error (maybe exists): {e}")

        print(">> Adding columns to `categories`...")
        try:
            await conn.execute(text("ALTER TABLE categories ADD COLUMN image_url VARCHAR;"))
            print("OK: Added image_url to categories")
        except Exception as e:
            print(f"WARN: categories.image_url error (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE categories RENAME COLUMN sortorder TO sort_order;"))
            print("OK: Renamed sortorder -> sort_order")
        except Exception as e:
            print(f"WARN: sort_order rename error: {e}")

        # Rename old columns in products table
        try:
            await conn.execute(text("ALTER TABLE products RENAME COLUMN isweighted TO is_weighted;"))
            print("OK: Renamed isweighted -> is_weighted")
        except Exception as e:
            print(f"WARN: is_weighted rename error: {e}")

        try:
            await conn.execute(text("ALTER TABLE products RENAME COLUMN minweightkg TO min_weight;"))
            print("OK: Renamed minweightkg -> min_weight")
        except Exception as e:
            print(f"WARN: min_weight rename error: {e}")

if __name__ == "__main__":
    asyncio.run(run_migration())

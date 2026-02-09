import asyncio
from sqlalchemy import text
from api.database import AsyncSessionLocal

async def main():
    print("Starting migration...")
    async with AsyncSessionLocal() as db:
         # Use db.begin() for transaction management
        async with db.begin():
            # Update cost_price = priceperkg where cost_price is 0 and priceperkg > 0
            # Explicitly cast to integer if needed, but python handles it.
            # Using text() for raw SQL is fine.
            
            # Count convertible rows
            result = await db.execute(text("SELECT count(*) FROM products WHERE (cost_price IS NULL OR cost_price = 0) AND priceperkg > 0"))
            count = result.scalar()
            print(f"Found {count} products to migrate.")
            
            if count > 0:
                await db.execute(text("UPDATE products SET cost_price = priceperkg WHERE (cost_price IS NULL OR cost_price = 0) AND priceperkg > 0"))
                print(f"Updated cost_price for {count} products.")
            
            # Ensure markup is 0
            await db.execute(text("UPDATE products SET markup = 0 WHERE markup IS NULL"))
            print("Markup set to 0 for NULLs.")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(main())

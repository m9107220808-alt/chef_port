import asyncio
from sqlalchemy import text
from api.database import AsyncSessionLocal

async def main():
    print("Starting cost recalculation...")
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # Update cost_price = priceperkg * 0.75
            # Update markup = 30
            # Only for items with a price
            
            result = await db.execute(text("UPDATE products SET cost_price = priceperkg * 0.75, markup = 30 WHERE priceperkg > 0"))
            print(f"Recalculated costs and markup for {result.rowcount} products.")
            
    print("Recalculation complete.")

if __name__ == "__main__":
    asyncio.run(main())

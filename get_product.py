import asyncio
from sqlalchemy import select
from api.database import async_session
from api.models.product import Product

async def get_one():
    async with async_session() as session:
        result = await session.execute(select(Product).limit(1))
        p = result.scalar_one_or_none()
        if p:
            print(f"ID: {p.id}, Code: {p.code}, Name: {p.name}")
        else:
            print("No products found")

if __name__ == "__main__":
    asyncio.run(get_one())

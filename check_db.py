import asyncio
from sqlalchemy import text
from api.database import async_session

async def check():
    async with async_session() as session:
        # Получаем структуру таблицы products (SQLite)
        result = await session.execute(text("PRAGMA table_info(products)"))
        print(f"{'CID':<5} {'NAME':<15} {'TYPE':<10} {'NOTNULL':<10} {'DFLT':<10} {'PK':<5}")
        for row in result:
            print(f"{row[0]:<5} {row[1]:<15} {row[2]:<10} {row[3]:<10} {row[4]!r:<10} {row[5]:<5}")

if __name__ == "__main__":
    asyncio.run(check())

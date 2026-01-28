from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from api.config import settings

# Создаём движок базы данных
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Логи SQL запросов (для отладки)
    future=True
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()

async def get_db():
    """Получить сессию БД (dependency для FastAPI)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from api.database import Base
from api.models import Category, Product

logger = logging.getLogger(__name__)

SYNC_DATABASE_URL = "postgresql+psycopg2://postgres:mA2kDs5jk@localhost:5432/chefport_db"


engine = create_engine(SYNC_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)


def create_tables_sync():
    Base.metadata.create_all(bind=engine)


def init_demo_catalog_sync():
    session = SessionLocal()
    try:
        categories_count = session.execute(
            select(func.count(Category.id))
        ).scalar_one()
        if categories_count > 0:
            logger.info("Категории уже есть, демо-каталог не инициализируем")
            return

        # Пример демо-данных по аналогии с db.py
        fresh = Category(code="freshfish", name="Свежая рыба", sortorder=1)
        frozen = Category(code="frozen", name="Замороженная рыба", sortorder=2)
        session.add_all([fresh, frozen])
        session.flush()

        products = [
            Product(
                categoryid=fresh.id,
                code="salmon",
                name="Лосось охлаждённый",
                priceperkg=1780,
                isweighted=True,
                minweightkg=0.5,
                description="Свежий лосось, стейки.",
            ),
            Product(
                categoryid=fresh.id,
                code="seabass",
                name="Сибас свежий",
                priceperkg=1300,
                isweighted=True,
                minweightkg=1.0,
                description="Сибас потрошёный.",
            ),
        ]
        session.add_all(products)
        session.commit()
        logger.info("Демо-каталог инициализирован")
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_tables_sync()
    init_demo_catalog_sync()

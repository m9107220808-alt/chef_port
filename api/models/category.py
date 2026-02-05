from sqlalchemy import Column, Integer, String
from api.database import Base


class Category(Base):
    """Категория товаров"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)
    image_url = Column(String, nullable=True)  # Фото категории
    
    def __repr__(self):
        return f"<Category(id={self.id}, code={self.code}, name={self.name})>"

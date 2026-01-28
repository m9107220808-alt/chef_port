from sqlalchemy import Column, Integer, String
from api.database import Base


class Category(Base):
    """Категория товаров"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    sortorder = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Category(id={self.id}, code={self.code}, name={self.name})>"

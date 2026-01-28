from sqlalchemy import Column, Integer, String, Float, Text, Boolean
from api.database import Base


class Product(Base):
    """Модель товара (морепродукты)"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    categoryid = Column(Integer, nullable=False)  # FK на categories
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    priceperkg = Column(Float, nullable=False, default=0)
    weight = Column(Float, default=0)
    description = Column(Text, nullable=True)
    isweighted = Column(Boolean, nullable=False, default=False)
    minweightkg = Column(Float, nullable=False, default=0.1)
    externalid = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<Product(id={self.id}, code={self.code}, name={self.name})>"

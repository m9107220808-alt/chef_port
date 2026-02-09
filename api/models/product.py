from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.sql import func
from api.database import Base


class Product(Base):
    """Модель товара (морепродукты) v1.5"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    categoryid = Column(Integer, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    priceperkg = Column(Float, nullable=False, default=0)
    weight = Column(Float, default=0)
    description = Column(Text, nullable=True)
    isweighted = Column("isweighted", Boolean, nullable=False, default=False)
    minweightkg = Column("minweightkg", Float, nullable=False, default=0.1)
    category = Column(String(100))
    in_stock = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    externalid = Column(String(255), nullable=True)
    
    # v1.5 fields
    is_hit = Column(Boolean, default=False)
    is_discount = Column(Boolean, default=False)
    discount_percent = Column(Integer, default=0)  # NEW: процент скидки
    image_url = Column(String, nullable=True)
    cost_price = Column(Float, default=0)
    markup = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, code={self.code}, name={self.name})>"

from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime
from sqlalchemy.sql import func
from api.database import Base


class Cart(Base):
    """Корзина пользователя"""
    __tablename__ = "cart"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(BigInteger, nullable=False)
    productcode = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    createdat = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Cart(userid={self.userid}, productcode={self.productcode}, qty={self.quantity})>"

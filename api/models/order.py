from sqlalchemy import Column, Integer, BigInteger, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base


class Order(Base):
    """Заказ"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(BigInteger, nullable=False)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    deliverytype = Column(String(20), nullable=True)
    status = Column(String(50), nullable=False, default="new")
    paymentstatus = Column(String(20), nullable=False, default="not_paid")
    paymenttype = Column(String(20), nullable=True)
    total = Column(Integer, nullable=False)
    createdat = Column(DateTime(timezone=True), server_default=func.now())
    updatedat = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, userid={self.userid}, total={self.total})>"


class OrderItem(Base):
    """Позиция заказа"""
    __tablename__ = "orderitems"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    orderid = Column(Integer, ForeignKey("orders.id"), nullable=False)
    productcode = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    weight = Column(String(50), nullable=True)

    order = relationship("Order", back_populates="items")
    
    def __repr__(self):
        return f"<OrderItem(orderid={self.orderid}, name={self.name})>"

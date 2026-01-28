from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from api.database import Base


class OrderHistory(Base):
    """История изменений статуса заказа"""
    __tablename__ = "orderhistory"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    orderid = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    paymentstatus = Column(String(20), nullable=False)
    changedat = Column(DateTime(timezone=True), server_default=func.now())
    changedby = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<OrderHistory(orderid={self.orderid}, status={self.status})>"

from sqlalchemy import Column, Integer, BigInteger
from api.database import Base


class OrderMessage(Base):
    """Связь заказа с сообщением в Telegram"""
    __tablename__ = "ordermessages"
    
    orderid = Column(Integer, primary_key=True)
    userid = Column(BigInteger, nullable=False)
    messageid = Column(Integer, nullable=False)
    chatid = Column(BigInteger, nullable=False)
    
    def __repr__(self):
        return f"<OrderMessage(orderid={self.orderid}, messageid={self.messageid})>"

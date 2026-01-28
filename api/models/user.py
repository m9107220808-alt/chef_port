from sqlalchemy import Column, BigInteger, String, DateTime, Boolean
from sqlalchemy.sql import func
from api.database import Base

class User(Base):
    """Модель пользователя Telegram"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Адрес доставки
    delivery_address = Column(String(500), nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

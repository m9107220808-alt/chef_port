from sqlalchemy import Column, String
from api.database import Base

class ShopSettings(Base):
    """Настройки магазина (дизайн, поведение)"""
    __tablename__ = "shop_settings"
    
    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)
    description = Column(String, nullable=True)

    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value})>"

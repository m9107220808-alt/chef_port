from sqlalchemy import Column, Integer, BigInteger, String, Boolean
from api.database import Base


class UserAddress(Base):
    """Адреса пользователя (несколько адресов на одного пользователя)"""
    __tablename__ = "useraddresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(BigInteger, nullable=False)
    label = Column(String(255), nullable=True)          # Название адреса: "Дом", "Работа"
    address = Column(String(500), nullable=False)       # Полный текст адреса
    isdefault = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<UserAddress(id={self.id}, userid={self.userid}, label={self.label})>"

from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime
from sqlalchemy.sql import func
from api.database import Base


class UserProfile(Base):
    """Профиль пользователя"""
    __tablename__ = "userprofiles"
    
    userid = Column(BigInteger, primary_key=True)
    fullname = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    city = Column(String(255), default="г. Смоленск")
    street = Column(String(500), nullable=True)
    house = Column(String(50), nullable=True)
    flat = Column(String(50), nullable=True)
    entrance = Column(String(50), nullable=True)
    floor = Column(String(50), nullable=True)
    deliverytype = Column(String(20), default="delivery")  # delivery / pickup
    consentpd = Column(Boolean, nullable=False, default=False)
    consentmarketing = Column(Boolean, nullable=False, default=False)
    createdat = Column(DateTime(timezone=True), server_default=func.now())
    updatedat = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserProfile(userid={self.userid}, fullname={self.fullname})>"

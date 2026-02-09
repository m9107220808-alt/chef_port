from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from api.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), index=True)
    sort_order = Column(Integer, default=0)
    icon = Column(String)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    # v1.5 field
    image_url = Column(String, nullable=True)
    
    children = relationship("Category", 
                          backref=backref('parent', remote_side=[id]),
                          cascade="all, delete-orphan")

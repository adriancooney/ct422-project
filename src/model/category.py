from base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String

class Category(Base):
    __tablename__ = "module_category"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String, unique=True)
    modules = relationship("Module", backref="category")
from base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class Module(Base):
    __tablename__ = "module"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)
    category = Column(Integer, ForeignKey('module_category.id'))
    papers = relationship("Paper")
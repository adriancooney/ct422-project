from project.src.model.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class Category(Base):
    __tablename__ = "module_category"

    id = Column(Integer, primary_key=True)
    institution_id = Column(Integer, ForeignKey('institution.id'))
    name = Column(String)
    code = Column(String)
    modules = relationship("Module", backref="category")
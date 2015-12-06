from project.src.model.base import Base
from project.src.model.exception import NotFound
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, String, ForeignKey

class Category(Base):
    __tablename__ = "module_category"

    id = Column(Integer, primary_key=True)
    institution_id = Column(Integer, ForeignKey('institution.id'))
    name = Column(String)
    code = Column(String)
    modules = relationship("Module", backref="category")

    @staticmethod
    def getByCode(session, code):
        try:
            return session.query(Category).filter(Category.code == code.upper()).one()
        except NoResultFound:
            raise NotFound("category", "Category %s not found." % code)
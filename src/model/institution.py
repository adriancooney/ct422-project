from project.src.model.base import Base
from project.src.model.exception import NotFound
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, String

class Institution(Base):
    __tablename__ = "institution"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String, unique=True)
    categories = relationship("Category", backref="institution")

    @staticmethod
    def getByCode(session, code):
        try:
            return session.query(Institution).filter(Institution.code == code.upper()).one()
        except NoResultFound:
            raise NotFound("institution", "Institution %s not found." % code)
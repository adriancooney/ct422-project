from project.src.model.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String

class Institution(Base):
    __tablename__ = "institution"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String, unique=True)
    categories = relationship("Category", backref="institution")

    @staticmethod
    def getByCode(session, code):
        return session.query(Institution).filter(Institution.code == code).one()
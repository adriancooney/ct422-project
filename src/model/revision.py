from datetime import datetime
from project.src.model.base import Base
from project.src.model.exception import NotFound
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime

class Revision(Base):
    __tablename__ = "revision"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'))
    visitor_id = Column(Integer, ForeignKey('visitor.id'))
    visitor = relationship('Visitor', foreign_keys=[visitor_id])
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, visitor, content):
        self.visitor = visitor
        self.content = content

    @staticmethod
    def findById(session, id):
        try:
            return session.query(Revision).filter(Revision.id == id).one()
        except NoResultFound:
            raise NotFound('revision', 'Revision with id %s not found' % id)
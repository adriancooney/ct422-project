from project.src.model.base import Base
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Table
from sqlalchemy.dialects import postgresql

class Similar(Base):
    __tablename__ = 'similar_questions'
    question_id = Column(Integer, ForeignKey('question.id'), primary_key=True)
    similar_question_id = Column(Integer, ForeignKey('question.id'), primary_key=True)
    similarity = Column(Float)
    question = relationship("Question", foreign_keys=similar_question_id)

class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True)
    similar = relationship("Similar", foreign_keys=Similar.question_id)
    parent_id = Column(Integer, ForeignKey('question.id'))
    children = relationship("Question",
        backref=backref('parent', remote_side=[id])
    )

    paper_id = Column(Integer, ForeignKey("paper.id"))
    path = Column(postgresql.ARRAY(Integer))
    pretty_path = Column(postgresql.ARRAY(String))
    content = Column(Text)
    __table_args__ = (UniqueConstraint('paper_id', 'path'),)

    def __init__(self, index):
        self.path = map(lambda i: i.i, index)
        self.pretty_path = map(lambda i: str(i), index)

    def __repr__(self):
        return "<Question(id={}, paper_id={}, path={}, len(content)={}, len(children)={}, len(similar)={})>".format(self.id, self.paper_id, self.path, len(self.content) if self.content else 0, len(self.children), len(self.similar))

    def to_dict(self):
        return {
            'path': self.path,
            'pretty_path': self.pretty_path,
            'content': self.content
        }

    def get_similar(self, threshold=0.4):
        return filter(lambda s: s.similarity > threshold, self.similar)
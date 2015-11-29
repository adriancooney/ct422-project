from base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects import postgresql

class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("paper.id"))
    path = Column(postgresql.ARRAY(Integer))
    pretty_path = Column(postgresql.ARRAY(String))
    content = Column(Text)
    __table_args__ = (UniqueConstraint('paper_id', 'path'),)

    def __init__(self, index):
        self.path = map(lambda i: i.i, index)
        self.pretty_path = map(lambda i: str(i), index)

    def __repr__(self):
        return "<Question(id={}, paper_id={}, path={}, len(content)={})>".format(self.id, self.paper_id, self.path, len(self.content))

    def to_dict(self):
        return {
            'path': self.path,
            'pretty_path': self.pretty_path,
            'content': self.content
        }
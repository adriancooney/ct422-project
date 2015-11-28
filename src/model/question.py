from base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects import postgresql

class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("paper.id"))
    path = Column(postgresql.ARRAY(Integer))
    pretty_path = Column(postgresql.ARRAY(String))
    content = Column(Text)

    def __init__(self, index):
        self.path = map(lambda i: i.i, index)
        self.pretty_path = map(lambda i: str(i), index)
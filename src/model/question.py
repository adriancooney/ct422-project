import project.src.model
from project.src.model.base import Base
from project.src.model.revision import Revision
from project.src.model.exception import NotFound
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
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
    __table_args__ = (UniqueConstraint('paper_id', 'path'),)

    current_revision_id = Column(Integer, ForeignKey('revision.id'))
    revision = relationship("Revision", secondary=Table('question_revision', Base.metadata,
        Column('question_id', Integer, ForeignKey('question.id')),
        Column('revision_id', Integer, ForeignKey('revision.id'))
    ), uselist=False)
    revisions = relationship("Revision", foreign_keys=[Revision.question_id])

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

    def get_similar(self, threshold=None):
        if not threshold:
            threshold = project.src.model.Module.SIMILARITY_THRESHOLD

        return filter(lambda s: s.similarity > threshold and s.question.id != self.id, self.similar)

    @property
    def content(self):
        if self.revision:
            return self.revision.content.replace(u"\uFFFD", '').strip()

    @property
    def joined_path(self):
        return '.'.join(map(str, self.path))
    
    def set_content(self, vistor, content):
        revision = Revision(vistor, content)
        self.revisions.append(revision)
        self.revision = revision

    def is_parent(self, question):
        """Test whether a question is a descendent of self."""
        if question.parent is self:
            return True

        # Compare paths
        if len(self.path) >= question.path:
            # If their path is equal to or shorter than our path
            #  they cannot possible be a descendant
            return False

        if self.path != question.path[len(self.path)]:
            # If the first indices of the path are not
            # the same, this is not a parent
            return False

        return True

    @staticmethod
    def getByPath(session, paper, path):
        try:
            return session.query(Question).filter(
                (Question.paper_id == paper.id) & \
                (Question.path == path)
            ).one()
        except NoResultFound:
            raise NotFound("question", "Question with path %s not found." % '.'.join(map(str, path)))
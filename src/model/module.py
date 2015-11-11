import json
import logging
import itertools
from paper import NoLinkException, UnparseableException, PaperNotFound
from base import Base
from sqlalchemy.orm import relationship, Session
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean

class Module(Base):
    __tablename__ = "module"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey('module_category.id'))
    is_indexed = Column(Boolean, default=False)
    papers = relationship("Paper", backref="module")

    def index(self):
        if self.is_indexed:
            return

        for paper in self.papers:
            try:
                paper.index()
            except NoLinkException:
                logging.info("No link for paper %r" % paper)
            except UnparseableException:
                logging.warning("Unable to parse paper %r" % paper)
            except PaperNotFound:
                logging.warning("Paper %r not found." % paper)

        self.is_indexed = True

        session = Session.object_session(self)
        session.add(self)
        session.commit()

    def to_dict(self):
        data = {}

        # First of all, organize the papers by year
        for paper in self.papers:
            # Skip papers that we couldn't parse
            if not paper.contents:
                continue

            year = str(paper.year_start)

            # We use year start as the key
            if not year in data:
                data[year] = []

            data[year].append(paper.contents)

        return { self.code: data }

    def to_JSON(self):
        return json.dumps(self.to_dict(), indent=4)

    def __repr__(self):
        return "<Module(id={}, code={}, papers={})>".format(self.id, self.code, len(self.papers))

    def count_question(**args):
        pass
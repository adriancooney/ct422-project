import slate
import json
import pycurl
import logging
from os.path import join
from sklearn.feature_extraction.text import CountVectorizer

from base import Base
from parser.parser import Parser, UnparseableException
from paper_pdf import PaperPDF, PaperNotFound
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm.session import Session
from sqlalchemy.dialects.postgresql import JSON

class Paper(Base):
    PAPER_DIR = None

    # ORM
    __tablename__ = "paper"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("module.id"))
    name = Column(String)
    period = Column(String)
    sitting = Column(Integer)
    year_start = Column(Integer)
    year_stop = Column(Integer)
    pdf = relationship("PaperPDF", backref="paper", uselist=False)
    link = Column(String)

    contents = Column(JSON)
    raw_contents = Column(Text)

    def __init__(self, module, name, period, sitting, year_start, year_stop, link, contents, document=None):
        """The Paper class describes a Exam paper.
        
        Here we parse questions and store them in a neat array.
        """

        self.module = module
        self.name = name
        self.period = period
        self.sitting = sitting
        self.year_start = year_start
        self.year_stop = year_stop
        self.link = link
        self.contents = contents

    def index(self):
        """Parse the paper's questions.
        
        This function takes in the parsed PDF document, which is an 
        list of strings, one for each page. We assume the document
        follows the Paper Specification in notebooks/Exam Paper Feature
        Exraction.ipynb.

        Args:
            document (List[str]): The list of pages.
        """
        if not self.link:
            raise NoLinkException("No link attribute on this paper.")

        if not self.PAPER_DIR:
            raise RuntimeError("Paper.PAPER_DIR is not set.")

        session = Session.object_session(self)

        if not self.pdf:
            # Looks like we have no PDF associated with this paper
            self.pdf = PaperPDF(paper_id=self.id)

            # Download it
            self.pdf.download(Paper.PAPER_DIR)

            # Save it's download location to the database
            session.add(self.pdf)
            session.commit()

        try:
            # Get the contents of the PDF
            pages = [unicode(page, errors='replace') for page in self.pdf.get_contents()]
        except:
            # Catch any slate.PDF exceptions and convert them to Unparsable
            raise UnparseableException()

        # Save the raw content
        self.raw_contents = ''.join(pages)

        # Parse the pages contents
        # TODO: Parse first page.
        parsed = Parser.parse_pages(pages[1:])

        # Save the contents
        self.contents = Parser.to_dict(parsed)

        # Add self to commit
        session.add(self)

        # Save to db
        session.commit()

    def __repr__(self):
        return "<Paper(id={id}, {module}, {year_start}/{year_stop}, {sitting}, link={link})>".format(
            id=self.id, module=self.module.code, year_start=self.year_start, year_stop=self.year_stop,
            sitting=self.sitting, link=(self.link != None))

    def get_question(self, *args):
        """Get a questions contents from a paper. If none available, return the nearest estimate
        to question path. All this function really does is smartly traverse the document tree ignoring
        sections and such.

        Args:
            **args: 
                The path to the question (Int..)

                Example: 
                    To get to question 1, (a), ii. you need to convert the indexes to their
                    integer form i.e. 1 = 1, (a) = 1, ii = 2 then pass these ints as arguments.

                    paper.get_question(1, 1, 2)

        Returns:
            str: The content of the question
        """

        if not self.contents:
            return None

        question = None
        children = self.contents["children"]
        path = list(args)

        while path:
            i = path.pop(0)

            try:
                question = children[i]

                if "children" in question:
                    children = question["children"]
            except IndexError:
                break

        return question

    def get_questions(self):
        """This methods returns a list of all the questions in the form of:

            (Paper, (question_path), content)
            (<Paper(id=1)>, (1, 2, 1), "<question document>")"""

        if not self.contents:
            raise RuntimeError("%r has no contents." % self)

        def flatten(question, path=()):
            qs = []

            if "content" in question:
                qs.append((path, question["content"]))

            if "children" in question:
                for i, child in enumerate(question["children"]):
                    qs += flatten(child, path + (i,))

            return qs

        return flatten(self.contents)

    def is_indexed(self):
        return bool(self.contents) or bool(self.pdf)

    def to_dict(self):
        return {
            'id': self.id,
            'years': [self.year_start, self.year_stop],
            'name': self.name,
            'sitting': self.sitting,
            'period': self.period
        }

class NoLinkException(Exception):
    pass
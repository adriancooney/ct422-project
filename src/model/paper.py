import sys
import slate
import json
import pycurl
import logging
import sqlalchemy
import pyparsing as pp
from datetime import datetime
from os.path import join
from sklearn.feature_extraction.text import CountVectorizer

from base import Base
from question import Question
from index import Index
from paper_pdf import PaperPDF, PaperNotFound
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm.session import Session

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

    questions = relationship("Question", backref="paper")
    raw_contents = Column(Text)

    indexed = Column(Boolean)
    indexed_at = Column(DateTime)
    parseable = Column(Boolean)

    # Order by paper period
    order_by_period = sqlalchemy.sql.expression.case(
        ((period == "Winter", 1),
         (period == "Summer", 2),
         (period == "Autumn", 3),
         (period == "Spring", 4))
    )

    def __init__(self, module, name, period, sitting, year_start, year_stop, link):
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

    def index(self):
        """Parse the paper's questions.
        
        This function takes in the parsed PDF document, which is an 
        list of strings, one for each page. We assume the document
        follows the Paper Specification in notebooks/Exam Paper Feature
        Exraction.ipynb.

        Args:
            document (List[str]): The list of pages.
        """
        logging.info("Indexing paper %r" % self)

        self.indexed = True
        self.indexed_at = datetime.utcnow()

        try:
            if not self.pdf:
                # Looks like we have no PDF associated with this paper
                # Download it.
                self.download()

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
            # TODO: Discuss: should we insert questions into the database without content (i.e. just keep the indices)?
            self.questions = filter(lambda q: bool(q.content), Paper.parse_pages(pages[1:]))
        except:
            # Save the indexing information
            self.save()

            # Re-raise
            raise sys.exc_info()

        # If it got this far, it means no UnparseableException has been
        # raised and we've parsed the paper!
        self.parseable = True
        self.save()

    def save(self):
        """Save self to the database"""
        session = Session.object_session(self)
        session.add(self)
        session.commit()

    def download(self):
        """Download the PDF and save it to the database"""

        if not self.link:
            raise NoLinkException("No link attribute on this paper.")

        if not self.PAPER_DIR:
            raise RuntimeError("Paper.PAPER_DIR is not set.")

        self.pdf = PaperPDF(paper_id=self.id)

        # Download it
        self.pdf.download(Paper.PAPER_DIR)

        # Save it's download location to the database
        session = Session.object_session(self)
        session.add(self.pdf)
        session.commit()

    def __repr__(self):
        return "<Paper(id={id}, {module}, {year_start}/{year_stop}, {period}, {sitting}, link={link}{indexed})>".format(
            id=self.id, module=self.module.code, year_start=self.year_start, year_stop=self.year_stop,
            sitting=self.sitting, period=self.period, link=(self.link != None), indexed=(", indexed" if self.is_indexed() else ""))

    def get_question(self, *path):
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

        for question in self.questions:
            if question.path == path:
                return question

    def is_indexed(self):
        """Return whether a paper is indexed or not."""
        return self.indexed

    def to_dict(self):
        return {
            'id': self.id,
            'years': [self.year_start, self.year_stop],
            'name': self.name,
            'sitting': self.sitting,
            'period': self.period
        }

    def get_link(self, module, format=None):
        return "/paper/{}/{}/{}{}".format(
            module.code, self.year_start, self.period.lower(), "." + format if format else "")

    ######################################
    # Paper parser.
    ######################################

    # Let's define our parser
    _ = (pp.White(exact=1) | pp.LineEnd() | pp.LineStart()).suppress()
    __ = pp.White().suppress()
    ___ = pp.Optional(__)
    ____ = pp.Optional(_)

    # Define tokens for numerical, alpha and roman indices
    # Max two digits for numerical indices because lecturers aren't psychopaths
    index_digit = pp.Word(pp.nums, max=2).setParseAction(lambda s, l, t: [Index("decimal", int(t[0]))])("[0-9]") 
    index_alpha = pp.Word(pp.alphas, exact=1).setParseAction(lambda s, l, t: [Index("alpha", t[0])])("[a-z]")
    index_roman = pp.Word("ivx").setParseAction(lambda s, l, t: [Index("roman", t[0])])("[ivx]") # We only support 1-100 roman numerals
    index_type = (index_digit | index_roman | index_alpha)("index")

    # Define token for ("Question" / "Q") + "."
    question = (pp.CaselessLiteral("Question") + pp.Optional("."))("question")

    # Define tokens for formatted indices e.g [a], (1), ii. etc.
    index_dotted = (index_type + pp.Literal(".").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("dotted"))
    index_round_brackets = (pp.Optional(pp.Literal("(")).suppress() + index_type + pp.Literal(")").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("round"))
    index_square_brackets = (pp.Literal("[").suppress() + index_type + pp.Literal("]").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("square"))
    index_question = (pp.Word("qQ", exact=1).suppress() + pp.Optional(".").suppress() + index_type + pp.Optional(".").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("question"))

    # Define final index token with optional Question token before formatted index
    qindex = (
        # Whitespace is required before each index (e.g. "hello world." the d. would be take for an index)
        _ + \
        # Optional "Question." before
        pp.Optional(question + ___).suppress() + \
        # The index
        (index_question | index_dotted | index_round_brackets | index_square_brackets) + \
        # Required whitespace *after* index
        _
    )

    # Define a section header
    section = (pp.CaselessKeyword("Section").suppress() + __ + index_type + _).setParseAction(
        lambda s, l, t: [t[0].section()]
    )("section")

    # Entry point for the parser
    entry = section ^ qindex

    @staticmethod
    def parse_pages(pages):
        """Parse a page in a paper.

        We have a pretty complicated sorting algorithm

        Args:
            page (str): A page within the paper.
        """

        # If were passed in a list of pages, join them together
        if isinstance(pages, list):
            pages = ' '.join([page for page in pages])

        logging.info("Parsing exam paper question pages.")
        logging.info(pages)

        stack = [] # The stack that holds the current index path
        questions = []

        question, last_question, marker = None, None, 0

        # Loop over every token we've parsed from the pages
        for token, start, end in Paper.entry.leaveWhitespace().scanString(pages, overlap=True):
            # Tiny function to push the current question onto the stack
            def push():
                stack.append(index)
                question = Question(stack)
                questions.append(question)
                return question

            index = token[0] # The incoming index

            logging.info("0. Handling index %r" % index)

            # If the container is the paper, just push the question
            if len(stack) == 0:
                logging.info("1. Pushing top level index %r." % index)
                question = push()
                continue

            last_index = stack[-1] # The last index is the last item in the stack

            if index.isSimilar(last_index):
                logging.info("1.1 Similiar indexes %s and previous %s." % (index.index_type, last_index.index_type))

                if last_index.isNext(index):
                    logging.info("1.1.1 Pushing index with same type as last index and in sequence.")
                    stack.pop()
                    question = push()
                else:
                    logging.info("1.1.2 Question with similar indexes but not in sequence, ignoring.")
                    continue
            else:
                logging.info("1.2 Dissimilar indexes %s and previous %s." % (index.index_type, last_index.index_type))
                
                parent_index, n = None, 0

                # Go through the stack and find the similar index
                for i, idx in reversed(list(enumerate(stack))):
                    if idx.isSimilar(index):
                        parent_index, n = idx, i
                        break

                # We need to traverse the stack and see if we can find a similar index
                if parent_index:
                    logging.info("1.2.1 Index similar to parent index %d up the stack [%r]" % (n, parent_index))

                    # If we have found a similar index and they're in sequence, add the question after
                    # the found container.
                    if parent_index.isNext(index):
                        logging.info("1.2.1.1 Index in sequence, pushing into stack.")
                        stack = stack[:n]
                        question = push()
                    else:
                        logging.info("1.2.1.2 Index not in sequence, ignoring")
                        continue

                # If we encounter a new type of index and it's not the start of a new list, we
                # can just discard it (it's probably marks). However if the previous index is 
                # a section, we can just continue. 
                elif index.i == 1 or last_index.is_section: 
                    logging.info("1.2.2 Pushing new question %r." % index )
                    question = push()
                else:
                    logging.info("1.2.3 New index value not first in sequence, ignoring.")
                    continue

            # Save the text
            if last_question != None:
                last_question.content = pages[marker:start]
                last_question = None
                marker = end
            elif marker == 0:
                marker = end

            last_question = question

        # Squeeze out that last part
        if last_question:
            last_question.content = pages[marker:]

        # Test to see if we have any data returned. For now,
        # we'll assume it's "unparsable" if not content if found.
        if not questions:
            raise UnparseableException()

        return questions

    #####################################
    # SQL methods
    #####################################
    
    @staticmethod
    def getById(session, id):
        return session.query(Paper).filter(Paper.id == id).one()

class InvalidPathException(Exception):
    pass

class NoLinkException(Exception):
    pass

class UnparseableException(Exception):
    pass
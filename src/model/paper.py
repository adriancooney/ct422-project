import slate
import json
import pycurl
from os.path import join

from base import Base
from parser.parser import Parser
from paper_pdf import PaperPDF
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm.session import Session
from sqlalchemy.dialects.postgresql import JSON

class Paper(Base):
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

        if document != None:
            self.parse(document)

    def parse(self, document):
        """Parse the paper's questions.
        
        This function takes in the parsed PDF document, which is an 
        list of strings, one for each page. We assume the document
        follows the Paper Specification in notebooks/Exam Paper Feature
        Exraction.ipynb.

        Args:
            document (List[str]): The list of pages.
        """
        # Parse the front page
        # Paper.parse_front_page(document[0])

        # Parse the rest of the pages
        self.raw_content = Parser.parse_pages(document[1:])
        self.contents = Parser.to_dict(self.raw_content)
   

    def download(self, path):
        """Downloads the paper to disk and returns the PaperPDF object"""
        if self.pdf:
            return self.pdf

        if self.link is None:
            raise ValueError("No link attribute on this paper.")

        filename = self.get_filename()
        filepath = join(path, filename)

        with open(filepath, 'wb') as pdf_file:
            c = pycurl.Curl()
            c.setopt(c.URL, self.link)
            c.setopt(c.WRITEDATA, pdf_file)
            c.perform()
            c.close()

        session = Session.object_session(self)

        if session:
            # Save the downloaded pdf to the database
            self.pdf = PaperPDF(path=filepath, paper_id=self.id)
            session.add(self)
            session.commit()

        return self.pdf

    def download_and_parse(self, path):
        """Download and parse the PDF file."""
        download = self.download(path)

        with open(download.path) as pdf:
            contents = slate.PDF(pdf)

            self.parse(contents)

            session = Session.object_session(self)

            if session:
                session.add(self)
                session.commit()


    period_map = {
        'Semester 1': 'Sem-1',
        'Autumn': 'Autumn',
        'Spring': 'Spring',
        'Winter': 'Winter',
        'Summer Repeats/Resits': 'Summer-Repeat',
        'Summer': 'Summer'
    }

    def get_filename(self):
        """Return a filename for the PDF.

        Returns:
            filename (string) e.g. CT422-1-2013-2014-1-2.pdf"""

        return "-".join([
            str(self.module.code),
            str(self.year_start),
            str(self.year_stop),
            str(self.sitting),
            Paper.period_map[self.period]]
        ) + ".pdf"

    def __repr__(self):
        return "<Paper(id={id}, {module}, {year_start}/{year_stop}, {sitting}, link={link})>".format(
            id=self.id, module=self.module.code, year_start=self.year_start, year_stop=self.year_stop,
            sitting=self.sitting, link=(self.link != None))
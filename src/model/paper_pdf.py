import pycurl
import slate
from httplib import InvalidURL
from project.src.model.base import Base
from os.path import join
from sqlalchemy import Column, Integer, String, ForeignKey

class PaperPDF(Base):
    __tablename__ = "paper_download"

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)
    paper_id = Column(Integer, ForeignKey("paper.id"), unique=True)

    def download(self, path):
        """Downloads the paper to disk and returns the PaperPDF object"""

        self.path = join(path, self.get_filename())

        # Download the file with pycurl
        with open(self.path, 'wb') as pdf_file:
            c = pycurl.Curl()
            c.setopt(c.URL, self.paper.link)
            c.setopt(c.WRITEDATA, pdf_file)
            c.perform()

            code = c.getinfo(pycurl.HTTP_CODE)
            c.close()

            if code != 200:
                raise PaperNotFound()

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
            str(self.paper.module.code),
            str(self.paper.year_start),
            str(self.paper.year_stop),
            str(self.paper.sitting),
            PaperPDF.period_map[self.paper.period]]
        ) + ".pdf"

    def get_contents(self):
        print self.path

        """Get the contents of the PDF. See slate.PDF for return values."""
        with open(self.path) as pdf:
            return slate.PDF(pdf)

class PaperNotFound(Exception):
    pass
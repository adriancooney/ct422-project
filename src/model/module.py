from base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class Module(Base):
    __tablename__ = "module"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey('module_category.id'))
    papers = relationship("Paper", backref="module")

    def download_papers(self, path):
        papers = []
        for paper in self.papers:
            try:
                papers.append(paper.download(path))
            except ValueError:
                # Ignore papers who don't have links
                pass

        return papers

    # def build_index(self):
        # for paper in self.papers:
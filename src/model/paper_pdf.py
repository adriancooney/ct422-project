from base import Base
from sqlalchemy import Column, Integer, String, ForeignKey

class PaperPDF(Base):
    __tablename__ = "paper_download"

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)
    paper_id = Column(Integer, ForeignKey("paper.id"), unique=True)
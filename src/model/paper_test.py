from . import Paper
from ..config import Session

# Grab a paper
session = Session()
paper = session.query(Paper).filter(Paper.id == 3907).first()

def test_index():
    Paper.PAPER_DIR = "/tmp"

    paper.index()
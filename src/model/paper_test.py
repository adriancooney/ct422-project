from . import Paper
from ..config import Session

# Grab a paper
session = Session()

# def test_index():
#     paper = session.query(Paper).filter(Paper.id == 3907).first()

#     Paper.PAPER_DIR = "/tmp"

#     paper.index()

def test_feature_extraction():
    paper = session.query(Paper).filter(Paper.id == 3720).first()

    paper.vectorize()
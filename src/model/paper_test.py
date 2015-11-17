from . import Paper
from ..config import Session

# Grab a paper
session = Session()

# def test_index():
#     paper = session.query(Paper).filter(Paper.id == 3907).first()

#     Paper.PAPER_DIR = "/tmp"

#     paper.index()

# def test_get_question():
#     paper = session.query(Paper).filter(Paper.id == 3907).first()

#     print paper.get_question(0, 0)

def test_get_questions():
    paper = session.query(Paper).filter(Paper.id == 3907).first()

    print paper.get_questions()
import random
from . import Module, Paper
from ..config import Session

session = Session()

# def test_module_download():
#     Paper.PAPER_DIR = "/tmp/ct422"
#     ct422 = session.query(Module).filter(Module.code == "CT422-1").one()
#     papers = ct422.index()

#     print ct422.to_JSON()

def test_vectorize():
    ct422 = session.query(Module).filter(Module.code == "CT422-1").one()
    
    # Find paper
    random.seed(100)
    paper = filter(lambda paper: paper.contents, ct422.papers)[0]
    questions = paper.get_questions()
    question = random.choice(questions)[0]

    print ct422.find_similar_questions(paper, question)



import random
import json
from . import Module, Paper
from ..config import Session

session = Session()

# def test_module_download():
#     Paper.PAPER_DIR = "/tmp/ct422"
#     ct422 = session.query(Module).filter(Module.code == "CT422-1").one()
#     papers = ct422.index(force=True)

# def test_find_similar():
#     ct422 = session.query(Module).filter(Module.code == "CT422-1").one()
    
#     # Find paper
#     random.seed(100)
#     paper = filter(lambda paper: paper.contents, ct422.papers)[0]
#     questions = paper.get_questions()
#     question = random.choice(questions)[0]

#     print ct422.find_similar_questions(paper, question).index 

# def test_analysis():
#     ct422 = session.query(Module).filter(Module.code == "CT422-1").one()

#     paper = filter(lambda paper: paper.contents, ct422.papers)[0]

#     print json.dumps(ct422.similarity_analysis(paper))

# def test_analysis():
#     ct422 = session.query(Module).filter(Module.code == "CT422-1").one()

#     print ct422.latest_similarity_analysis(groupByYear=True)

def test_popular():
    ct422 = session.query(Module).filter(Module.code == "CT422-1").one()

    print ct422.find_most_popular_questions().head(50).to_dict(orient="records")
# def test_get_questions():
#     ct422 = session.query(Module).filter(Module.code == "CT422-1").one()

#     print ct422.papers[3].get_questions()

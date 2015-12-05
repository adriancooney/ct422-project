from project.src.config import Session
from project.src.model import Index
from project.src.model.question import Question, Similar

session = Session()

def test_similar():
    a = Question([Index("decimal", 1)])
    b = Question([Index("decimal", 2)])
    s = Similar(similarity=0.5)
    s.question = b
    a.similar.append(s)

    session.add(a)
    session.commit()

    q = session.query(Question).filter(Question.id == a.id).one()

    print q.similar[0].question, b.id
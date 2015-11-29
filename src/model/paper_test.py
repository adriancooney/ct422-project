import slate
import logging
import os
from pytest import raises
from paper import Paper, UnparseableException
from ..config import Session

logging.basicConfig(level=logging.DEBUG)

# Grab a paper
session = Session()

# def index_string(questions): return ','.join(['.'.join(question.pretty_path) for question in questions])

# def test_from_pdf():
#     tests = [
#         ("../../data/2014_2015_CT422_1_1_5.PDF", "1,1.a,1.b,1.c,2,2.a,2.b,2.c,3,3.a,3.b,3.c,4,4.a,4.b,4.c"),
#         ("../../data/2014_2015_CH140_1_1_5.PDF", "A,A.1,A.1.i,A.1.i.a,A.1.i.b,A.1.i.c,A.1.i.d,A.1.i.e,A.1.ii,A.1.ii.a,A.1.ii.b,A.1.ii.c,A.1.ii.d,A.1.ii.e,A.1.iii,A.1.iii.a,A.1.iii.b,A.1.iii.c,A.1.iii.d,A.1.iv,A.1.iv.a,A.1.iv.b,A.1.iv.c,A.1.iv.d,A.1.iv.e,A.1.v,A.1.v.a,A.1.v.b,A.1.v.c,A.1.v.d,A.1.vi,A.1.vi.a,A.1.vi.b,A.1.vi.c,A.1.vi.d,A.1.vii,A.1.vii.a,A.1.vii.b,A.1.vii.c,A.1.vii.d,A.1.viii,A.1.viii.a,A.1.viii.b,A.1.viii.c,A.1.viii.d,A.1.ix,A.1.ix.a,A.1.ix.b,A.1.ix.c,A.1.ix.d,A.1.x,A.1.x.a,A.1.x.b,A.1.x.c,A.1.x.d,A.1.xi,A.1.xi.a,A.1.xi.b,A.1.xi.c,A.1.xi.d,A.1.xii,A.1.xii.a,A.1.xii.b,A.1.xii.c,A.1.xii.d,A.2,A.2.i,A.2.ii,A.2.iii,A.2.iii.a,A.2.iii.b,A.2.iii.c,A.2.iii.d,A.2.iv,A.3,A.3.i,A.3.ii,A.3.iii,A.3.iv,A.3.v,A.4,A.4.i,A.4.ii,A.4.ii.a,A.4.ii.b,A.4.ii.c,A.4.ii.d,A.4.iii"),
#         ("../../data/2014_2015_CT420_1_1_2.PDF", "A,A.1,A.1.i,A.1.ii,A.1.iii,A.1.iv,A.2,A.2.i,A.2.ii,A.2.iii,A.3,A.3.i,A.3.ii,B,B.4,B.4.i,B.4.i.a,B.4.i.b,B.4.i.c,B.4.i.d,B.4.i.e,B.4.ii,B.4.iii,B.4.iv,B.5,B.5.i,B.5.ii,B.5.ii.a,B.5.ii.b,B.5.ii.c,B.5.iii,B.5.iv,B.6,B.6.i,B.6.ii,B.6.iii,B.6.iv"),
#         ("../../data/CT422-1-2014-2015-2-Autumn.pdf", "1,1.i,1.ii,1.iii,2,2.i,2.ii,2.iii,3,3.i,3.ii,3.iii,4,4.i,4.ii")
#     ]

#     for paper_path, expected in tests:
#         full_paper_path = os.path.join(os.path.dirname(__file__), paper_path)
#         with open(full_paper_path) as pdf:
#             pages = slate.PDF(pdf)

#             questions = Paper.parse_pages(pages[1:])

#             index = index_string(questions)

#             print "Paper: %s == '%s'" % (os.path.basename(paper_path), index)
#             assert index == expected

# def test_unparsable():
#     with raises(UnparseableException):
#         with open(os.path.join(os.path.dirname(__file__), "../../data/CT422-1-2013-2014-2-Autumn.pdf")) as pdf:
#             pages = slate.PDF(pdf)
#             Paper.parse_pages(pages[1:])

# def test_index():
#     Paper.index.parseString("1.")
#     Paper.index.parseString("(1)")
#     Paper.index.parseString("[1]")
#     Paper.index.parseString("(a)")
#     Paper.index.parseString("a.")
#     Paper.index.parseString("[a]")

#     assert Paper.index.parseString("i.")[0].i == 1
#     assert Paper.index.parseString("ii.")[0].i == 2
#     assert Paper.index.parseString("iv.")[0].i == 4

# def test_parser_section():
#     Paper.section.leaveWhitespace().parseString("Section 1 ")

def test_index():
    paper = session.query(Paper).filter(Paper.id == 3878).first()

    Paper.PAPER_DIR = "/tmp"
    print paper

    paper.index()

# def test_get_question():
#     paper = session.query(Paper).filter(Paper.id == 3907).first()

#     print paper.get_question(0, 0)

# def test_get_questions():
#     paper = session.query(Paper).filter(Paper.id == 3907).first()

#     print paper.get_questions()
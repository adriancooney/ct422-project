from pytest import raises
from parser import Parser, UnparseableException
from .. import Paper, Module, PaperPDF
from ...config import Session
import logging
import os
import slate

# logging.basicConfig(level=logging.DEBUG)

# Grab a paper
session = Session()
paper = session.query(Paper).filter(
    (Paper.link != None) & \
    (Paper.module_id == Module.id) & \
    (Module.code.like("CT422%"))
).first()

def test_index():
    Parser.index.parseString("1.")
    Parser.index.parseString("(1)")
    Parser.index.parseString("[1]")
    Parser.index.parseString("(a)")
    Parser.index.parseString("a.")
    Parser.index.parseString("[a]")

    assert Parser.index.parseString("i.")[0].i == 1
    assert Parser.index.parseString("ii.")[0].i == 2
    assert Parser.index.parseString("iv.")[0].i == 4

def test_parser_section():
    Parser.section.leaveWhitespace().parseString("Section 1 ")

def test_from_pdf():
    tests = [
        ("../../../data/2014_2015_CT422_1_1_5.PDF", "1,>a,>b,>c,2,>a,>b,>c,3,>a,>b,>c,4,>a,>b,>c,"),
        ("../../../data/2014_2015_CH140_1_1_5.PDF", "sa,>1,>>i,>>>a,>>>b,>>>c,>>>d,>>>e,>>ii,>>>a,>>>b,>>>c,>>>d,>>>e,>>iii,>>>a,>>>b,>>>c,>>>d,>>iv,>>>a,>>>b,>>>c,>>>d,>>>e,>>v,>>>a,>>>b,>>>c,>>>d,>>vi,>>>a,>>>b,>>>c,>>>d,>>vii,>>>a,>>>b,>>>c,>>>d,>>viii,>>>a,>>>b,>>>c,>>>d,>>ix,>>>a,>>>b,>>>c,>>>d,>>x,>>>a,>>>b,>>>c,>>>d,>>xi,>>>a,>>>b,>>>c,>>>d,>>xii,>>>a,>>>b,>>>c,>>>d,>2,>>i,>>ii,>>iii,>>>a,>>>b,>>>c,>>>d,>>iv,>3,>>i,>>ii,>>iii,>>iv,>>v,>4,>>i,>>ii,>>>a,>>>b,>>>c,>>>d,>>iii,"),
        ("../../../data/2014_2015_CT420_1_1_2.PDF", "sa,>1,>>i,>>ii,>>iii,>>iv,>2,>>i,>>ii,>>iii,>3,>>i,>>ii,sb,>4,>>i,>>>a,>>>b,>>>c,>>>d,>>>e,>>ii,>>iii,>>iv,>5,>>i,>>ii,>>>a,>>>b,>>>c,>>iii,>>iv,>6,>>i,>>ii,>>iii,>>iv,"),
        ("../../../data/CT422-1-2014-2015-2-Autumn.pdf", "1,>i,>ii,>iii,2,>i,>ii,>iii,3,>i,>ii,>iii,4,>i,>ii,")
    ]

    for paper_path, expected in tests:
        full_paper_path = os.path.join(os.path.dirname(__file__), paper_path)
        with open(full_paper_path) as pdf:
            pages = slate.PDF(pdf)
            parsed = Parser.parse_pages(pages[1:])
            index = Parser.to_tree_string(parsed, compact=True, tab=">")
            print "Paper: %s == '%s'" % (os.path.basename(paper_path), index)
            assert index == expected

def test_unparsable():
    with raises(UnparseableException):
        with open(os.path.join(os.path.dirname(__file__), "../../../data/CT422-1-2013-2014-2-Autumn.pdf")) as pdf:
            pages = slate.PDF(pdf)
            Parser.parse_pages(pages[1:])
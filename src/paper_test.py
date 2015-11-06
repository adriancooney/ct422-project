from paper import Paper
import logging
import os

logging.basicConfig(level=logging.DEBUG)

EXAMPLE_PAPER_1 = os.path.join(os.path.dirname(__file__), "../data/2014_2015_CT422_1_1_5.PDF")
EXAMPLE_PAPER_2 = os.path.join(os.path.dirname(__file__), "../data/2014_2015_CH140_1_1_5.PDF")


def test_index():
    Paper.index.parseString("1.")
    Paper.index.parseString("(1)")
    Paper.index.parseString("[1]")
    Paper.index.parseString("(a)")
    Paper.index.parseString("a.")
    Paper.index.parseString("[a]")

    assert Paper.index.parseString("i.")[0].i == 1
    assert Paper.index.parseString("ii.")[0].i == 2
    assert Paper.index.parseString("iv.")[0].i == 4

def test_parser_section():
    Paper.section.leaveWhitespace().parseString("Section 1 ")

def test_from_pdf():
    paper = Paper.from_pdf(EXAMPLE_PAPER_1)

    print "Paper: %s == '%s'" % (os.path.basename(EXAMPLE_PAPER_1), paper.to_string(compact=True, tab=">"))
    assert paper.to_string(compact=True, tab=">") == "1,>a,>b,>c,2,>a,>b,>c,3,>a,>b,>c,4,>a,>b,>c,"


    paper = Paper.from_pdf(EXAMPLE_PAPER_2)
    print "Paper: %s == '%s'" % (os.path.basename(EXAMPLE_PAPER_2), paper.to_string(compact=True, tab=">"))
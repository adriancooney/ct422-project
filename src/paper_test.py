from paper import Paper
import logging
import os

logging.basicConfig(level=logging.DEBUG)

EXAMPLE_PAPER_1 = os.path.join(os.path.dirname(__file__), "../data/2014_2015_CT422_1_1_5.PDF")
EXAMPLE_PAPER_2 = os.path.join(os.path.dirname(__file__), "../data/2014_2015_CH140_1_1_5.PDF")
EXAMPLE_PAPER_3 = os.path.join(os.path.dirname(__file__), "../data/2014_2015_CT420_1_1_2.PDF")

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
    index = paper.to_string(compact=True, tab=">")
    print "Paper: %s == '%s'" % (os.path.basename(EXAMPLE_PAPER_1), index)
    assert index == "1,>a,>b,>c,2,>a,>b,>c,3,>a,>b,>c,4,>a,>b,>c,"

    paper = Paper.from_pdf(EXAMPLE_PAPER_2)
    index = paper.to_string(compact=True, tab=">")
    print "Paper: %s == '%s'" % (os.path.basename(EXAMPLE_PAPER_2), index)
    assert index == "sa,>1,>>i,>>>a,>>>b,>>>c,>>>d,>>>e,>>ii,>>>a,>>>b,>>>c,>>>d,>>>e,>>iii,>>>a,>>>b,>>>c,>>>d,>>iv,>>>a,>>>b,>>>c,>>>d,>>>e,>>v,>>>a,>>>b,>>>c,>>>d,>>vi,>>>a,>>>b,>>>c,>>>d,>>vii,>>>a,>>>b,>>>c,>>>d,>>viii,>>>a,>>>b,>>>c,>>>d,>>ix,>>>a,>>>b,>>>c,>>>d,>>x,>>>a,>>>b,>>>c,>>>d,>>xi,>>>a,>>>b,>>>c,>>>d,>>xii,>>>a,>>>b,>>>c,>>>d,>2,>>i,>>ii,>>iii,>>>a,>>>b,>>>c,>>>d,>>iv,>3,>>i,>>ii,>>iii,>>iv,>>v,>4,>>i,>>ii,>>>a,>>>b,>>>c,>>>d,>>iii,"

    paper = Paper.from_pdf(EXAMPLE_PAPER_3)
    index = paper.to_string(compact=True, tab=">")
    print "Paper: %s == '%s'" % (os.path.basename(EXAMPLE_PAPER_2), index)
    assert index == "sa,>1,>>i,>>ii,>>iii,>>iv,>2,>>i,>>ii,>>iii,>3,>>i,>>ii,sb,>4,>>a,>>b,>>c,>>d,>>e,>5,>>i,>>ii,>>>a,>>>b,>>>c,>>iii,>>iv,>6,"
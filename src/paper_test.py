from paper import Paper
import logging

logging.basicConfig(level=logging.DEBUG)

EXAMPLE_PAPER = "../data/2014_2015_CT422_1_1_5.PDF"

def test_from_pdf():
    paper = Paper.from_pdf(EXAMPLE_PAPER)
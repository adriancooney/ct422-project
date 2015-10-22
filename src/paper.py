import slate
import logging
import pyparsing as pp
from index import Index


class Paper:
    __ = pp.White().suppress()
    _ = pp.White(exact=1).suppress()
    ___ = pp.Optional(__)

    # Define tokens for numerical, alpha and roman indices
    index_digit = pp.Word(pp.nums).setParseAction(lambda s, l, t: [Index("decimal", int(t[0]))]).setName("[0-9]")
    index_alpha = pp.Word(pp.alphas, exact=1).setParseAction(lambda s, l, t: [Index("alpha", t[0])]).setName("[a-z]")
    index_roman = pp.Word("ivx").setParseAction(lambda s, l, t: [Index("roman", t[0])]).setName("[ivx]") # We only support 1-100 roman numerals
    index_type = index_digit | index_roman | index_alpha
    index_type.setName("index")

    # Define token for ("Question" / "Q") + "."
    question = (pp.CaselessLiteral("Question") | pp.Word("qQ")) + pp.Optional(".")
    question.setName("question")

    # Define tokens for formatted indices e.g [a], (1), ii. etc.
    index_dotted = (index_type + ".").setParseAction(lambda s, l, t: [t[0]])
    index_round_brackets = ("(" + index_type + ")").setParseAction(lambda s, l, t: [t[1]])
    index_square_brackets = ("[" + index_type + "]").setParseAction(lambda s, l, t: [t[1]])

    # Define final index token with optional Question token before formatted index
    index = _ + pp.Optional(question + ___).suppress() + (index_dotted | index_round_brackets | index_square_brackets) + _

    # Define a section header
    section = (pp.CaselessLiteral("Section").suppress() + __ + index_type).setParseAction(lambda s, l, t: [Section(t[0])]).setName("section")
        
    entry = (section ^ index).leaveWhitespace()

    def __init__(self, document=None):
        """The Paper class describes a Exam paper.
        
        Here we parse questions and store them in a neat array.
        """
        self.questions = []

        if document != None:
            self.parse(document)

    def parse(self, document):
        """Parse the paper's questions.
        
        This function takes in the parsed PDF document, which is an 
        list of strings, one for each page. We assume the document
        follows the Paper Specification in notebooks/Exam Paper Feature
        Exraction.ipynb.

        Args:
            document (List[str]): The list of pages.
        """
        # Parse the front page
        self.parse_front_page(document[0])

        # Parse the rest of the pages
        self.parse_pages(document[1:])

    def parse_front_page(self, front_page):
        """Parse the front page of a paper.

        Args:
            front_page (str): The front page of a paper.
        """

        logging.info("Parsing front page of \"%s\".." % front_page[:30])

    def parse_pages(self, pages):
        """Parse a page in a paper.

        Args:
            page (str): A page within the paper.
        """

        if isinstance(pages, list):
            pages = ' '.join([page for page in pages])

        stack = []

        print pages

        for token, u, v in Paper.entry.scanString(pages):
            print token

    @staticmethod
    def from_pdf(path):
        """Parse a paper from a PDF.

        Args:
            path (str): The path to the PDF.

        Returns:
            A new Paper object from the PDF.
        """

        with open(path) as pdf:
            return Paper(slate.PDF(pdf))
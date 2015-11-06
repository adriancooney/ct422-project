import slate
import logging
import pyparsing as pp

from index import Index
from question import Question
from container import Container

class Paper(Container):
    # Let's define our parser
    __ = pp.White().suppress()
    _ = (pp.White(exact=1) | pp.LineEnd() | pp.LineStart()).suppress()
    ___ = pp.Optional(__)

    # Define tokens for numerical, alpha and roman indices
    # Max two digits for numerical indices because lecturers aren't psychopaths
    index_digit = pp.Word(pp.nums, max=2).setParseAction(lambda s, l, t: [Index("decimal", int(t[0]))])("[0-9]") 
    index_alpha = pp.Word(pp.alphas, exact=1).setParseAction(lambda s, l, t: [Index("alpha", t[0])])("[a-z]")
    index_roman = pp.Word("ivx").setParseAction(lambda s, l, t: [Index("roman", t[0])])("[ivx]") # We only support 1-100 roman numerals
    index_type = (index_digit | index_roman | index_alpha)("index")

    # Define token for ("Question" / "Q") + "."
    question = (pp.CaselessLiteral("Question") + pp.Optional("."))("question")

    # Define tokens for formatted indices e.g [a], (1), ii. etc.
    index_dotted = (index_type + pp.Literal(".").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("dotted"))
    index_round_brackets = (pp.Literal("(").suppress() + index_type + pp.Literal(")").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("round"))
    index_square_brackets = (pp.Literal("[").suppress() + index_type + pp.Literal("]").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("square"))
    index_question = (pp.Word("qQ", exact=1).suppress() + pp.Optional(".").suppress() + index_type + pp.Optional(".").suppress()).setParseAction(lambda s, l, t: t[0].setNotation("question"))

    # Define final index token with optional Question token before formatted index
    index = (
        # Whitespace is required before each index 
        _ + \
        # Optional "Question." before
        pp.Optional(question + ___).suppress() + \
        # The index
        (index_question | index_dotted | index_round_brackets | index_square_brackets) + \
        # Required whitespace *after* index
        _
    )

    # Define a section header
    section = (pp.CaselessKeyword("Section").suppress() + __ + index_type + _).setParseAction(
        lambda s, l, t: [t[0].section()]
    )("section")

    # Entry point for the parser
    entry = section ^ index

    def __init__(self, document=None):
        """The Paper class describes a Exam paper.
        
        Here we parse questions and store them in a neat array.
        """

        Container.__init__(self)

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

        We have a pretty complicated sorting algorithm

        Args:
            page (str): A page within the paper.
        """


        # If were passed in a list of pages, join them together
        if isinstance(pages, list):
            pages = ' '.join([page for page in pages])

        logging.info("Parsing exam paper question pages.")
        logging.info(pages)

        stack = [self]

        # Loop over every token we've parsed from the pages
        for token, u, v in Paper.entry.leaveWhitespace().scanString(pages):
            index = token[0] # The incoming index
            container = stack[-1] # The container is the last item in the stack

            logging.info("0. Handling index %r" % index)

            question = Question(index)

            if isinstance(container, Paper):
                logging.info("1. Pushing top level question %r." % question)
                container.push(question)
                stack.append(question)
            elif isinstance(container, Question):
                last_index = container.index

                if index.isSimilar(last_index):
                    logging.info("1.1 Similiar indexes %s and previous %s." % (index.index_type, last_index.index_type))
                    if last_index.isNext(index):
                        logging.info("1.1.1 Pushing question with same index type and in sequence.")
                        stack.pop()
                        container = stack[-1]
                        container.push(question)
                        stack.append(question)
                    else:
                        # Outlier
                        logging.info("1.1.2 Question with similar indexes but not in sequence, ignoring.")
                        continue
                else:
                    logging.info("1.2 Dissimilar indexes %s and previous %s." % (index.index_type, last_index.index_type))
                    
                    parent_container, n = self._find_similar(stack, -2, index)

                    # We need to traverse the container tree and see if we can find a similar index
                    if parent_container:

                        logging.info("1.2.1 Index similar to parent container index %d up the stack [%r]" % (n, parent_container.index))

                        if parent_container.index.isNext(index):
                            logging.info("1.2.1.1 Index in sequence, pushing into parent container's container.")
                            stack = stack[:n]

                            container = stack[-1]
                            container.push(question)
                            stack.append(question)
                        else:
                            logging.info("1.2.1.2 Index not in sequence, ignoring")
                            continue
                    elif index.i == 1 or last_index.is_section:
                        logging.info("1.2.2 Pushing new question into container %r." % container)
                        container.push(question)
                        stack.append(question)
                    else:
                        logging.info("1.2.3 New index value not first in sequence, ignoring.")
                        continue

        logging.info(self)  

    def _find_similar(self, stack, start, index):
        """Traverses up the stack finding a container of similar index
        """ 
        i = start
        parent_container = stack[i]
        while parent_container != None:
            if isinstance(parent_container, Paper):
                return (False, 0)
            elif isinstance(parent_container, Question) and parent_container.index.isSimilar(index):
                return (parent_container, i)
            else:
                i -= 1
                parent_container = stack[i]

        return (False, 0)

    def to_string(self, container=None, level=0, tab="--", compact=False):
        output = (tab * level) + (" " if not compact and level > 0 else "") if tab != None else ""

        if container is None:
            container = self
            level = -1

        if isinstance(container, Question):
            if container.index.is_section:
                output += "s" + str(container.index.value).lower()
            else:
                output += str(container.index.value).lower()

            output += "," if compact else "\n"

        if isinstance(container, Container):
            for item in container.contents:
                output += self.to_string(container=item, level=level+1, compact=compact, tab=tab)

        return output

    def __repr__(self):
        return self.to_string()


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
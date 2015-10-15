import slate
import logging

class Paper:
    """The Paper class describes a Exam paper.
    
    Here we parse questions and store them in a neat array.
    """

    def __init__(self, document=None):
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

        for i in range(len(document)):
            if i == 0:
                self.parse_front_page(document[i])
            else:
                self.parse_page(document[i])


    def parse_front_page(self, front_page):
        """Parse the front page of a paper.

        Args:
            front_page (str): The front page of a paper.
        """

        logging.info("Parsing front page of \"%s\".." % front_page[:30])

    def parse_page(self, page):
        """Parse a page in a paper.

        Args:
            page (str): A page within the paper.
        """

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
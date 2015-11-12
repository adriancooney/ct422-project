"""This script downloads all the papers from mis.nuigalway.ie
"""

import logging
from ..src.model import Paper
from ..src.config import Session

session = Session()

# Get all the modules
paper = session.query(Paper).filter(Paper.id == ).one()

# Save them to the downloads folder
Paper.PAPER_DIR = "/Users/adrian/Downloads/exam_papers"

print "Indexing {}.".format(paper)

# Index the module
paper.index()
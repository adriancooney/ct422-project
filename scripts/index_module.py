"""This script downloads all the papers from mis.nuigalway.ie
"""

import logging
import time
from ..src.model import Module, Paper
from ..src.config import Session

session = Session()

# Shutup sql alchemy
sqla = logging.getLogger("sqlalchemy.engine.base.Engine")
sqla.disabled = True

# Get all the modules
module = session.query(Module).filter(Module.code == "ME352-1").one()

# Save them to the downloads folder
Paper.PAPER_DIR = "/Users/adrian/Downloads/exam_papers"

print "Indexing {}.".format(module)

# Index the module
module.index(force=True)
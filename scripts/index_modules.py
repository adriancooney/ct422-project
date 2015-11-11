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
modules = session.query(Module).filter(Module.is_indexed == False).all()

# Save them to the downloads folder
Paper.PAPER_DIR = "/Users/adrian/Downloads/exam_papers"

for i, module in enumerate(modules):
    print "{}. Indexing {}. ({}/{})".format(i, module, i, len(modules))

    # Index the module
    module.index()
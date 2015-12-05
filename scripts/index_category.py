"""This script downloads all the papers from mis.nuigalway.ie
"""

import logging
import time
from project.src.model import Category
from project.src.config import Session
from sys import argv, exit

session = Session()

if len(argv) == 1:
    print "Please specify category to index."
    exit()

# Get the category
category = Category.getByCode(session, argv[1])

print "Indexing {}.".format(category)

for module in category.modules:
    if not module.indexed:
        # Index the module
        module.index(force=True)
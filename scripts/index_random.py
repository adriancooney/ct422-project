"""Index random N modules.

Usages:
    
    python index_random.py <count>

"""

from project.src.model import Module
from project.src.config import Session
from sqlalchemy.sql.expression import func
from sqlalchemy.orm.exc import NoResultFound
from sys import argv, exit

if len(argv) == 1:
    count = 10
else:
    count = argv[1]

session = Session()

try:
    # Select random modules
    module = session.query(Module)

    print "Indexing {} - {}".format(module.code, module.name)
    
    module.index(force=True)
except NoResultFound:
    print "Module not found."
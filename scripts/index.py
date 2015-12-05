from project.src.model import Module
from project.src.config import Session
from sqlalchemy.orm.exc import NoResultFound
from sys import argv, exit

if len(argv) == 1:
    print "Please specify a module e.g. ct422"

session = Session()
try:
    module = Module.getByCode(session, argv[1])

    print "Indexing {} - {}".format(module.code, module.name)
    
    module.index(force=True)
except NoResultFound:
    print "Module not found."
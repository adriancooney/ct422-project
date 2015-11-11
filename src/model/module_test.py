from . import Module, Paper
from ..config import Session

session = Session()

def test_module_download():
    Paper.PAPER_DIR = "/tmp/ct422"
    ct422 = session.query(Module).filter(Module.code == "CT422-1").one()
    papers = ct422.index()

    print ct422.to_JSON()
from module import Module
from ..config import Session

session = Session()

def test_module_download():
    ct422 = session.query(Module).filter(Module.code == "CT422-1").one()

    papers = ct422.download_papers("/tmp/ct422")
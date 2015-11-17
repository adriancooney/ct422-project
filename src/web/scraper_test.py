from scraper import Scraper
import pytest

@pytest.mark.xfail(raises=ValueError)
def test_scraper_max():
    Scraper.get_papers("MA%")

def test_scraper_none():
    assert len(Scraper.get_papers("MA1")) == 0
from . import api

def test_get_paper():
    api.get_paper('CT422-1', 2007, 'summer', 1)
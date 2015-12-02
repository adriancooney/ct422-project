from project.src import api
import flask

# def test_get_paper():
#     api.get_paper('CT422-1', 2007, 'summer', 1)

# def test_get_module_report():
    # api.get_module_report('CT422-1', 2007, 'winter')

# def test_get_pdf():
#     api.get_paper("CT422-1", 2007, None, 1, "html")

# def test_get_module():
#     api.get_module("CT422-1")

def test_list_categories():
    api.list_category_modules(2)

"""This script creates a database of all the mis.nuigalway.ie exam papers
"""

import os
import pandas
import logging
from sqlalchemy.orm.exc import NoResultFound
from ..src.web import Scraper
from ..src.model import Module, Category, Paper
from ..src.config import Session

session = Session()

# First off, we check if we have created the module categories
# We will most definitely have to on the first run.
# Import the modules.csv
modules = pandas.read_csv(os.path.join(os.path.dirname(__file__), "../data/modules.csv"))

# Create the modules
if session.query(Category).count() == 0:
    logging.info(">> Creating the module categories..")
    session.bulk_insert_mappings(Category, [dict(**row) for index, row in modules.iterrows()])
    session.commit()

# Create the queue
queue = [(row, row.code + "%") for row in session.query(Category).order_by(Category.code).all()]

# Loop over each item in the queue
while len(queue) > 0:
    category, search = queue.pop(0)
    print ">> Searching exam papers for code {} (\"{}\")".format(category.code, search)

    try:
        papers = Scraper.get_papers(search)

        print "   %d papers got for %s (%s)" % (len(papers), category.name, category.code)

        for paper in papers:
            #{'name': u'Cell Biology', 'sitting': u'First Sitting', 'period': u'Semester 1', 'module': u'AN219-1', 'paper': u'Paper 1 - Written', 'link': 'https://www.mis.nuigalway.ie/papers_public/2014_2015/AN/2014_2015_AN219_1_1_5.PDF', 'year': u'2014/2015'}
            # First of all, let's find the module for the paper
            # if it doesn't exist create it
            try:
                module = session.query(Module).filter(Module.code == paper["module"]).one()
            except NoResultFound:
                # Nope, it doesn't exist, create the module
                module = Module(category=category.id, code=paper["module"], name=paper["name"])
                session.add(module)
                session.commit()

                print module.id

            years = paper["year"].split("/")

            # Create the paper object
            paper = Paper(
                module=module.id,
                name=paper["paper"],
                period=paper["period"],
                sitting=paper["sitting"],
                year_start=int(years[0]),
                year_stop=int(years[1]),
                link=paper["link"]
            )

            # Add it to the database
            session.add(paper)
            session.commit()
    except ValueError:
        # Sometimes nuig shits itself when you request to many papers. This means you need
        # to break down your search query into a smaller scope. We do this by instead of XX%,
        # we add each letter from the alphabet to XXA%, XXB%, .., XX9% to the start of the queue
        # for processing.
        print "!! Too may results returned for %s. Breaking down.." % category.code
        new_terms = [(category, "{}{}%".format(search[:-1], u)) for u in "abcdefghijklmnoprstuvwxyz0123456789".upper()]
        queue = new_terms + queue
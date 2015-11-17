import json
import logging
import itertools

import pandas as pd
from paper import Paper
from itertools import groupby
from collections import OrderedDict
from pandas import DataFrame, concat
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from paper import NoLinkException, UnparseableException, PaperNotFound
from base import Base
from sqlalchemy.orm import relationship, Session, reconstructor
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean

class Module(Base):
    SIMILARITY_THRESHOLD = 0.7

    __tablename__ = "module"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey('module_category.id'))
    is_indexed = Column(Boolean, default=False)
    papers = relationship("Paper", backref="module")

    @reconstructor
    def init_load(self):
        self.questions = None
        self.vectorizer = None
        self.tfidf = None

    def index(self, force=False):
        if not force and self.is_indexed:
            return

        for paper in self.papers:
            try:
                paper.index()
            except NoLinkException:
                logging.info("No link for paper %r" % paper)
            except UnparseableException:
                logging.warning("Unable to parse paper %r" % paper)
            except PaperNotFound:
                logging.warning("Paper %r not found." % paper)

        self.is_indexed = True

        session = Session.object_session(self)
        session.add(self)
        session.commit()

    def to_dict(self):
        data = {}

        # First of all, organize the papers by year
        for paper in self.papers:
            # Skip papers that we couldn't parse
            if not paper.contents:
                continue

            year = str(paper.year_start)

            # We use year start as the key
            if not year in data:
                data[year] = []

            data[year].append(paper.contents)

        return { self.code: data }

    def to_JSON(self):
        return json.dumps(self.to_dict(), indent=4)

    def __repr__(self):
        return "<Module(id={}, code={}, papers={})>".format(self.id, self.code, len(self.papers))

    def get_questions(self):
        """This methods returns a list of all the questions in the form of:

            (Paper, (question_path), content)
            (<Paper(id=1)>, (1, 2, 1), "<question document>")"""

        questions = []
        for paper in self.papers:
            if paper.contents:
                nq = []
                for path, question, index in paper.get_questions():
                    nq.append((paper, path, question["content"], index))
                questions += nq

        return DataFrame(questions, columns=["Paper", "Path", "Content", "Index"])

    def vectorize(self):
        self.questions = self.get_questions()
        self.vectorizer = TfidfVectorizer()
        self.tfidf = self.vectorizer.fit_transform(self.questions["Content"])

    def find_similar_questions(self, paper, path):
        if not self.vectorizer:
            self.vectorize()

        def is_question(i):
            question = self.questions.iloc[i]
            return question["Path"] == path and question["Paper"] == paper

        # Grab the question we have to find similar for's index
        question = self.questions.select(is_question)
        question_index = question.index[0]

        # Compute the similarity
        cs = cosine_similarity(self.tfidf[question_index:question_index+1], self.tfidf)
        similarity = DataFrame(cs[0], columns=["Similarity"])

        # Join the similirity onto the questions datafame
        joined = concat([self.questions, similarity], axis=1)

        return joined.sort_values(["Similarity"], ascending=False)

    def similarity_analysis(self, paper):
        """Perform a similarity analysis over all the questions in paper"""
        analysis = []
        for path, question, index in paper.get_questions():
            logging.info("Perform similarity analysis on question %r '%s..'" % (question, question["content"][:30]))

            similar_questions = self.find_similar_questions(paper, path)
            similar_relevant = similar_questions[similar_questions["Similarity"] > Module.SIMILARITY_THRESHOLD]

            p = []
            for i, row in similar_relevant.iterrows():
                npaper = row["Paper"]
                npath = row["Path"]

                # Prevent similarity analysis on same paper
                if npaper == paper:
                    continue

                data = npaper.to_dict()
                nquestion, nindex = npaper.get_question(*npath)

                data['similarity'] = row["Similarity"]
                data['question'] = {
                    'index': nindex,
                    'path': npath,
                    'content': nquestion["content"]
                }

                p.append(data)

            breakdown = {
                'question': {
                    'content': question["content"],
                    'path': path,
                    'index': index
                },
                'papers': p
            }

            analysis.append(breakdown)

        return analysis, paper

    def similarity_analysis_by_year(self, paper):
        analysis, paper = self.similarity_analysis(paper)

        for question in analysis:
            papers = question["papers"]

            # Sort the papers first by year
            papers.sort(key=lambda p: p["years"][0])

            npapers = OrderedDict()

            for key, group in groupby(papers, lambda p: p["years"][0]):
                npapers[key] = [record for record in group]

            question["papers"] = npapers

        return analysis, paper


    def latest_similarity_analysis(self, groupByYear=False):
        """Perform similarity analysis on the latest paper"""
        session = Session.object_session(self)
        latest_paper = session.query(Paper).filter(
            (Paper.module_id == self.id) & \
            (Paper.contents != None)
        ).order_by(Paper.year_start.desc(), Paper.order_by_period).first()

        if groupByYear:
            return self.similarity_analysis_by_year(latest_paper)
        else:
            return self.similarity_analysis(latest_paper)
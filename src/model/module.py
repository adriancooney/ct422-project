import json
import logging
import itertools

from pandas import DataFrame, concat
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from paper import NoLinkException, UnparseableException, PaperNotFound
from base import Base
from sqlalchemy.orm import relationship, Session, reconstructor
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean

class Module(Base):
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

        def flatten(paper, question, path=()):
            qs = []

            if "content" in question:
                qs.append((paper, path, question["content"]))

            if "children" in question:
                for i, child in enumerate(question["children"]):
                    qs += flatten(paper, child, path + (i,))

            return qs

        questions = []
        for paper in self.papers:
            if paper.contents:
                questions += [(paper,) + question for question in paper.get_questions()]

        return DataFrame(questions, columns=["Paper", "Path", "Content"])

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

        question = self.questions.select(is_question)
        question_index = question.index[0]

        similarity = DataFrame(cosine_similarity(self.tfidf[question_index:question_index+1], self.tfidf)[0], columns=["Similarity"])
        joined = concat([self.questions, similarity], axis=1)

        return joined.sort(["Similarity"], ascending=False)
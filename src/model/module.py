import json
import logging
import itertools
import nltk
import pandas as pd
import numpy as np
import scipy as sp

from os import path
from itertools import groupby
from collections import OrderedDict
from pandas import DataFrame, concat
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import relationship, Session, reconstructor
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean

from base import Base
from paper import NoLinkException, UnparseableException, PaperNotFound, Paper

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
                questions += [(paper, p, q["content"], i) for p, q, i in paper.get_questions()]

        return DataFrame(questions, columns=["Paper", "Path", "Content", "Index"])

    def vectorize(self):
        """
            So let's begin our process of TFIDF vectorization of our documents.
            We're given a document set D and we want:

                1. Remove the stop words.
                2. Stem.
                3. Get the TFIDF for each document.
        """
        # Retrieve our list of documents (i.e. the questions from each paper)
        self.questions = self.get_questions()

        # First, let's remove the stop words using the default SKLearn
        # stop word dictionary, stem the words and count each word.
        # We'll use the handy sklearn.feature_extraction.CountVectorizer
        # to do this in one fell swoop.

        # Create our tokenizer to hand to the CountVectorizer. This will stem
        # each token and return it. We'll be using the NLTK stem package which
        # will do the work for us. We also need to grab out NLTK tokenizer.
        stemmer = PorterStemmer()
        stopwords = nltk.corpus.stopwords.words('english')
        tokenizer = RegexpTokenizer(r'\w+')
        
        # And now define the `tokenize` method
        def tokenize(text):
            # Convert our document to a list of tokens (remove whitespace, punctuation)
            # WARNING: This needs to be improved to preserve some punctuation (it's or lion's)
            # and preserve marking.
            tokens = tokenizer.tokenize(text)

            # Remove stop words then stem
            return map(stemmer.stem, tokens)

        # Create our vectorizer with our tokenizer
        self.vectorizer = CountVectorizer(stop_words=stopwords, decode_error="replace")
        
        # Fit the questions and save the word counts
        self.documents = self.vectorizer.fit_transform(self.questions.Content)
        self.dictionary = self.vectorizer.get_feature_names()

        # So now we have counts for every word in the every document (i.e. tf)
        # Define our TFIDF generation functions
        N = len(self.questions)
        tf = lambda document, term: self.documents[document, term]
        df = lambda term: self.documents[:, term].sign().sum()
        idf = lambda term: np.math.log10(float(N) / float(df(term)))
        tfidf = lambda document, term: float(tf(document, term)) * idf(term)

        # Initilize our TFIDF sparse matrix
        self.tfidf_documents = sp.sparse.lil_matrix(self.documents.shape, dtype=float)

        # Fill it with the tfidf for all terms and we're done!
        for document, term in zip(*self.documents.nonzero()):
            self.tfidf_documents[document, term] = tfidf(document, term)


    def find_similar_questions(self, paper, path):
        # Compute the tf-idf if not already completed
        if not self.vectorizer:
            self.vectorize()

        def is_question(i):
            question = self.questions.iloc[i]
            return question["Path"] == path and question["Paper"] == paper

        # Grab the question we have to find similar for's index
        question = self.questions.select(is_question)
        question_index = question.index[0]

        # Transform our query
        query = self.tfidf_documents[question_index, :]

        # Compute the similarity and return a gram matrix
        # of D_n x Query and stick it in a datafram
        similarity = DataFrame(cosine_similarity(self.tfidf_documents, query), columns=["similarity"])

        # Join the similarity onto the questions datafame
        joined = concat([self.questions, similarity], axis=1)

        return joined.sort_values(["similarity"], ascending=False)

    def similarity_analysis(self, paper):
        """Perform a similarity analysis over all the questions in paper"""
        analysis = []

        # Get all the questions in the paper
        for path, question, index in paper.get_questions():
            logging.info("Perform similarity analysis on question %r '%s..'" % (question, question["content"][:30]))

            # Find similar questions for this specific questions within all the papers
            similar_questions = self.find_similar_questions(paper, path)

            # Only select questions over similarity threshold
            similar_relevant = similar_questions[(similar_questions.similarity > Module.SIMILARITY_THRESHOLD)]

            papers = []
            for i, row in similar_relevant.iterrows():
                relevant_paper = row["Paper"]
                relevant_question_path = row["Path"]

                # Prevent similarity analysis on same paper
                if relevant_paper == paper:
                    continue

                data = relevant_paper.to_dict()
                relevant_question, relevant_question_index = relevant_paper.get_question(*relevant_question_path)

                data['similarity'] = row.similarity
                data['question'] = {
                    'index': relevant_question_index,
                    'path': relevant_question_path,
                    'content': relevant_question["content"]
                }

                papers.append(data)

            breakdown = {
                'question': {
                    'content': question["content"],
                    'path': path,
                    'index': index
                },
                'papers': papers
            }

            analysis.append(breakdown)

        return analysis, paper

    def similarity_analysis_by_year(self, paper):
        """Group the similarity analysis by year"""
        analysis, paper = self.similarity_analysis(paper)

        for question in analysis:
            papers = question["papers"]

            # Sort the papers first by year
            papers.sort(key=lambda p: p["years"][0])

            ordered_papers = OrderedDict()

            for key, group in groupby(papers, lambda p: p["years"][0]):
                ordered_papers[key] = [record for record in group]

            question["papers"] = ordered_papers

        return analysis, paper

    def latest_similarity_analysis(self, groupByYear=False):
        """Perform similarity analysis on the latest paper"""
        session = Session.object_session(self)

        # Get the latest paper
        latest_paper = session.query(Paper).filter(
            (Paper.module_id == self.id) & \
            (Paper.contents != None)
        ).order_by(Paper.year_start.desc(), Paper.order_by_period).first()

        if groupByYear:
            return self.similarity_analysis_by_year(latest_paper)
        else:
            return self.similarity_analysis(latest_paper)
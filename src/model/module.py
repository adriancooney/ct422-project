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
from datetime import datetime
from pandas import DataFrame, concat
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import relationship, Session, reconstructor
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func

from project.src.model.question import Question, Similar
from project.src.model.paper import NoLinkException, UnparseableException, PaperNotFound, Paper
from project.src.model.base import Base

class Module(Base):
    SIMILARITY_THRESHOLD = 0.2

    __tablename__ = "module"

    id = Column(Integer, primary_key=True)
    code = Column(String)
    name = Column(String)
    category_id = Column(Integer, ForeignKey('module_category.id'))
    papers = relationship("Paper", backref="module", order_by="Paper.year_start, Paper.period, Paper.indexed")
    indexed = Column(Boolean)
    indexed_at = Column(DateTime)

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
                if force or not paper.is_indexed():
                    print "Indexing %r" % paper
                    paper.index()
                else:
                    print "Skipping indexing paper %r" % paper
            except NoLinkException:
                logging.info("No link for paper %r" % paper)
            except UnparseableException:
                logging.warning("Unable to parse paper %r" % paper)
            except PaperNotFound:
                logging.warning("Paper %r not found." % paper)

        self.indexed = True
        self.indexed_at = datetime.now()

        session = Session.object_session(self)

        self.vectorize()

        for question in self.questions:
            question.similar = self.find_similar_questions(question)
            session.add(question)

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
        """This methods returns a list of all the questions."""

        questions = []
        for paper in self.papers:
            if paper.questions:
                questions += paper.questions

        return filter(lambda q: q.content, questions)

    def get_grouped_papers(self):
        # Group by period
        get_period = lambda p: p.period
        get_year = lambda p: p.year_start
        papers = [paper for paper in sorted(self.papers, key=get_period)] # Sort by period
        papers = { period: [p for p in group] for period, group in groupby(papers, key=get_period) } # Group by period

        # Now make a dict of papers by year
        for period, group in papers.iteritems():
            papers[period] = { paper.year_start: paper for paper in sorted(group, key=get_year) }

        return papers

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
        self.documents = self.vectorizer.fit_transform(map(lambda q: q.content, self.questions))
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

    def find_similar_questions(self, question):
        # Compute the tf-idf if not already completed
        if not self.vectorizer:
            self.vectorize()

        # Grab the question we have to find similar for's index
        question_index = 0
        for i, q in enumerate(self.questions):
            if question is q:
                question_index = i
                break

        # Grab our question vector
        query = self.tfidf_documents[question_index, :]

        # Compute the similarity and return a gram matrix
        # of D_n x Query and stick it in a datafram
        similarity = cosine_similarity(self.tfidf_documents, query).flatten()

        # Generate the similarity object
        return [Similar(question=q, similarity=s) for q, s in zip(self.questions, similarity)]

    def similarity_analysis(self, paper):
        """Perform a similarity analysis over all the questions in paper"""
        analysis = []

        # Get all the questions in the paper
        for question in paper.questions:
            logging.info("Perform similarity analysis on question %r '%s..'" % (question, question.content[:30]))

            # Find similar questions for this specific questions within all the papers
            similar_questions = self.find_similar_questions(question)

            # Only select questions over similarity threshold
            similar_relevant = similar_questions[similar_questions.similarity > Module.SIMILARITY_THRESHOLD].sort(
                "similarity", ascending=False)

            papers = []
            for i, row in similar_relevant.iterrows():
                relevant_question = row.question

                # Prevent similarity analysis on same paper
                if relevant_question.paper == paper:
                    continue

                data = {
                    'paper': relevant_question.paper,
                    'similarity': row.similarity,
                    'question': relevant_question
                }

                papers.append(data)

            # Sort them
            papers.sort(key=lambda p: p["paper"].year_start)

            ordered_papers = OrderedDict()
            for key, group in groupby(papers, lambda p: p["paper"].year_start):
                ordered_papers[key] = [record for record in group]

            breakdown = {
                'question': question,
                'papers': ordered_papers
            }

            analysis.append(breakdown)

        return analysis

    def find_most_popular_questions(self):
        """Find the most popular questions. 

        This loops through all the questions, find's the similar questions
        and ranks them by sum(similarity)
        """
        session = Session.object_session(self)

        questions = session.query(Similar.question_id, func.sum(Similar.similarity).label("cum_similarity")).filter(
            (Similar.similarity > Module.SIMILARITY_THRESHOLD) & \
            (Similar.question_id == Similar.similar_question_id)
        ).group_by(Similar.question_id).join(Question, Similar.question_id == Question.id).all()

        print questions

    def is_indexed(self):
        """Determine whether a module is indexed or not."""
        return self.indexed or all(map(lambda p: p.indexed, self.papers))

    #########################################
    # Query methods
    #########################################
    
    @staticmethod
    def getByCode(session, code):
        return session.query(Module).filter(
            Module.code.like(code.upper() + '%')
        ).one()
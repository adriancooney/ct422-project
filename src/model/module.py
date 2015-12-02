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

from paper import NoLinkException, UnparseableException, PaperNotFound, Paper
from base import Base

class Module(Base):
    SIMILARITY_THRESHOLD = 0.2

    __tablename__ = "module"

    id = Column(Integer, primary_key=True)
    code = Column(String)
    name = Column(String)
    category_id = Column(Integer, ForeignKey('module_category.id'))
    papers = relationship("Paper", backref="module", order_by="Paper.year_start, Paper.period, Paper.indexed")

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
                if not paper.is_indexed():
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
        """This methods returns a list of all the questions."""

        questions = []
        for paper in self.papers:
            if paper.questions:
                questions += paper.questions

        return questions

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

        return DataFrame(zip(self.questions, similarity), columns=["question", "similarity"])

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
        # Compute the tf-idf if not already completed
        if not self.vectorizer:
            self.vectorize()

        # Let's find the most popular question i.e. the question that is
        # simililar to most other questions, then group them by their path.
        # This is computing the gram matrix of the entire corpus D \cdot D.
        popularity = cosine_similarity(self.tfidf_documents, self.tfidf_documents).sum(axis=0)

        # Create our dataframe
        popular = DataFrame(zip(self.questions, popularity), columns=["question", "popularity"])

        questions = []

        # Group by question path
        for index, group in popular.groupby(lambda i: '.'.join(map(str, popular.iloc[i].question.path))):
            # Sort them by popularity
            group.sort_values("popularity", ascending=False)

            head = group.head(1)

            # Assume the first is the most popular
            questions.append({
                'question': head.question.values[0],
                'popularity': head.popularity.values[0],
                'similar': group.to_dict(orient="records")
            })

        return sorted(questions, key=lambda q: q["popularity"], reverse=True)

    def is_indexed(self):
        """Determine whether a module is indexed or not."""
        return all(map(lambda p: p.indexed, self.papers))

    #########################################
    # Query methods
    #########################################
    
    @staticmethod
    def getByCode(session, code):
        return session.query(Module).filter(
            Module.code.like(code + '%')
        ).one()
import flask
import logging
import os.path
import sqlalchemy
from logging.handlers import RotatingFileHandler
from flask import Flask, abort, request
from itertools import groupby
from project.src.model import Module, Paper, Category, Institution
from project.src.model.paper import UnparseableException, NoLinkException, InvalidPathException
from project.src.model.paper_pdf import PaperNotFound
from project.src.config import Session, APP_PORT, APP_HOST, APP_DEBUG, APP_LOG
from werkzeug.contrib.cache import SimpleCache
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
cache = SimpleCache()
session = Session()

def fail(code, message, format='html'):
    """Fail a request in a standard way."""
    if format == 'json':
        response = flask.jsonify({
            'error': message,
            'code': code
        })
    elif format == 'html':
        response = flask.render_template('error.html', code=code, message=message)

    return response, code

@app.route('/module/<module>/')
def get_module(module):
    try:
        module = module.upper()
        module = Module.getByCode(session, module)

        # Fail if the module is not indexed
        if not module.is_indexed():
            return fail(403, "Module {} has not been indexed yet.".format(module.code))

        papers = module.get_grouped_papers()

        # if module.is_indexed() and sum(map(lambda p: len(p.questions), module.papers)) > 5:
        #     popular = module.find_most_popular_questions()
        #     return flask.render_template('module.html', module=module, popular=popular)
        # else:
        return flask.render_template('module.html', module=module)

    except NoResultFound:
        return fail(404, "Module not found.")


@app.route('/module/<module>/report/', defaults={ 'year': 'latest', 'period': 'winter' })    
@app.route('/module/<module>/<year>/report/', defaults={ 'period': 'winter' })
@app.route('/module/<module>/<year>/<period>/report/')
def get_module_report(module, year, period):
    try:
        module = Module.getByCode(session, module)

        period = period.lower()

        try:
            if year == 'latest':
                # Use the most recent paper
                paper = Paper.get_latest(session, module)
            else:
                year = int(year)

                print year, period, module.id
                paper = session.query(Paper).filter(
                    (Paper.year_start == year) & \
                    (Paper.period == (period[0].upper() + period[1:])) & \
                    (Paper.module_id == module.id)
                ).one()
        except NoResultFound:
            return fail(404, "No paper found.")

        analysis = module.similarity_analysis(paper)

        return flask.render_template('analysis.html', 
            module=module, paper=paper, analysis=analysis)
    except NoResultFound:
        return fail(404, "Module not found.")

# Get the content of a paper
# Example:
# 
#   /paper/ct422-1/2007/summer/1?question=0.1
@app.route('/module/<module>/<year>', defaults={ 'period': None, 'sitting': 1, 'format': 'html' })
@app.route('/module/<module>/<year>.<format>', defaults={ 'period': None, 'sitting': 1 })
@app.route('/module/<module>/<year>/<period>', defaults={ 'sitting': 1, 'format': 'html' })
@app.route('/module/<module>/<year>/<period>.<format>', defaults={ 'sitting': 1 })
@app.route('/module/<module>/<year>/<period>/<sitting>', defaults={ 'format': 'html' })
@app.route('/module/<module>/<year>/<period>/<sitting>.<format>')
def get_paper(module, year, period, sitting, format):
    try:
        if not format in ['pdf', 'html']:
            return fail(401, "Unknown format %s" % format)

        module = Module.getByCode(session, module)

        # Fail if the module is not indexed
        if not module.is_indexed():
            return fail(403, "Module {} has not been indexed yet.".format(module.code))

        # Get the paper
        selection = Paper.module_id == module.id

        if period:
            selection = selection & (Paper.period == (period[0].upper() + period[1:].lower()))

        if year == 'latest':
            paper = session.query(Paper).filter(selection).order_by(Paper.year_start.desc(), Paper.order_by_period).first()

            if not paper:
                raise NoResultFound()
        else:
            selection = selection & (Paper.year_start == year)
            paper = session.query(Paper).filter(selection).first()

            if not paper:
                raise NoResultFound()

        # Index the paper
        if not paper.is_indexed():
            try:
                paper.index()
            except UnparseableException:
                if not format == 'pdf':
                    return fail(400, "Unable to parse paper %r" % paper)
            except NoLinkException:
                return fail(404, "Paper %r has no link" % paper)
            except PaperNotFound:
                return fail(404, "PDF not found on NUIG Exam papers for %r." % paper)

        # If they just want the PDF, serve em that
        if format == 'pdf':
            # No downloading here.
            return flask.redirect(paper.link, code=302)

        # Direct path to question
        path = request.args.get("q")

        if path:
            path = [int(x) for x in path.split('.')]
            question = None

            # find the question
            for q in paper.questions:
                if q.path == path:
                    question = q

            if not question:
                return fail(404, "Question in paper %d not found." % paper.id)

            return flask.render_template("question.html", question=question)
        else:
            return flask.render_template("module.html", module=module, paper=paper)
    except NoResultFound:
        return fail(404, "Paper not found.")
    except KeyError:
        return fail(401, "Invalid period. Periods available: Winter, Summer, Autumn, Spring")

@app.route("/modules/<category>/")
def list_category_modules(category):
    try:
        category = session.query(Category).filter(
            Category.code == category.upper()
        ).one()

        return flask.render_template('modules.html', category=category)
    except NoResultFound:
        return fail(404, "Category not found.")

@app.route("/<institution>/")
def get_institution(institution):
    institution = Institution.getByCode(session, institution)

    return flask.render_template('institution.html', institution=institution)

@app.route("/")
def get_index():
    modules = session.query(Module).filter(Module.indexed == True).all()
    return flask.render_template('index.html', modules=modules)

if __name__ == '__main__':
    if APP_LOG:
        handler = RotatingFileHandler(APP_LOG, maxBytes=10000, backupCount=1)
        handler.setLevel(logging.DEBUG)
        logging.getLogger('werkzeug').addHandler(handler)
        app.logger.addHandler(handler)

    app.run(port=APP_PORT, host=APP_HOST, debug=APP_DEBUG)
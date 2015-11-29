import flask
import logging
import os.path
import sqlalchemy
from flask import Flask, abort, request
from ..model import Module, Paper
from ..model.paper import UnparseableException, NoLinkException, InvalidPathException
from ..model.paper_pdf import PaperNotFound
from ..config import Session
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
    module = module.upper()

    index = request.args.get("index")

    if index:
        id = int(index)

        try:
            paper = Paper.getById(session, id)

            try:
                print "Indexing paper %r" % paper
                paper.index()
            except:
                pass
        except NoResultFound:
            return fail(404, "Paper %d not found" % id)

    try:
        module = Module.getByCode(session, module)
    except NoResultFound:
        return fail(404, "Module not found.")

    return flask.render_template('module.html', module=module)

@app.route('/module/<module>/report/', methods=['GET'], defaults={ 'year': 'latest' })    
@app.route('/module/<module>/<year>/report/', methods=['GET'])
def get_module_report(module, year):
    pass

@app.route('/module/<module>.json', methods=['GET'])
def get_module_json(module): 
    try:
        module = module.upper()
        key = 'module.%s' % module

        # Get it from the cache
        data = cache.get(key)

        if not data:
            # Get the module
            module = session.query(Module).filter(Module.code == module).one()

            if not module.is_indexed:
                module.index()

            analysis, paper = module.latest_similarity_analysis(groupByYear=True)

            cache.set(key, (module, analysis, paper))
        else:
            module, analysis, paper = data

        return flask.jsonify(analysis=analysis)
    except NoResultFound:
        return fail(404, "Module %s not found." % str(module))

# Get the content of a paper
# Example:
# 
#   /paper/ct422-1/2007/summer/1?question=0.1

@app.route('/paper/<module>/<year>', defaults={ 'period': None, 'sitting': 1, 'format': 'html' })
@app.route('/paper/<module>/<year>.<format>', defaults={ 'period': None, 'sitting': 1 })
@app.route('/paper/<module>/<year>/<period>', defaults={ 'sitting': 1, 'format': 'html' })
@app.route('/paper/<module>/<year>/<period>.<format>', defaults={ 'sitting': 1 })
@app.route('/paper/<module>/<year>/<period>/<sitting>', defaults={ 'format': 'html' })
@app.route('/paper/<module>/<year>/<period>/<sitting>.<format>')
def get_paper(module, year, period, sitting, format):
    try:
        if not format in ['json', 'pdf', 'html']:
            return fail(401, "Unknown format %s" % format)

        selection = Module.code.like(module.upper() + "%") & \
            (Paper.module_id == Module.id) 

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

        if not paper.is_indexed():
            try:
                paper.index()
            except UnparseableException:
                if not format == 'pdf':
                    return fail(400, "Unable to parse paper %r" % paper)
            except NoLinkException:
                return fail(404, "Paper %r has no link")
            except PaperNotFound:
                return fail(404, "PDF not found on NUIG Exam papers for %r." % paper)

        if format == 'pdf':
            return flask.send_from_directory(os.path.dirname(paper.pdf.path), os.path.basename(paper.pdf.path))

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

            if format == 'json':
                return flask.jsonify(paper=paper.to_dict(), question=question.to_dict())
            elif format == 'html':
                return flask.render_template("question.html", question=question)
        else:
            print "SERVING UP DAT SHIT"
            if format == 'json':
                return flask.jsonify(paper=paper)
            elif format == 'html':
                return flask.render_template("paper.html", paper=paper)
    except NoResultFound:
        return fail(404, "Paper not found.")
    except KeyError:
        return fail(401, "Invalid period. Periods available: Winter, Summer, Autumn, Spring")
    except Exception, error:
        print error

@app.route("/papers/<module>.json")
def list_papers(module):
    papers = session.query(Paper).filter(
        Module.code.like(module.upper() + '%') & \
        (Paper.module_id == Module.id)
    ).all()

    papers = [paper.to_dict() for paper in papers]

    return flask.jsonify(papers=papers)

@app.route("/modules/", defaults={ 'format': 'html' })
@app.route("/modules.<format>")
def list_modules(format):
    # FUCK IT TAKE EM ALL
    modules = session.query(Module).order_by(Module.code).all()

    if format == 'json':
        return flask.jsonify(modules=modules)
    elif format == 'html':
        return flask.render_template('modules.html', modules=modules)

if __name__ == '__main__':
    app.run()
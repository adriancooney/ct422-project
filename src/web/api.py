import flask
import logging
import os.path
import sqlalchemy
from flask import Flask, abort, request
from ..model import Module, Paper
from ..config import Session
from werkzeug.contrib.cache import SimpleCache
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
cache = SimpleCache()
session = Session()

def fail(code, message):
    """Fail a request in a standard way."""
    response = flask.jsonify({
        'error': message,
        'code': code
    })

    response.status_code = code

    return response

@app.route('/module/<module>/report', methods=['GET'])
def get_module_report(module): 
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

        return flask.render_template("analysis.html", analysis=analysis, paper=paper, module=module)
    except NoResultFound:
        return fail(404, "Module %s not found." % str(module))

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

            # Index it if it has not been already
            if not module.is_indexed:
                module.index()

            # Get the similarity data
            data = module.latest_similarity_analysis(groupByYear=True)

            # Save it in the cache
            cache.set(key, data)

        return flask.jsonify(**data)
    except NoResultFound:
        return fail(404, "Module %s not found." % str(module))

# Get the content of a paper
# Example:
# 
#   /paper/ct422-1/2007/summer/1?question=0.1

@app.route('/paper/<module>/<year>.<format>', defaults={ 'period': None, 'sitting': 1 })
@app.route('/paper/<module>/<year>/<period>.<format>', defaults={ 'sitting': 1 })
@app.route('/paper/<module>/<year>/<period>/<sitting>.<format>')
def get_paper(module, year, period, sitting, format):
    global periods

    try:
        if not format in ['json', 'pdf']:
            return fail(401, "Unknown format %s" % format)

        selection = Module.code.like(module.upper() + "%") & \
            (Paper.module_id == Module.id) 

        if period:
            selection = selection & (Paper.period == period.lower())

        if year == 'latest':
            paper = session.query(Paper).filter(selection).order_by(Paper.year_start.desc(), Paper.order_by_period).first()

            if not paper:
                raise NoResultFound()
        else:
            selection = selection & (Paper.year_start == year)
            paper = session.query(Paper).filter(selection).one()

        if format == 'pdf':
            if not paper.pdf:
                return fail(404, "PDF not found.")

            return flask.send_from_directory(os.path.dirname(paper.pdf.path), os.path.basename(paper.pdf.path))

        if not paper.is_indexed():
            try:
                paper.index()
            except UnparseableException:
                return fail(400, "Unable to parse paper %r" % paper)
            except (NoLinkException, PaperNotFound):
                return fail(404, "Paper %r not found." % paper)

        if not paper.contents:
            return fail(404, "Paper %r is unparseable." % paper)

        path = request.args.get("question")

        if path:
            question, index = paper.get_question(*[int(x) for x in path.split('.')])

            if not question:
                return fail(404, "Question in paper %d not found." % paper.id)

            return flask.jsonify(**question)
        else:
            return flask.jsonify(paper=paper.to_dict(), contents=paper.contents)
    except NoResultFound:
        return fail(404, "Paper not found.")
    except KeyError:
        return fail(401, "Invalid period. Periods available: %s" % periods.keys.join(', '))
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

if __name__ == '__main__':
    app.run()
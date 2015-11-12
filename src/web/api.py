import flask
from flask import Flask, abort, request
from ..model import Module, Paper
from ..config import Session
from sqlalchemy.orm.exc import NoResultFound
app = Flask(__name__)

session = Session()

Paper.PAPER_DIR = "/Users/adrian/Downloads/exam_papers"

def fail(code, message):
    """Fail a request in a standard way."""
    response = flask.jsonify({
        'error': message,
        'code': code
    })

    reponse.status_code = code

    return response

@app.route('/module/<module>/report', methods=['GET'])
def get_module(module): 
    try:
        # Get the module
        module = session.query(Module).filter(Module.code == module).one()

        if not module.is_indexed:
            module.index()

        data = module.latest_similarity_analysis()

        return flask.render_template("analysis.html", **data)
    except NoResultFound:
        return fail(404, "Module %s not found." % str(module))

@app.route('/module/<module>', methods=['GET'])
def get_module_json(module): 
    try:
        # Get the module
        module = session.query(Module).filter(Module.code == module).one()

        if not module.is_indexed:
            module.index()

        data = module.latest_similarity_analysis(groupByYear=True)

        return flask.jsonify(**data)
    except NoResultFound:
        return fail(404, "Module %s not found." % str(module))

# Get the content of a paper
# Example:
# 
#   /paper/ct422-1/2007/summer/1?question=0.1
periods = {
    'semester-1': 'Semester 1',
    'autumn': 'Autumn',
    'spring': 'Spring',
    'winter': 'Winter',
    'resits': 'Summer Repeats/Resits',
    'summer': 'Summer',
}

@app.route('/paper/<module>/<year>/', defaults={ 'period': 'summer', 'sitting': 1 })
@app.route('/paper/<module>/<year>/<period>', defaults={ 'sitting': 1 })
@app.route('/paper/<module>/<year>/<period>/<sitting>')
def get_paper(module, year, period, sitting):
    global periods

    try:
        paper = session.query(Paper).filter(
            (Paper.module_id == Module.id) & \
            (Paper.year_start == year) & \
            (Paper.period == periods[period]) & \
            Module.code.like(module.upper() + "%")
        ).one()

        if not paper.is_indexed():
            try:
                paper.index()
            except UnparseableException:
                return fail(400, "Unable to parse paper %r" % paper)
            except (NoLinkException, PaperNotFound):
                return fail(404, "Paper %r not found." % paper)

        if not paper.contents:
            return fail(404, "Paper %s is unparseable.")

        path = request.args.get("question")

        if path:
            question = paper.get_question(*[int(x) for x in path.split('.')])

            if not question:
                return fail(404, "Question in paper %d not found." % paper.id)

            return flask.jsonify(**question)
        else:
            return flask.jsonify(**paper.contents)
    except NoResultFound:
        return fail(404, "Paper not found.")
    except KeyError:
        return fail(401, "Invalid period. Periods available: %s" % periods.keys.join(', '))

if __name__ == '__main__':
    app.run()
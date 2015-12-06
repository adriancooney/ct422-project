import flask
import logging
import os.path
from logging.handlers import RotatingFileHandler
from flask import Flask
from project.src.web.exception import HttpException, MissingParameter
from project.src.model import Module, Paper, Category, Institution, Question, Visitor
from project.src.model.exception import NotFound, InvalidInput
from project.src.config import Session, APP_PORT, APP_HOST, APP_DEBUG, APP_LOG

app = Flask(__name__)
session = Session()

def fail(code, message):
    """Fail a request in a standard way."""
    return flask.render_template('error.html', code=code, message=message), code

@app.before_request
def visit():
    # Log incoming visitors to database
    # Ignore all static requests
    if app.static_url_path in flask.request.url:
        return

    # Save the visitor
    visitor = Visitor(flask.request)
    session.add(visitor)
    session.commit()

    # Add them to the context
    flask.g.visitor = visitor

@app.route('/module/<module>/')
def get_module(module):
    module = Module.getByCode(session, module)

    # Fail if the module is not indexed
    if not module.is_indexed():
        return fail(403, "Module {} has not been indexed yet.".format(module.code))

    return flask.render_template('module.html', module=module)

@app.route('/module/<module>/<year>/<period>/', defaults={'format': 'html'})
@app.route('/module/<module>/<year>/<period>.pdf', defaults={'format': 'pdf' })
def get_paper(module, year, period, format):
    module = Module.getByCode(session, module)
    paper = Paper.find(session, module, year, period)

    if format == 'pdf':
        if not paper.link:
            return fail(404, "Paper is not available online.")

        return flask.redirect(paper.link)
    else:
        return flask.render_template('module.html', module=module, paper=paper)

@app.route('/module/<module>/<year>/<period>/edit', methods=['get', 'post'])
def get_edit_question(module, year, period):
    module = Module.getByCode(session, module)
    paper = Paper.find(session, module, year, period)

    question_path = flask.request.args.get('question')

    if not question_path:
        raise MissingParameter("question", type="query")

    question_path = map(int, question_path.split("."))
    question = Question.getByPath(session, paper, question_path)

    if flask.request.method == "POST":
        question.content = flask.request.form["content"]

        session.add(question)
        session.commit()

        return flask.redirect(flask.url_for('get_paper', 
            module=module.code, year=paper.year_start, period=paper.period, format="html") + "#Q" + '.'.join(map(str, question.path)))
    else:
        return flask.render_template('module.html', module=module, paper=paper, edit_question=question)

@app.route("/modules/<category>/")
def list_category_modules(category):
    category = Category.getByCode(session, category)
    return flask.render_template('modules.html', category=category)

@app.route("/institution/<institution>/")
def get_institution(institution):
    institution = Institution.getByCode(session, institution)
    return flask.render_template('institution.html', institution=institution)

@app.route("/")
def get_index():
    modules = session.query(Module).filter(Module.indexed == True).all()
    return flask.render_template('index.html', modules=modules)

# Error handlers
@app.errorhandler(NotFound)
def handle_not_found(error):
    return fail(404, error.message)

@app.errorhandler(InvalidInput)
def handle_invalid_input(error):
    return fail(400, error.message)

@app.errorhandler(HttpException)
def handle_http_exception(error):
    return fail(error.status_code, error.message)

if __name__ == '__main__':
    if APP_LOG:
        handler = RotatingFileHandler(APP_LOG, maxBytes=10000, backupCount=1)
        handler.setLevel(logging.DEBUG)
        logging.getLogger('werkzeug').addHandler(handler)
        app.logger.addHandler(handler)

    app.run(port=APP_PORT, host=APP_HOST, debug=APP_DEBUG)
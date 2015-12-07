import flask
import logging
import os.path
from babel.dates import format_datetime
from logging.handlers import RotatingFileHandler
from flask import Flask
from project.src.web.exception import HttpException, MissingParameter
from project.src.model import Module, Paper, Category, Institution, Question, Visitor, Revision
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

@app.after_request
def after_request(res):
    # TODO: Find a solution to this
    # Sane templating requires the use of setattr
    # for object and SQL Alchemy state management
    # stores object persistently across queries.
    # Bad news. It fucks up the views. We need expire
    # everything every request (DEAR LORD) or find a solution
    session.expire_all()

    return res

@app.route('/module/<module>/')
def get_module(module):
    module = Module.getByCode(session, module)

    # Fail if the module is not indexed
    if not module.is_indexed():
        return fail(403, "Module {} has not been indexed yet.".format(module.code))

    # Get the popular questions
    popular = module.get_popular_questions()

    for q, sim in popular:
        setattr(q, 'view_single', True)

    return flask.render_template('module.html', module=module, popular=popular)

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
        return flask.render_template('module_paper.html', module=module, paper=paper)

@app.route('/module/<module>/<year>/<period>/<action>', methods=['get', 'post'])
def question(module, year, period, action):
    module = Module.getByCode(session, module)
    paper = Paper.find(session, module, year, period)

    question_path = flask.request.args.get('question')

    if not question_path:
        raise MissingParameter("question", type="query")

    question_path = map(int, question_path.split("."))
    question = Question.getByPath(session, paper, question_path)

    if action == 'history':
        setattr(question, 'view_history', True)
        # Render a question's history
        return flask.render_template('module_history.html', module=module, paper=paper, history_question=question)
    elif action == 'revert':
        revision_id = int(flask.request.args.get('revision'))

        if not revision_id:
            raise MissingParameter('revision', type='query')

        # Find the revision with a new query instead of loading
        # all revisions.
        revision = Revision.findById(session, revision_id)

        # Show the revision history
        question.set_content(flask.g.visitor, revision.content)
        session.add(question)
        session.commit()

        return flask.redirect(flask.url_for('question', module=module.code, year=paper.year_start, period=paper.period, action="history", question=question.joined_path))
    elif action == 'edit':
        if flask.request.method == "POST":
            question.set_content(flask.g.visitor, flask.request.form["content"])

            session.add(question)
            session.commit()

            return flask.redirect(flask.url_for('get_paper', 
                module=module.code, year=paper.year_start, period=paper.period, format="html") + "#Q" + '.'.join(map(str, question.path)))

        # Set the edit flag to expanded
        setattr(question, 'view_edit', True)
    elif action == 'similar':
        for q in question.get_similar():
            setattr(q.question, 'view_similar_expanded_question', True)

        # Set the flag to the question
        setattr(question, 'view_similar_expanded', True)

    # Render
    return flask.render_template('module_paper.html', module=module, paper=paper)


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

@app.template_filter('format_date')
def format_date_filter(time):
    return format_datetime(time)

@app.template_filter('question_action')
def question_action_filter(question, action, direct=True, **kwargs):
    return flask.url_for('question', 
        module=question.paper.module.code, 
        year=question.paper.year, 
        period=question.paper.period, 
        action=action, 
        question=question.joined_path,
        **kwargs) + ("#Q" + question.joined_path if direct else "")

@app.template_filter('question_link')
def question_link_filter(question, direct=True):
    return flask.url_for('get_paper', 
        module=question.paper.module.code, 
        period=question.paper.period, 
        year=question.paper.year, 
        format='html') + ("#Q" + question.joined_path if direct else "")

@app.template_filter('paper_link')
def paper_link_filter(paper, format='html'):
    return flask.url_for('get_paper', 
        module=paper.module.code, 
        year=paper.year, 
        period=paper.period, 
        format=format)

if __name__ == '__main__':
    if APP_LOG:
        handler = RotatingFileHandler(APP_LOG, maxBytes=10000, backupCount=1)
        handler.setLevel(logging.DEBUG)
        logging.getLogger('werkzeug').addHandler(handler)
        app.logger.addHandler(handler)

    app.run(port=APP_PORT, host=APP_HOST, debug=APP_DEBUG)
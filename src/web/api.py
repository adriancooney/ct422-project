import flask
from flask import Flask, abort
from ..model import Module
from ..config import Session
from sqlalchemy.orm.exc import NoResultFound
app = Flask(__name__)

session = Session()

@app.route('/module/<module>', methods=['GET'])
def get_module(module): 
    try:
        # Get the module
        module = session.query(Module).filter(Module.code == module).one()

        return flask.jsonify(module.latest_similarity_analysis())
    except NoResultFound:
        abort(404)

if __name__ == '__main__':
    app.run()
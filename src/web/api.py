from flask import Flask
app = Flask(__name__)

@app.route('/module/<module>', methods=['GET'])
def get_module(): pass

if __name__ == '__main__':
    app.run()
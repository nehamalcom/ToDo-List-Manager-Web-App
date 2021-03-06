import os
from flask import Flask

def create_app(test_config=None):
    # creating and configuring the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'todolist.sqlite'),
    )

    if test_config is None:
        # if not testing, load the instance config
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensuring instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # testing example page
    @app.route('/hello')
    def hello():
        return 'Hello There!'
    
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import todo
    app.register_blueprint(todo.bp)
    # url for blog.index and index will generate same / URL
    app.add_url_rule('/', endpoint='index')

    return app
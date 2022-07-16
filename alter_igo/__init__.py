# initialize flask app
from flask import Flask
from flask_assets import Environment
from flask_sqlalchemy import SQLAlchemy

# initialize database connection
db = SQLAlchemy()


# create flask app
def create_app():
    # initialize core application
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    # initialize plugins
    db.init_app(app)

    # initialize assets
    assets = Environment()
    assets.init_app(app)

    # register blueprints
    with app.app_context():
        from .landing import routes
        from .profile import routes
        from .docs import routes
        from .home import routes
        from .help import routes
        from .assets import compile_static_assets

        app.register_blueprint(landing.landing_bp)
        app.register_blueprint(profile.profile_bp)
        app.register_blueprint(docs.docs_bp)
        app.register_blueprint(home.home_bp)
        app.register_blueprint(help.help_bp)

        compile_static_assets(assets)

        return app

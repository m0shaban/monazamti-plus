from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Add custom Jinja filters
    @app.template_filter('slice')
    def slice_filter(iterable, start, stop):
        return list(iterable)[start:stop]

    from app import routes, models, auth
    app.register_blueprint(routes.bp)
    app.register_blueprint(auth.bp)

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    return app

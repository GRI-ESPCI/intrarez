"""Intranet de la Rez Flask Web App (intrarez)

See github.com/GRI-ESPCI/intrarez for informations.
"""

__title__ = "intrarez"
__author__ = "Loïc Simon & other GRIs"
__license__ = "MIT"
__copyright__ = "Copyright 2021 GRIs – ESPCI Paris - PSL"
__version__ = "0.1.1"
__all__ = ["app"]


import logging

import flask
import flask_sqlalchemy
import flask_migrate
import flask_login
import flask_mail
import flask_moment
import flask_babel
from flask_babel import lazy_gettext as _l
import wtforms

from config import Config
from app._tools import loggers


# Load extensions
db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate()
login = flask_login.LoginManager()
login.login_view = "auth.login"         # login route function
login.login_message = _l("Merci de vous connecter pour accéder à cette page.")
login.login_message_category = "warning"
mail = flask_mail.Mail()
moment = flask_moment.Moment()
babel = flask_babel.Babel()


def create_app(config_class=Config):
    """Create and initialize a new Flask application instance."""
    # Initialize application
    app = flask.Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    app.jinja_env.add_extension("jinja2.ext.do")
    app.jinja_env.globals["get_locale"] = get_locale
    app.jinja_env.globals["alert_labels"] = {
        "info": _l("Information :"),
        "success": _l("Succès :"),
        "danger": _l("Attention :"),
        "warning": _l("Avertissement :"),
    }
    app.jinja_env.globals["alert_symbols"] = {
        "info": "info-circle-fill",
        "success": "check-circle-fill",
        "danger": "exclamation-triangle-fill",
        "warning": "exclamation-triangle-fill",
    }
    app.jinja_env.globals['bootstrap_is_hidden_field'] = (
        lambda field: isinstance(field, wtforms.fields.HiddenField)
    )

    # ! Keep import here to avoid circular import issues !
    from app import errors, main, auth
    app.register_blueprint(errors.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)

    # Set up error handling
    if not app.debug and not app.testing:
        loggers.set_handlers(app.logger, app.config)
        app.logger.info("Intrarez startup")

    return app


# Set up locale
@babel.localeselector
def get_locale():
    """Get the application language prefered by the remote user."""
    return flask.request.accept_languages.best_match(
        flask.current_app.config["LANGUAGES"]
    )


# Import application models
# ! Keep at the bottom to avoid circular import issues !
from app import models

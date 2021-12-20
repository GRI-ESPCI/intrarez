"""Intranet de la Rez Flask Web App (intrarez)

See github.com/GRI-ESPCI/intrarez for informations.
"""

__title__ = "intrarez"
__author__ = "Loïc Simon, Louis Grandvaux & other GRIs"
__license__ = "MIT"
__copyright__ = "Copyright 2021 GRIs – ESPCI Paris - PSL"
__all__ = "create_app"


import json

with open("package.json", "r") as fp:
    __version__ = json.load(fp).get("version", "Undefined")

import flask
import flask_sqlalchemy
import flask_migrate
import flask_login
import flask_mail
import flask_moment
import flask_babel
from flask_babel import lazy_gettext as _l
from werkzeug import urls as wku
import wtforms

from config import Config
from app import enums
from app.tools import loggers, utils


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
    """Create and initialize a new Flask application instance.

    Args:
        config_class (type): The configuration class to use.
            Default: :class:`.config.Config`.
    """
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
    app.jinja_env.globals.update(**__builtins__)
    app.jinja_env.globals.update(**{name: getattr(enums, name)
                                    for name in enums.__all__})
    app.jinja_env.globals["__version__"] = __version__
    app.jinja_env.globals["get_locale"] = utils.get_locale
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
    app.jinja_env.globals["bootstrap_icon"] = utils.get_bootstrap_icon
    app.jinja_env.globals['bootstrap_is_hidden_field'] = (
        lambda field: isinstance(field, wtforms.fields.HiddenField)
    )

    # ! Keep imports here to avoid circular import issues !
    from app import errors, main, auth, devices, rooms, gris
    app.register_blueprint(errors.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(devices.bp, url_prefix="/devices")
    app.register_blueprint(rooms.bp, url_prefix="/rooms")
    app.register_blueprint(gris.bp, url_prefix="/gris")

    # Set up error handling
    loggers.set_handlers(app)
    app.logger.info("Intrarez startup")

    # Set up captive portal
    @app.before_request
    def captive_portal():
        """Captive portal: redirect external requests to homepage."""
        netlocs = app.config["NETLOCS"]
        if netlocs is None or app.debug or app.testing:
            # Captive portal disabled or testing: process all requests
            return None
        if flask.request.endpoint:
            # No infinite redirections loop
            return None
        if wku.url_parse(flask.request.url).netloc not in netlocs:
            # Requested URL not in netlocs: redirect
            return utils.safe_redirect("main.index")
        # Valid URL
        return None

    # Set up custom context creation
    # ! Keep import here to avoid circular import issues !
    from app import context
    app.before_request(context.create_request_context)

    # Set up custom logging
    @app.after_request
    def logafter(response):
        """Add a logging entry describing the response served."""
        if flask.request.endpoint != "static":
            endpoint = flask.request.endpoint or f"[CP:<{flask.request.url}>]"
            if response.status_code < 400:          # Success
                msg = f"Served '{endpoint}'"
                if response.status_code >= 300:     # Redirect
                    msg += " [redirecting]"
            else:                                   # Error
                msg = f"Served error page ({flask.request}: {response.status})"

            remote_ip = flask.request.headers.get("X-Real-Ip", "<unknown IP>")
            if flask.g.logged_in:
                user = repr(flask_login.current_user)
                if flask.g.doas:
                    user += f" AS {flask.g.rezident!r}"
            else:
                user = "<anonymous>"
            msg += f" to {remote_ip} ({user})"
            app.logger.info(msg)
        return response

    return app


# Set up locale
babel.localeselector(utils.get_locale)

# Import application models
# ! Keep at the bottom to avoid circular import issues !
from app import models

# Set up user loader locale
@login.user_loader
def load_user(id):
    """Function used by Flask-login to get the connected user.

    Args:
        id (str): the ID of the connected user (stored in the session).

    Returns:
        :class:`Rezident`
    """
    if not id.isdigit():
        return False
    user = models.Rezident.query.get(int(id))
    return user

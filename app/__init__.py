"""Intranet de la Rez Flask Web App (intrarez)

See github.com/GRI-ESPCI/intrarez for informations.
"""

__title__ = "intrarez"
__author__ = "Loïc Simon, Louis Grandvaux & other GRIs"
__license__ = "MIT"
__copyright__ = "2021-2022 GRIs – ESPCI Paris - PSL"
__all__ = ["create_app"]


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
from werkzeug import urls as wku

from config import Config
from app import enums


in_app_copyright = "2021-2022 GRI ESPCI"


# Define Flask subclass
class IntraRezApp(flask.Flask):
    """:class:`flask.Flask` subclass. Only adds anew logger:

    Attrs:
        actions_logger (logging.Logger): Child of app logger used to
            report important actions (see :mod:`.tools.loggers`).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add rezidents actions logger
        self.actions_logger = self.logger.getChild("actions")


# Imports needing IntraRezApp - don't move!
from app.tools import loggers, utils, typing

# Load extensions
db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate()
login = flask_login.LoginManager()
mail = flask_mail.Mail()
moment = flask_moment.Moment()
babel = flask_babel.Babel()


def create_app(config_class: type = Config) -> IntraRezApp:
    """Create and initialize a new Flask application instance.

    Args:
        config_class (type): The configuration class to use.
            Default: :class:`.config.Config`.
    """
    # Initialize application
    app = IntraRezApp(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    # Set up Jinja
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.globals.update(**__builtins__)
    app.jinja_env.globals.update(
        **{name: getattr(enums, name) for name in enums.__all__}
    )
    app.jinja_env.globals["__version__"] = __version__
    app.jinja_env.globals["copyright"] = in_app_copyright
    app.jinja_env.globals["babel"] = flask_babel
    app.jinja_env.globals["promotions"] = utils.promotions

    # Register blueprints
    # ! Keep imports here to avoid circular import issues !
    from app.routes import auth, devices, errors, gris, main, payments, profile, rooms

    app.register_blueprint(errors.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(devices.bp, url_prefix="/devices")
    app.register_blueprint(rooms.bp, url_prefix="/rooms")
    app.register_blueprint(gris.bp, url_prefix="/gris")
    app.register_blueprint(payments.bp, url_prefix="/payments")
    app.register_blueprint(profile.bp, url_prefix="/profile")

    # Configure logging
    loggers.configure_logging(app)
    app.logger.info("Intrarez startup")

    # Set up mail processors building
    # ! Keep import here to avoid circular import issues !
    from app import email

    app.before_first_request(email.init_premailer)
    app.before_first_request(email.init_textifier)

    # Set up captive portal
    @app.before_request
    def _captive_portal() -> typing.RouteReturn | None:
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
            return context.capture()
        # Valid URL
        return None

    # Set up custom context creation
    # ! Keep import here to avoid circular import issues !
    from app import context

    app.before_request(context.create_request_context)

    # Set up custom logging
    @app.after_request
    def _log_after(response: flask.Response) -> flask.Response:
        """Add a logging entry describing the response served."""
        if flask.request.endpoint != "static":
            endpoint = flask.request.endpoint or f"[CP:<{flask.request.url}>]"
            if response.status_code < 400:  # Success
                msg = f"Served '{endpoint}'"
                if response.status_code >= 300:  # Redirect
                    msg += " [redirecting]"
            else:  # Error
                msg = f"Served error page ({flask.request}: {response.status})"

            remote_ip = flask.request.headers.get("X-Real-Ip", "<unknown IP>")
            user = "<anonymous>"
            try:
                if flask.g.logged_in:
                    user = repr(flask.g.logged_in_user)
                    if flask.g.doas:
                        user += f" AS {flask.g.rezident!r}"
            except AttributeError:
                pass
            msg += f" to {remote_ip} ({user})"
            app.logger.info(msg)
        return response

    # All set!
    return app


# Import application models
# ! Keep at the bottom to avoid circular import issues !
from app import models


# Set up locale
@babel.localeselector
def _get_locale() -> str | None:
    """Get the application language preferred by the remote user."""
    locale = flask.request.accept_languages.best_match(
        flask.current_app.config["LANGUAGES"]
    )
    if flask.g.logged_in and locale != flask.g.logged_in_user.locale:
        # Do not use flask.g.rezident here, it would override user locale
        # by the locale of a GRI using doas
        flask.g.logged_in_user.locale = locale
        db.session.commit()

    return locale


# Set up user loader
@login.user_loader
def _load_user(id: str) -> models.Rezident | None:
    """Function used by Flask-login to get the connected user.

    Args:
        id (str): the ID of the connected user (stored in the session).

    Returns:
        :class:`Rezident` | ``None``
    """
    if not id.isdigit():
        return None
    return models.Rezident.query.get(int(id))

"""Intranet de la Rez - Main Pages Routes"""

import datetime

import flask
import flask_login
from flask_babel import _

from app import db
from app.main import bp


# @bp.before_app_request
# def before_request():
#     if current_user.is_authenticated:
#         current_user.last_seen = datetime.datetime.utcnow()
#         db.session.commit()

@bp.route("/")
@bp.route("/index")
def index():
    """IntraRez home page."""
    return flask.render_template("main/index.html", title=_("Oui."))

@bp.route("/profile")
@flask_login.login_required
def profile():
    """IntraRez profile page."""
    return flask.render_template("main/index.html", title=_("Profil"))

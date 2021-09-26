"""Intranet de la Rez - Error Pages"""

import flask

from app import db
from app.errors import bp


@bp.app_errorhandler(404)
def not_found_error(error):
    return flask.render_template("errors/404.html"), 404

@bp.app_errorhandler(405)
def not_found_error(error):
    return flask.render_template("errors/405.html"), 405

@bp.app_errorhandler(418)
def not_found_error(error):
    return "Would you like a cup of tea?", 418

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return flask.render_template("errors/500.html"), 500

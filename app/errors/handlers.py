"""Intranet de la Rez - Error Pages"""

import traceback

import flask
from flask_babel import _
from werkzeug.exceptions import HTTPException

from app import db
from app.errors import bp


@bp.app_errorhandler(401)
def unauthorized_error(error):
    err_name = f"{error.code} {error.name}"
    err_descr = error.description
    flask.current_app.logger.error(f"{err_name} -- {flask.request}")
    return flask.render_template("errors/401.html", err_name=err_name,
                                 err_descr=err_descr,
                                 title=_("Accès restreint")), 401

@bp.app_errorhandler(403)
def forbidden_error(error):
    err_name = f"{error.code} {error.name}"
    err_descr = error.description
    flask.current_app.logger.error(f"{err_name} -- {flask.request}")
    return flask.render_template("errors/403.html", err_name=err_name,
                                 err_descr=err_descr,
                                 title=_("Accès restreint")), 403

@bp.app_errorhandler(404)
def not_found_error(error):
    err_name = f"{error.code} {error.name}"
    err_descr = error.description
    flask.current_app.logger.error(f"{err_name} -- {flask.request}")
    return flask.render_template("errors/404.html", err_name=err_name,
                                 err_descr=err_descr, title=err_name), 404

@bp.app_errorhandler(418)
def theiere_error(error):
    return "Would you like a cup of tea?", 418

@bp.app_errorhandler(Exception)
def other_error(error):
    if isinstance(error, HTTPException):
        code = error.code
        err_name = f"{error.code} {error.name}"
        err_descr = error.description
        flask.current_app.logger.error(f"{err_name} -- {flask.request}")
    else:
        code = 500
        err_name = "Python Exception"
        err_descr = "A Python exception stopped the execution of the request."
        try:
            is_gri = flask.g.is_gri
        except AttributeError:      
            # Very early error
            is_gri = False
        if is_gri:
            # GRI: show traceback
            tb = str(flask.escape(traceback.format_exc()))
            tb = flask.Markup(tb.replace("\n", "<br/>").replace(" ", "&nbsp;"))
            err_descr = "[debug mode - traceback below]" + flask.Markup(
                flask.render_template("errors/_tb.html", tb=tb)
            )
        flask.current_app.logger.error(traceback.format_exc())
    db.session.rollback()
    return flask.render_template("errors/other.html", err_name=err_name,
                                 err_descr=err_descr, title=err_name), code

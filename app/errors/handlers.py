"""Intranet de la Rez - Error Pages"""

import traceback

import flask
from flask_babel import _
from werkzeug.exceptions import HTTPException

from app import db
from app.errors import bp
from app.tools import typing


@bp.app_errorhandler(401)
def unauthorized_error(error: HTTPException) -> typing.RouteReturn:
    err_name = f"{error.code} {error.name}"
    err_descr = error.description
    flask.current_app.logger.warning(f"{err_name} -- {flask.request}")
    return flask.render_template("errors/401.html", err_name=err_name,
                                 err_descr=err_descr,
                                 title=_("Accès restreint")), 401


@bp.app_errorhandler(403)
def forbidden_error(error: HTTPException) -> typing.RouteReturn:
    err_name = f"{error.code} {error.name}"
    err_descr = error.description
    flask.current_app.logger.warning(f"{err_name} -- {flask.request}")
    return flask.render_template("errors/403.html", err_name=err_name,
                                 err_descr=err_descr,
                                 title=_("Accès restreint")), 403


@bp.app_errorhandler(404)
def not_found_error(error: HTTPException) -> typing.RouteReturn:
    err_name = f"{error.code} {error.name}"
    err_descr = error.description
    flask.current_app.logger.warning(f"{err_name} -- {flask.request}")
    return flask.render_template("errors/404.html", err_name=err_name,
                                 err_descr=err_descr, title=err_name), 404


@bp.app_errorhandler(418)
def theiere_error(error: HTTPException) -> typing.RouteReturn:
    return "Would you like a cup of tea?", 418


@bp.app_errorhandler(503)
def service_unavailable_error(error: HTTPException) -> typing.RouteReturn:
    err_name = f"{error.code} {error.name}"
    err_descr = error.description
    if flask.current_app.config["MAINTENANCE"]:
        flask.current_app.logger.info(f"{err_name} -- {flask.request}")
    else:
        flask.current_app.logger.error(f"{err_name} -- {flask.request}")
    return flask.render_template("errors/503.html", err_name=err_name,
                                 err_descr=err_descr, title=err_name), 503


@bp.app_errorhandler(Exception)
def other_error(error: Exception) -> typing.RouteReturn:
    if isinstance(error, HTTPException):
        code = error.code or 500
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
            tb_str = str(flask.escape(traceback.format_exc()))
            tb = flask.Markup(
                tb_str.replace("\n", "<br/>").replace(" ", "&nbsp;")
            )
            err_descr = "[debug mode - traceback below]" + flask.Markup(
                flask.render_template("errors/_tb.html", tb=tb)
            )
        flask.current_app.logger.error(traceback.format_exc())
    db.session.rollback()
    return flask.render_template("errors/other.html", err_name=err_name,
                                 err_descr=err_descr, title=err_name), code

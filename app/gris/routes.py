"""Intranet de la Rez - Gris Pages Routes"""

import functools

import flask
import flask_login
from flask_babel import _

from app import db
from app.gris import bp, forms
from app.devices import check_device
from app.tools.utils import redirect_to_next
from app.models import Rezident


def gris_only(routine):
    """Route function decorator to restrict access to GRIs.

    Args:
        routine (function): The route function to restrict access to.

    Returns:
        The protected routine.
    """
    @functools.wraps(routine)
    def new_routine():
        # On vérifie que l'utilisateur est connecté...
        if not flask_login.current_user.is_authenticated:
            return flask.redirect(flask.url_for("auth.login"),
                                  next=flask.request.endpoint)

        # ...et qu'il est GRI
        if not flask_login.current_user.is_gri:
            flask.abort(403)

        return routine()

    return new_routine


@bp.route("/rezidents")
@check_device
@gris_only
def rezidents():
    """Users list page."""
    return flask.render_template("gris/rezidents.html",
                                 users=Rezident.query.all(),
                                 title=_("Liste des Rezidents"))

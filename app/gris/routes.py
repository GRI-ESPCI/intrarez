"""Intranet de la Rez - Gris Pages Routes"""

import flask
from flask_babel import _

from app import context
from app.gris import bp
from app.models import Rezident


@bp.route("/rezidents")
@context.gris_only
def rezidents():
    """Users list page."""
    return flask.render_template("gris/rezidents.html",
                                 users=Rezident.query.all(),
                                 title=_("Liste des Rezidents"))


@bp.route("/monitoring_ds")
@context.gris_only
def monitoring_ds():
    """Integration of Darkstat network monitoring."""
    return flask.render_template("gris/monitoring_ds.html",
                                 title=_("Darkstat network monitoring"))


@bp.route("/monitoring_bw")
@context.gris_only
def monitoring_bw():
    """Integration of Bandwidthd network monitoring."""
    return flask.render_template("gris/monitoring_bw.html",
                                 title=_("Bandwidthd network monitoring"))

"""Intranet de la Rez - Gris Pages Routes"""

import contextlib
import io
import traceback
import sys

import flask
from flask_babel import _

from app import context
from app.gris import bp, forms
from app.models import Rezident
from app.tools import utils


@bp.route("/rezidents")
@context.gris_only
def rezidents():
    """Rezidents list page."""
    return flask.render_template("gris/rezidents.html",
                                 rezidents=Rezident.query.all(),
                                 title=_("Gestion des Rezidents"))


@bp.route("/run_script", methods=["GET", "POST"])
@context.gris_only
def run_script():
    form = forms.ChoseScriptForm()
    """Run an IntraRez script."""
    if form.validate_on_submit():
        # Exécution du script
        try:
            _stdin = sys.stdin
            sys.stdin = io.StringIO()   # Block script for wainting for stdin
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with contextlib.redirect_stderr(sys.stdout):
                    utils.run_script(form.script.data)
        except Exception:
            output = stdout.getvalue() + traceback.format_exc()
        else:
            output = stdout.getvalue()
        finally:
            sys.stdin = _stdin

        output = str(flask.escape(output))
        output = flask.Markup(output.replace("\n", "<br/>").replace(" ",
                                                                    "&nbsp;"))
        return flask.render_template("gris/run_script.html", form=form,
                                     output=output,
                                     title=_("Exécuter un script"))
    return flask.render_template("gris/run_script.html", form=form,
                                 output=None,
                                 title=_("Exécuter un script"))


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

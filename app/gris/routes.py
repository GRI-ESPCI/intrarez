"""Intranet de la Rez - Gris Pages Routes"""

import contextlib
import datetime
import io
import traceback
import sys

import flask
from flask_babel import _

from app import context, db
from app.gris import bp, forms
from app.models import Rezident, Ban
from app.tools import utils, typing


@bp.route("/rezidents", methods=["GET", "POST"])
@context.gris_only
def rezidents() -> typing.RouteReturn:
    """Rezidents list page."""
    form = forms.BanForm()
    if form.validate_on_submit():
        if form.ban_id.data:
            ban = Ban.query.get(int(form.ban_id.data))
            if form.unban.data:
                # Terminate existing ban
                ban.end = datetime.datetime.utcnow()
                utils.log_action(f"Terminated {ban}")
                flask.flash(_("Le ban a été terminé."), "success")
            else:
                # Update existing ban
                ban.end = form.get_end(ban.start)
                ban.reason = form.reason.data
                ban.message = form.message.data
                utils.log_action(f"Modified {ban}: {ban.end} / {ban.reason}")
                flask.flash(_("Le ban a bien été modifié."), "success")
        else:
            # New ban
            rezident = Rezident.query.get(int(form.rezident.data))
            if rezident.is_banned:
                flask.flash(_("Ce rezident est déjà banni !"), "danger")
            else:
                start = datetime.datetime.utcnow()
                end = form.get_end(start)
                ban = Ban(
                    rezident=rezident,
                    start=start,
                    end=end,
                    reason=form.reason.data,
                    message=form.message.data,
                )
                db.session.add(ban)
                utils.log_action(f"Added {ban}: {ban.end} / {ban.reason}")
                flask.flash(_("Le mécréant a bien été banni."), "success")
        db.session.commit()
        utils.run_script("gen_dhcp.py")  # Update DHCP rules

    return flask.render_template(
        "gris/rezidents.html",
        form=form,
        rezidents=Rezident.query.all(),
        title=_("Gestion des Rezidents"),
    )


@bp.route("/run_script", methods=["GET", "POST"])
@context.gris_only
def run_script() -> typing.RouteReturn:
    """Run an IntraRez script."""
    form = forms.ChoseScriptForm()
    if form.validate_on_submit():
        script = form.script.data
        utils.log_action(f"Executing script from GRI menu: {script}")
        # Exécution du script
        _stdin = sys.stdin
        sys.stdin = io.StringIO()  # Block script for wainting for stdin
        try:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with contextlib.redirect_stderr(sys.stdout):
                    try:
                        utils.run_script(script)
                    except Exception as exc:
                        utils.log_action(f" -> ERROR: {exc}", warning=True)
                        output = stdout.getvalue() + traceback.format_exc()
                    else:
                        output = stdout.getvalue()
        finally:
            sys.stdin = _stdin

        output_str = str(flask.escape(output))
        output = flask.Markup(output_str.replace("\n", "<br/>").replace(" ", "&nbsp;"))
        return flask.render_template(
            "gris/run_script.html",
            form=form,
            output=output,
            title=_("Exécuter un script"),
        )
    return flask.render_template(
        "gris/run_script.html", form=form, output=None, title=_("Exécuter un script")
    )


@bp.route("/monitoring_ds")
@context.gris_only
def monitoring_ds() -> typing.RouteReturn:
    """Integration of Darkstat network monitoring."""
    return flask.render_template(
        "gris/monitoring_ds.html", title=_("Darkstat network monitoring")
    )


@bp.route("/monitoring_bw")
@context.gris_only
def monitoring_bw() -> typing.RouteReturn:
    """Integration of Bandwidthd network monitoring."""
    return flask.render_template(
        "gris/monitoring_bw.html", title=_("Bandwidthd network monitoring")
    )

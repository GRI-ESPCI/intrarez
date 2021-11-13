"""Intranet de la Rez - Main Pages Routes"""

import datetime
import json
import subprocess
import re

import flask
import flask_login
from flask_babel import _
from discord_webhook import DiscordWebhook

from app import db
from app.main import bp, forms
from app.devices import check_device


@bp.route("/")
@bp.route("/index")
@check_device
def index():
    """IntraRez home page."""
    return flask.render_template("main/index.html", title=_("Accueil"))

@bp.route("/contact", methods=["GET", "POST"])
def contact():
    """IntraRez contact page."""
    with open("app/static/gris.json", "r") as fp:
        gris = json.load(fp)

    form = forms.ContactForm()
    if form.validate_on_submit():
        role_id = flask.current_app.config["GRI_ROLE_ID"]
        webhook = DiscordWebhook(
            url=flask.current_app.config["MESSAGE_WEBHOOK"],
            content=f"<@&{role_id}> Nouveau message !",
        )
        webhook.add_embed(form.create_embed())
        try:
            webhook.execute()
        except Exception as exc:
            flask.flash(flask.Markup(_(
                "Oh non ! Le message n'a pas pu être transmis. N'hésitez pas "
                "à contacter un GRI aux coordonnées en bas de page.<br/>"
                "(Type d'erreur : ") + f"<code>{type(exc).__name__}</code>)"),
                "danger"
            )
        else:
            flask.flash(_("Message transmis !"), "success")
            return flask.redirect(flask.url_for("main.index"))

    return flask.render_template("main/contact.html", title=_("Contact"),
                                 form=form, gris=gris)

@bp.route("/legal")
def legal():
    """IntraRez legal page."""
    return flask.render_template("main/legal.html",
                                 title=_("Mentions légales"))

@bp.route("/test")
@check_device
def test():
    """Test page."""
    # return flask.render_template("errors/other.html")
    # flask.abort(403)
    raise RuntimeError("obanon")
    # flask.flash("Succès", "success")
    # flask.flash("Info", "info")
    # flask.flash("Warning", "warning")
    # flask.flash("Danger", "danger")
    pt = {}
    pt["BRF"] = flask.current_app.before_request_funcs
    pt["ARF"] = flask.current_app.after_request_funcs
    for name in dir(flask.request):
        if name.startswith("_"):
            continue
        obj = getattr(flask.request, name)
        if not callable(obj):
            pt[name] = obj

    return flask.render_template("main/test.html", title=_("Test"), pt=pt)

@bp.route("/profile")
@check_device
def profile():
    """IntraRez profile page."""
    return flask.render_template("main/profile.html", title=_("Profil"))


@bp.route("/home")
@check_device
def rickroll():
    """The old good days..."""
    with open("logs/rickrolled.log", "a") as fh:
        fh.write(f"{datetime.datetime.now()}: rickrolled "
                 f"{flask_login.current_user.full_name}\n")
    return flask.redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

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


# @bp.before_app_request
# def before_request():
#     if current_user.is_authenticated:
#         current_user.last_seen = datetime.datetime.utcnow()
#         db.session.commit()

@bp.route("/")
@bp.route("/index")
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
def test():
    """Test page."""
    # flask.flash("Succès", "success")
    # flask.flash("Info", "info")
    # flask.flash("Warning", "warning")
    # flask.flash("Danger", "danger")
    pt = {}
    for name in dir(flask.request):
        if name.startswith("_"):
            continue
        obj = getattr(flask.request, name)
        if not callable(obj):
            pt[name] = obj

    caller = flask.request.headers.get("X-Real-Ip")
    if not caller:
        flask.flash("No caller (test mode?)", "danger")
    else:
        result = subprocess.run(["/sbin/arp", "-a"], capture_output=True)
        flask.flash(flask.Markup(
            "<code>arp-a</code> result:<br/>"
            f"<pre>{result}</pre>"), "info")
        mtch = re.search(rf"^.*? \({caller}\) at ([0-9a-f:]{{17}}) .*",
                         result.stdout.decode(), re.M)
        if mtch:
            flask.flash(f"Your MAC address is: {mtch.group(1)}", "success")
        else:
            flask.flash("Unable to find your MAC adress :(", "warning")

    return flask.render_template("main/test.html", title=_("Test"), pt=pt)

@bp.route("/profile")
@flask_login.login_required
def profile():
    """IntraRez profile page."""
    return flask.render_template("main/index.html", title=_("Profil"))

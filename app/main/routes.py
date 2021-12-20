"""Intranet de la Rez - Main Pages Routes"""

import datetime
import json

import flask
from flask_babel import _
from discord_webhook import DiscordWebhook
import premailer

from app import context, email
from app.main import bp, forms
from app.tools import captcha, utils


@bp.route("/")
@bp.route("/index")
@context.all_good_only
def index():
    """IntraRez home page for the internal network."""
    return flask.render_template("main/index.html", title=_("Accueil"))


@bp.route("/external_home")
def external_home():
    """IntraRez homepage for the Internet."""
    if flask.g.internal:
        return utils.safe_redirect("auth.auth_needed")

    return flask.render_template("main/external_home.html",
                                 title=_("Bienvenue sur l'IntraRez !"))


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    """IntraRez contact page."""
    with open("app/static/gris.json") as fp:
        gris = json.load(fp)

    form = forms.ContactForm()
    if form.validate_on_submit():
        if (not flask.g.internal) and (not captcha.verify_captcha()):
            flask.flash(_("Le capctcha n'a pas pu être vérifié. "
                          "Veuillez réessayer."), "danger")
        else:
            role_id = flask.current_app.config["GRI_ROLE_ID"]
            webhook = DiscordWebhook(
                url=flask.current_app.config["MESSAGE_WEBHOOK"],
                content=f"<@&{role_id}> Nouveau message !",
            )
            webhook.add_embed(form.create_embed())
            rep = webhook.execute()
            if rep:
                flask.flash(_("Message transmis !"), "success")
                return utils.safe_redirect("main.index")

            flask.flash(flask.Markup(_(
                "Oh non ! Le message n'a pas pu être transmis. N'hésitez pas "
                "à contacter un GRI aux coordonnées en bas de page.<br/>"
                "(Erreur : ") + f"<code>{rep.code} / {rep.text}</code>)"),
                "danger"
            )

    return flask.render_template("main/contact.html", title=_("Contact"),
                                 form=form, gris=gris)


@bp.route("/legal")
def legal():
    """IntraRez legal page."""
    return flask.render_template("main/legal.html",
                                 title=_("Mentions légales"))


@bp.route("/changelog")
def changelog():
    """IntraRez changelog page."""
    return flask.render_template("main/changelog.html",
                                 title=_("Notes de mise à jour"),
                                 datetime=datetime)


@bp.route("/profile")
@context.all_good_only
def profile():
    """IntraRez profile page."""
    return flask.render_template("main/profile.html", title=_("Profil"))


@bp.route("/connect_check")
@context.internal_only
def connect_check():
    """Connect check page."""
    return flask.render_template("main/connect_check.html",
                                 title=_("Accès à Internet"))


@bp.route("/home")
def rickroll():
    """The old good days..."""
    if flask.g.logged_in:
        with open("logs/rickrolled.log", "a") as fh:
            fh.write(f"{datetime.datetime.now()}: rickrolled "
                     f"{flask.g.rezident.full_name}\n")
    return flask.redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@bp.route("/test")
@context.gris_only
def test():
    """Test page."""
    # return flask.render_template("errors/other.html")
    # flask.abort(403)
    # raise RuntimeError("obanon")
    flask.flash("Succès", "success")
    flask.flash("Info", "info")
    flask.flash("Warning", "warning")
    flask.flash("Danger", "danger")
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


@bp.route("/mail")
@context.gris_only
def mail():
    """Mails test route"""
    user = flask.g.rezident
    subject = "[IntraRez] Réinitialisation du mot de passe"
    sender = "IntraRez <intrarez@pc-est-magique.fr>"
    recipients = [f"{user.full_name} <{user.email}>"]
    token = "kfsdklmfkdslm"
    text_body = flask.render_template("mails/reset_password.txt",
                                      user=user, token=token)
    html_body = premailer.transform(
        flask.render_template("mails/test.html"),
        base_url="https://intrarez.pc-est-magique.fr/",
        allow_loading_external_files=True,
        remove_classes=True,
        external_styles=[
            flask.url_for("static",
                          filename="css/compiled/custom-bootstrap.css"),
            flask.url_for("static", filename="css/custom.css")
        ],
        disable_validation=True,
        disable_leftover_css=True
    )
    email.send_email(subject, sender, recipients, text_body, html_body)
    return html_body

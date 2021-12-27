"""Intranet de la Rez - Authentication Routes"""

import re

import flask
import flask_login
from flask_babel import _
import unidecode

from app import context, db
from app.auth import bp, forms, email
from app.models import Rezident
from app.tools import utils


def new_username(form):
    """Create a user unique username from a registration form."""
    pnom = form.prenom.data.lower()[0] + form.nom.data.lower()[:7]
    base_username = re.sub(r"\W", "", unidecode.unidecode(pnom), re.A)
    # Check if username already exists
    username = base_username
    discr = 0
    while Rezident.query.filter_by(username=username).first():
        discr += 1
        username = base_username + str(discr)
    return username


@bp.route("/auth_needed")
def auth_needed():
    """Authentification needed page."""
    if not flask.g.internal:
        return utils.safe_redirect("main.external_home")

    return flask.render_template("auth/auth_needed.html",
                                 title=_("Accès à Internet"))


@bp.route("/register", methods=["GET", "POST"])
@context.internal_only
def register():
    """IntraRez registration page."""
    if flask.g.logged_in:
        return utils.redirect_to_next()

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        username = new_username(form)
        user = Rezident(
            username=username, nom=form.nom.data.title(),
            prenom=form.prenom.data.title(),
            promo=form.promo.data, email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flask.flash(_("Compte créé avec succès !"), "success")
        flask_login.login_user(user, remember=False)
        return utils.redirect_to_next()

    return flask.render_template("auth/register.html",
                                 title=_("Nouveau compte"), form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """IntraRez login page."""
    if flask.g.logged_in:
        return utils.redirect_to_next()

    form = forms.LoginForm()
    if form.validate_on_submit():
        # Check user / password
        user = (Rezident.query.filter_by(username=form.login.data).first()
            or Rezident.query.filter_by(email=form.login.data).first())
        if user is None:
            flask.flash(_("Nom d'utilisateur inconnu"), "danger")
        elif not user.check_password(form.password.data):
            flask.flash(_("Mot de passe incorrect"), "danger")
        else:
            # OK
            flask_login.login_user(user, remember=form.remember_me.data)
            flask.flash(_("Connecté !"), "success")
            return utils.redirect_to_next()

    return flask.render_template("auth/login.html", title=_("Connexion"),
                                 form=form)


@bp.route("/logout")
def logout():
    """IntraRez logout page."""
    if flask.g.logged_in:
        flask_login.logout_user()
        flask.flash(_("Vous avez été déconnecté."), "success")

    return utils.redirect_to_next()


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    """IntraRez password reset request page."""
    if flask.g.logged_in:
        return utils.redirect_to_next()

    form = forms.ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Rezident.query.filter_by(email=form.email.data).first()
        if user:
            email.send_password_reset_email(user)
        flask.flash(_("Un email a été envoyé avec les instructions pour "
                      "réinitialiser le mot de passe."), "info")
        return utils.safe_redirect("auth.login")

    return flask.render_template("auth/reset_password_request.html",
                                 title=_("Mot de passe oublié"), form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """IntraRez password reset page (link sent by mail)."""
    if flask.g.logged_in:
        flask.flash(_("Ce lien n'est pas utilisable en étant authentifié."),
                    "warning")
        return utils.redirect_to_next()

    rezident = Rezident.verify_reset_password_token(token)
    if not rezident:
        flask.flash(_("Lien de réinitialisation invalide ou expiré."),
                    "danger")
        return utils.redirect_to_next()

    form = forms.ResetPasswordForm()
    if form.validate_on_submit():
        rezident.set_password(form.password.data)
        db.session.commit()
        flask.flash(_("Le mot de passe a été réinitialisé avec succès."),
                    "success")
        return utils.safe_redirect("auth.login")

    return flask.render_template("auth/reset_password.html",
                                 title=_("Nouveau mot de passe"), form=form)

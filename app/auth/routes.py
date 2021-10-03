"""Intranet de la Rez - Authentication Routes"""

import flask
import flask_login
from flask_babel import _
import unidecode

from app import db
from app.auth import bp, forms, email
from app.models import User
from app.tools.utils import redirect_to_next


def new_username(form):
    """Create a user unique username from a registration form."""
    pnom = form.prenom.data.lower()[0] + form.nom.data.lower()[:7]
    base_username = unidecode.unidecode(pnom)
    # Check if username already exists
    username = base_username
    discr = 0
    while User.query.filter_by(username=username).first():
        discr += 1
        username = base_username + str(discr)
    return username


@bp.route("/register", methods=["GET", "POST"])
def register():
    """IntraRez registration page."""
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("main.index"))

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        username = new_username(form)
        user = User(
            username=username, nom=form.nom.data.title(),
            prenom=form.prenom.data.title(),
            promo=form.promo.data, email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flask.flash(_("Compte créé avec succès !"), "success")
        flask_login.login_user(user, remember=False)
        return redirect_to_next()

    return flask.render_template("auth/register.html",
                                 title=_("Nouveau compte"), form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """IntraRez login page."""
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("main.index"))

    form = forms.LoginForm()
    if form.validate_on_submit():
        # Check user / password
        user = (User.query.filter_by(username=form.login.data).first()
            or User.query.filter_by(email=form.login.data).first())
        if user is None:
            flask.flash(_("Nom d'utilisateur inconnu"), "danger")
            return flask.redirect(flask.url_for("auth.login"))
        elif not user.check_password(form.password.data):
            flask.flash(_("Mot de passe incorrect"), "danger")
            return flask.redirect(flask.url_for("auth.login"))
        # OK
        flask_login.login_user(user, remember=form.remember_me.data)
        flask.flash(_("Connecté !"), "success")
        return redirect_to_next()

    return flask.render_template("auth/login.html", title=_("Connexion"),
                                 form=form)


@bp.route("/logout")
def logout():
    """IntraRez logout page."""
    flask_login.logout_user()
    flask.flash(_("Vous avez été déconnecté."), "success")
    return flask.redirect(flask.url_for("main.index"))


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    """IntraRez password reset request page."""
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("main.index"))

    form = forms.ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            email.send_password_reset_email(user)
        flask.flash(_("Un email a été envoyé avec les instructions pour "
                      "réinitialiser le mot de passe."), "info")
        return flask.redirect(flask.url_for("auth.login"))

    return flask.render_template("auth/reset_password_request.html",
                                 title=_("Mot de passe oublié"), form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """IntraRez password reset page (link sent by mail)."""
    if flask_login.current_user.is_authenticated:
        flask.flash(_("Ce lien n'est pas utilisable en étant authentifié."),
                    "warning")
        return flask.redirect(flask.url_for("main.index"))

    user = User.verify_reset_password_token(token)
    if not user:
        flask.flash(_("Lien de réinitialisation invalide ou expiré."),
                    "danger")
        return flask.redirect(flask.url_for("main.index"))

    form = forms.ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flask.flash(_("Le mot de passe a été réinitialisé avec succès."),
                    "success")
        return flask.redirect(flask.url_for("auth.login"))

    return flask.render_template("auth/reset_password.html",
                                 title=_("Nouveau mot de passe"), form=form)

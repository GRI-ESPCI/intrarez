"""Intranet de la Rez - Profile Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.routes.profile import bp, forms
from app.utils import helpers, typing


@bp.route("/")
@context.all_good_only
def main() -> typing.RouteReturn:
    """IntraRez profile page."""
    return flask.render_template("profile/main.html", title=_("Profil"))


@bp.route("/modify_account", methods=["GET", "POST"])
@context.all_good_only
def modify_account() -> typing.RouteReturn:
    """IntraRez account modification page."""
    form = forms.AccountModificationForm()
    if form.validate_on_submit():
        rezident = flask.g.rezident
        rezident.nom = form.nom.data.title()
        rezident.prenom = form.prenom.data.title()
        rezident.promo = form.promo.data
        rezident.email = form.email.data
        db.session.commit()
        helpers.log_action(
            f"Modified account {rezident} ({rezident.prenom} {rezident.nom} "
            f"{rezident.promo}, {rezident.email})"
        )
        flask.flash(_("Compte modifié avec succès !"), "success")
        return helpers.redirect_to_next()

    return flask.render_template(
        "profile/modify_account.html", title=_("Mettre à jour mon compte"), form=form
    )


@bp.route("/update_password", methods=["GET", "POST"])
@context.all_good_only
def update_password() -> typing.RouteReturn:
    """IntraRez password update page."""
    form = forms.PasswordUpdateForm()
    if form.validate_on_submit():
        if flask.g.rezident.check_password(form.current_password.data):
            flask.g.rezident.set_password(form.password.data)
            db.session.commit()
            helpers.log_action(f"Updated password of {flask.g.rezident}")
            flask.flash(_("Mot de passe mis à jour !"), "success")
            return helpers.redirect_to_next()
        else:
            flask.flash(_("Mot de passe actuel incorrect"), "danger")

    return flask.render_template(
        "profile/update_password.html", title=_("Modifier mon mot de passe"), form=form
    )

"""Intranet de la Rez - Profile Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.profile import bp, forms
from app.models import Rezident
from app.tools import utils


@bp.route("/")
@context.all_good_only
def main():
    """IntraRez profile page."""
    return flask.render_template("profile/main.html", title=_("Profil"))


@bp.route("/modify_account", methods=["GET", "POST"])
@context.all_good_only
def modify_account():
    """IntraRez account modification page."""
    form = forms.AccountModificationForm()
    if form.validate_on_submit():
        rezident = flask.g.rezident
        rezident.nom = form.nom.data.title()
        rezident.prenom = form.prenom.data.title()
        rezident.promo = form.promo.data
        rezident.email = form.email.data
        db.session.commit()
        flask.current_app.actions_logger.info(
            f"Modified account {rezident} ({rezident.prenom} {rezident.nom} "
            f"{rezident.promo}, {rezident.email})"
        )
        flask.flash(_("Compte modifié avec succès !"), "success")
        return utils.redirect_to_next()

    return flask.render_template("profile/modify_account.html",
                                 title=_("Mettre à jour mon compte"),
                                 form=form)


@bp.route("/update_password", methods=["GET", "POST"])
@context.all_good_only
def update_password():
    """IntraRez password update page."""
    form = forms.PasswordUpdateForm()
    if form.validate_on_submit():
        if flask.g.rezident.check_password(form.current_password.data):
            flask.g.rezident.set_password(form.password.data)
            db.session.commit()
            flask.current_app.actions_logger.info(
                f"Updated password of {flask.g.rezident}"
            )
            flask.flash(_("Mot de passe mis à jour !"), "success")
            return utils.redirect_to_next()
        else:
            flask.flash(_("Mot de passe actuel incorrect"), "danger")

    return flask.render_template("profile/update_password.html",
                                 title=_("Modifier mon mot de passe"),
                                 form=form)

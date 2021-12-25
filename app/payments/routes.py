"""Intranet de la Rez - Payments-related Pages Routes"""

import datetime

import flask
from flask_babel import _
import flask_login

from app import context, db
from app.payments import bp, email
from app.enums import SubState
from app.models import Offer, Payment, Subscription
from app.tools import utils


@bp.before_app_first_request
def create_first_offer():
    """Create subscription welcome order if not already present."""
    if not Offer.query.first():
        offer = Offer.create_first_offer()
        db.session.add(offer)
        db.session.commit()


@bp.route("/")
@context.all_good_only
def main():
    """Subscriptions informations page."""
    subscriptions = sorted(flask.g.rezident.subscriptions,
                           key=lambda sub: sub.start, reverse=True)
    return flask.render_template("payments/main.html",
                                 title=_("Mon abonnement Internet"),
                                 subscriptions=subscriptions)


@bp.route("/pay")
@context.all_good_only
def pay():
    """Payment page."""
    if flask.g.rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    offers = Offer.query.filter_by(visible=True).order_by(Offer.price).all()
    return flask.render_template("payments/pay.html",
                                 title=_("Paiement"), offers=offers)


@bp.route("/pay/<method>")
@bp.route("/pay/<method>/<offer>")
@context.all_good_only
def pay_(method=None, offer=None):
    """Payment page."""
    if flask.g.rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    methods = {
        "lydia": _("Payer avec Lydia"),
        "transfer": _("Payer par virement"),
        "cash": _("Payer en main propre"),
        "magic": _("Ajouter un paiement"),
    }
    if method in methods:
        offer = Offer.query.get(offer)
        if offer and offer.visible and offer.active:
            if method == "magic" and not flask.g.doas:
                flask.abort(403)
            return flask.render_template(f"payments/pay_{method}.html",
                                         title=methods[method], offer=offer)

    # Bad arguments
    return utils.safe_redirect("payments.pay", next=None)


@bp.route("/add_payment/<offer>")
@context.all_good_only
def add_payment(offer=None):
    """Add an arbitrary payment by a GRI."""
    if flask.g.rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    if not flask.g.doas:
        flask.abort(403)

    offer = Offer.query.get(offer)
    if not (offer and offer.visible and offer.active):
        flask.flash("Offre incorrecte", "danger")
        return utils.redirect_to_next()

    rezident = flask.g.rezident
    payment = Payment(rezident=rezident, amount=offer.price,
                      timestamp=datetime.datetime.now(), lydia=False,
                      gri=flask_login.current_user)
    db.session.add(payment)
    subscription = Subscription(rezident=rezident, offer=offer,
                                payment=payment, start=datetime.date.today(),
                                end=datetime.date.today() + offer.delay)
    db.session.add(subscription)

    rezident.sub_state = rezident.computed_sub_state    # Should be "subscibed"
    db.session.commit()

    flask.flash("Paiement et abonnement enregistrés !", "success")
    email.send_state_change_email(rezident, rezident.sub_state)

    return utils.redirect_to_next()


@bp.route("/test_mail")
@context.gris_only
def test_mail():
    """Mails test route"""
    body = email.send_state_change_email(flask.g.rezident, SubState.outlaw)
    flask.flash("Mail sent", "success")
    return body

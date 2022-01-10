"""Intranet de la Rez - Payments-related Pages Routes"""

import datetime

import flask
from flask_babel import _

from app import context, db
from app.payments import bp, email
from app.enums import SubState
from app.models import Offer, Payment, Subscription
from app.tools import utils, typing


@bp.before_app_first_request
def create_first_offer() -> None:
    """Create subscription welcome order if not already present."""
    if not Offer.query.first():
        offer = Offer.create_first_offer()
        db.session.add(offer)
        db.session.commit()
        utils.log_action(f"Created first offer ({offer})")


@bp.route("/")
@context.all_good_only
def main() -> typing.RouteReturn:
    """Subscriptions informations page."""
    subscriptions = sorted(flask.g.rezident.subscriptions,
                           key=lambda sub: sub.start, reverse=True)
    return flask.render_template("payments/main.html",
                                 title=_("Mon abonnement Internet"),
                                 subscriptions=subscriptions)


@bp.route("/pay")
@context.all_good_only
def pay() -> typing.RouteReturn:
    """Payment page."""
    if flask.g.rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    offers = Offer.query.filter_by(visible=True).order_by(Offer.price).all()
    return flask.render_template("payments/pay.html",
                                 title=_("Paiement"), offers=offers)


@bp.route("/pay/<method>")
@bp.route("/pay/<method>/")
@bp.route("/pay/<method>/<offer>")
@context.all_good_only
def pay_(method: str, offer: str | None = None) -> typing.RouteReturn:
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
    return utils.ensure_safe_redirect("payments.pay", next=None)


@bp.route("/add_payment/<offer>")
@context.all_good_only
def add_payment(offer: str = None) -> typing.RouteReturn:
    """Add an arbitrary payment by a GRI."""
    if not flask.g.doas:
        flask.abort(403)

    rezident = flask.g.rezident
    if rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    offer = Offer.query.get(offer)
    if not (offer and offer.visible and offer.active):
        flask.flash("Offre incorrecte", "danger")
        return utils.redirect_to_next()

    offer = typing.cast(Offer, offer)   # type check only

    # Determine new subscription dates
    start = rezident.current_subscription.renew_day
    end = start + offer.delay

    # Add subscription
    payment = Payment(
        rezident=rezident,
        amount=offer.price,
        timestamp=datetime.datetime.now(),
        lydia=False,
        gri=flask.g.logged_in_user,
    )
    db.session.add(payment)
    subscription = Subscription(
        rezident=rezident,
        offer=offer,
        payment=payment,
        start=start,
        end=end,
    )
    db.session.add(subscription)

    rezident.sub_state = rezident.compute_sub_state()
    db.session.commit()
    utils.log_action(
        f"Added {subscription} to {offer}, with {payment} added by GRI, "
        f"granting Internet access for {start} – {end}"
    )
    if rezident.sub_state != SubState.subscribed:
        raise RuntimeError(
            f"payments.add_payment : Paiement {payment} ajouté, création "
            f"de l'abonnement {subscription}, mais le rezident {rezident} "
            f"a toujours l'état {rezident.sub_state}..."
        )

    flask.flash("Paiement et abonnement enregistrés !", "success")

    email.send_state_change_email(rezident, rezident.sub_state)
    flask.flash("Mail d'information envoyé !", "success")

    return utils.redirect_to_next()

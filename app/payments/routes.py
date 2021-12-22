"""Intranet de la Rez - Payments-related Pages Routes"""

import flask
from flask_babel import _

from app import context, db
from app.payments import bp
from app.enums import SubState
from app.models import Offer
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

    methods = {
        "lydia": "payments.lydia",
        "transfer": "payments.transfer",
        "cash": "payments.cash",
    }
    method = flask.request.args.get("method")
    if method in methods:
        offer = Offer.query.get(flask.request.args.get("offer"))
        if offer and offer.visible and offer.active:
            return utils.safe_redirect(methods[method], offer=offer.slug,
                                       next=None)

    offers = Offer.query.filter_by(visible=True).order_by(Offer.price).all()
    return flask.render_template("payments/pay.html",
                                 title=_("Payer"),
                                 offers=offers)


@bp.route("/lydia")
@context.all_good_only
def lydia():
    """Payment page."""
    offer = Offer.query.get(flask.request.args.get("offer"))
    if not (offer and offer.visible and offer.active):
        return utils.safe_redirect("payments.pay")
    if flask.g.rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    return f"PAY BY LYDIA {offer.name}"


@bp.route("/transfer")
@context.all_good_only
def transfer():
    """Payment page."""
    offer = Offer.query.get(flask.request.args.get("offer"))
    if not (offer and offer.visible and offer.active):
        return utils.safe_redirect("payments.pay")
    if flask.g.rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    return f"PAY BY VIREMENT {offer.name}"


@bp.route("/cash")
@context.all_good_only
def cash():
    """Payment page."""
    offer = Offer.query.get(flask.request.args.get("offer"))
    if not (offer and offer.visible and offer.active):
        return utils.safe_redirect("payments.pay")
    if flask.g.rezident.sub_state == SubState.subscribed:
        flask.flash(_("Vous avez déjà un abonnement en cours !"), "warning")
        return utils.redirect_to_next()

    return f"PAY BY CASH {offer.name}"

"""Intranet de la Rez - Payments-related Pages Routes"""

import flask
import flask_login
from flask_babel import _

from app import db
from app.payments import bp
from app.devices import check_device
from app.models import Offer


@bp.before_app_first_request
def create_first_offer():
    """Create subscription welcome order if not already present."""
    if not Offer.query.first():
        offer = Offer.create_first_offer()
        db.session.add(offer)
        db.session.commit()


@bp.route("/")
@check_device
def main():
    """Subscriptions informations page."""
    subscriptions = sorted(flask_login.current_user.subscriptions,
                           key=lambda sub: sub.start, reverse=True)
    return flask.render_template("payments/main.html",
                                 title=_("Mon abonnement Internet"),
                                 subscriptions=subscriptions)


@bp.route("/pay")
@check_device
def pay():
    """Payment page."""
    return flask.render_template("payments/pay.html",
                                 title=_("Please give us your money"))

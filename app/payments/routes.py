"""Intranet de la Rez - Payments-related Pages Routes"""

import functools

import flask
import flask_login
from flask_babel import _

from app import db
from app.payments import bp
from app.devices import check_device
from app.models import Offer


@bp.before_app_first_request
def create_first_offer():
    """Create Rezidence rooms if not already present."""
    if not Offer.query.first():
        offer = Offer.create_first_offer()
        db.session.add(offer)
        db.session.commit()


@bp.route("/pay")
@check_device
def pay():
    """PAY."""
    return flask.render_template("payments/pay.html",
                                 title=_("Please give us your money"))

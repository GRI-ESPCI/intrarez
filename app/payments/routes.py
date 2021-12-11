"""Intranet de la Rez - Payments-related Pages Routes"""

import functools

import flask
import flask_login
from flask_babel import _

from app.payments import bp
from app.devices import check_device
from app.tools.utils import redirect_to_next
from app.models import Rezident


@bp.route("/pay")
@check_device
def pay():
    """PAY."""
    return flask.render_template("payments/pay.html",
                                 title=_("Please give us your money"))

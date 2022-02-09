"""Intranet de la Rez - Lydia Integration"""

import datetime
import hashlib

import flask
from flask_babel import _
import requests

from app import db
from app.enums import PaymentStatus
from app.models import Rezident, Payment, Offer


def get_payment_url(rezident: Rezident, offer: Offer,
                    phone: str | None) -> str:
    """Get URL to send the rezident to to make him pay.

    If a payment request is already waiting, it returns its URL, else
    it creates a new request and returns its URL.

    Args:
        rezident: The rezident that want to pay.
        offer, phone: Passed to :func:`.create_payment`.

    Returns:
        The Lydia pay page URL.
    """
    try:
        payment = next(payment for payment in rezident.payments
                       if (payment.status == PaymentStatus.waiting
                           and payment.amount == offer.price))
    except StopIteration:
        # No payment waiting, create one
        return create_payment(rezident, offer, phone)
    else:
        # Payment waiting, check still open
        update_payment(payment)
        if payment.status == PaymentStatus.waiting:
            # Still open: return pay URL
            return build_payment_url(payment.lydia_uuid)
        elif payment.status == PaymentStatus.accepted:
            # Payment made (but callback not called?): validate it
            return flask.url_for("payments.lydia_validate",
                                 payment_id=payment.id)
        else:
            # Payment closed, cancelled...: create a new one
            return create_payment(rezident, offer, phone)


def create_payment(rezident: Rezident, offer: Offer, phone: str | None) -> str:
    """Creates a new Lydia payment request.

    Args:
        rezident: The rezident that want to pay.
        offer: The offer to pay for.
        phone: The phone number used to send the Lydia request. If
            omitted, or if not associated with a Lydia account, it
            will send the user to a CB pay page.

    Returns:
        The Lydia pay page URL.
    """
    payment = Payment(
        rezident=rezident,
        amount=offer.price,
        created=datetime.datetime.now(),
    )
    db.session.add(payment)
    db.session.commit()

    rep = requests.post(
        flask.current_app.config["LYDIA_BASE_URL"] + "/api/request/do.json",
        data={
            "vendor_token": flask.current_app.config["LYDIA_VENDOR_TOKEN"],
            "amount": format(float(offer.price), ".2f"),
            "currency": "EUR",
            "recipient": (phone or rezident.email
                          or f"{rezident.username}@no-email.org"),
            "type": "phone" if phone else "email",
            "payment_method": "lydia" if phone else "cb",
            "order_ref": payment.id,
            "message": _("Offre Internet à la Rez :") + f" {offer.name}",
            "notify": "no",
            "notify_collector": "no",
            "confirm_url": flask.url_for("payments.lydia_callback_confirm",
                                         _external=True),
            "cancel_url": flask.url_for("payments.lydia_callback_cancel",
                                        _external=True),
            "expire_url": flask.url_for("payments.lydia_callback_cancel",
                                        _external=True),
            "end_mobile_url": flask.url_for("payments.lydia_success",
                                            _external=True),
            "browser_success_url": flask.url_for("payments.lydia_success",
                                                 _external=True),
            "browser_fail_url": flask.url_for("payments.lydia_fail",
                                              _external=True),
        },
    )

    if rep and rep.json().get("error") == "0":
        # Payment request created
        payment.status = PaymentStatus.waiting
        payment.lydia_uuid = rep.json()["request_uuid"]
        db.session.commit()
        return build_payment_url(payment.lydia_uuid,
                                 method="lydia" if phone else "cb")
    else:
        raise RuntimeError(
            f"Lydia Request Do Failed: {rep.request.body} >>> {rep.text}"
        )


def update_payment(payment: Payment) -> None:
    """Check the state of a Lydia payment request.

    Updates the associated IntraRez payment if the status changed.

    Args:
        payment: The payment to update status of. ``lydia_uuid`` must be set.
    """
    rep = requests.post(
        flask.current_app.config["LYDIA_BASE_URL"] + "/api/request/state.json",
        data={"request_uuid": payment.lydia_uuid},
    )
    if rep:
        state = rep.json()["state"]
        payment.status = {
            "0": PaymentStatus.waiting,
            "1": PaymentStatus.accepted,
            "5": PaymentStatus.refused,
            "6": PaymentStatus.cancelled,
        }.get(state, PaymentStatus.error)
        db.session.commit()
    else:
        raise RuntimeError(
            f"Lydia Request Check Failed: {rep.request.body} >>> {rep.text}"
        )


def build_payment_url(request_uuid: str, method: str = "auto") -> str:
    """Build Lydia payment URL from request UUID.

    Args:
        request_uuid: The UUID of the payment request.
        method: The method to use. One of ``lydia``, ``cb`` or
            ``auto`` (default). See
            https://homologation.lydia-app.com/doc/api/#api-Request-Do.

    Returns:
        The Lydia pay page URL.
    """
    base_url = flask.current_app.config["LYDIA_BASE_URL"]
    return f"{base_url}/collect/payment/{request_uuid}/{method}"


def check_signature(sig: str, **params: str) -> bool:
    """Check whether the signature passed by a Lydia call is correct.

    See https://homologation.lydia-app.com/doc/api/#signature.

    Args:
        sig: The signature to compare to (md5 hexdigest).
        **params: The parameters in the signature (in any order).

    Returns:
        Whether the signature validates with the params and private token.
    """
    sorted_params = sorted(params.items(), key=lambda kv: kv[0])
    query = "&".join(f"{key}={val}" for key, val in sorted_params)
    raw_sig = query + "&" + flask.current_app.config["LYDIA_PRIVATE_TOKEN"]
    return (hashlib.md5(raw_sig.encode()).hexdigest() == sig)

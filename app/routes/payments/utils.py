"""Intranet de la Rez - Payments-related Pages Utils"""

import datetime

from app import db
from app.enums import SubState
from app.models import Offer, Payment, Rezident, Subscription
from app.routes.payments import email
from app.utils import helpers


def add_subscription(
    rezident: Rezident, offer: Offer, payment: Payment
) -> Subscription:
    """Add a new subscription to a Rezident.

    Update sub state and send informative email.
    Remove user's current ban if necessary.

    Args:
        rezident: The Rezident to add a subscription to.
        offer: The offer just subscripted to.
        payment: The payment made by the Rezident to subscribe to the Offer.

    Returns:
        The subscription created.
    """
    # Determine new subscription dates
    start = rezident.current_subscription.renew_day
    end = start + offer.delay

    # Add new subscription
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

    if rezident.sub_state != SubState.subscribed:
        raise RuntimeError(
            f"payments.add_payment : Paiement {payment} ajouté, création "
            f"de l'abonnement {subscription}, mais le rezident {rezident} "
            f"a toujours l'état {rezident.sub_state}..."
        )

    # Remove ban and update DHCP
    if rezident.is_banned:
        rezident.current_ban.end = datetime.datetime.utcnow()
        helpers.log_action(f"{rezident} subscribed, terminated {rezident.current_ban}")
        db.session.commit()
        helpers.run_script("gen_dhcp.py")  # Update DHCP rules

    # Send mail
    email.send_state_change_email(rezident, rezident.sub_state)
    return subscription

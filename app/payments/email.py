"""Intranet de la Rez - Payments-related emails"""

import flask
import flask_babel
from flask_babel import _

from app.email import send_email
from app.models import Rezident, SubState


def send_state_change_email(rezident: Rezident, sub_state: SubState) -> None:
    """Send an email informing a Rezident of a subscription state change.

    Args:
        rezident: The Rezident in question.
        sub_state: The new Rezident subscription state.
    """
    with flask_babel.force_locale(rezident.locale or "en"):
        # Render mail content in rezident's language
        if sub_state == SubState.subscribed:
            subject = _("Paiement validé !")
            template_name = "new_subscription"
        elif sub_state == SubState.trial:
            subject = _("Paiement nécessaire")
            template_name = "subscription_expired"
        else:
            subject = _("Votre accès Internet a été coupé")
            template_name = "internet_cut"

        html_body = flask.render_template(
            f"payments/mails/{template_name}.html",
            rezident=rezident,
            sub=rezident.current_subscription
        )

    send_email(
        f"payments/{template_name}",
        subject=f"[IntraRez] {subject}",
        recipients={rezident.email: rezident.full_name},
        html_body=html_body,
    )


def send_reminder_email(rezident: Rezident) -> None:
    """Send an email informing a Rezident its access will be cut soon.

    Args:
        rezident: The Rezident in question.
    """
    with flask_babel.force_locale(rezident.locale or "en"):
        # Render mail content in rezident's language
        subject = _("IMPORTANT - Votre accès Internet va bientôt couper !")
        html_body = flask.render_template(
            "payments/mails/renew_reminder.html",
            rezident=rezident,
            sub=rezident.current_subscription,
        )

    send_email(
        "payments/renew_reminder",
        subject=f"[IntraRez] {subject}",
        recipients={rezident.email: rezident.full_name},
        html_body=html_body,
    )

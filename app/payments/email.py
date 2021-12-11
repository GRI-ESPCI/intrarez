"""Intranet de la Rez - Payments-related emails"""

import flask
from flask_babel import _

from app.email import send_email
from app.models import SubState


def send_state_change_email(rezident, sub_state):
    """Send an email informing a Rezident of a subscription state change.

    Args:
        rezident (~models.Rezident): the Rezident in question.
        sub_state (~enums.SubState): the new Rezident subscription state.
    """
    sender_mail = flask.current_app.config["ADMINS"][0]
    match sub_state:
        case SubState.subscribed:
            subject = _("Paiement validé !")
            template_name = "payment_state_subscribed"
        case SubState.trial:
            subject = _("Attention, paiement Internet nécessaire")
            template_name = "payment_state_trial"
        case SubState.outlaw:
            subject = _("Votre accès Internet a été coupé")
            template_name = "payment_state_outlaw"

    send_email(
        subject=f"[IntraRez] {subject}",
        sender=f"IntraRez <{sender_mail}>",
        recipients=[f"{rezident.full_name} <{rezident.email}>"],
        text_body=flask.render_template(f"payments/mails/{template_name}.txt",
                                        rezident=rezident),
        html_body=flask.render_template(f"payments/mails/{template_name}.html",
                                        rezident=rezident)
    )

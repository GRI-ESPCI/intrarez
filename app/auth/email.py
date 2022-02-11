"""Intranet de la Rez - Authentication-related Emails"""

import flask
import flask_babel
from flask_babel import _

from app.email import send_email
from app.models import Rezident


def send_account_registered_email(rezident: Rezident) -> None:
    """Send an email confirming account registration.

    Args:
        rezident: The rezident that just registered.
    """
    subject = _("Compte créé avec succès !")
    html_body = flask.render_template(
        "auth/mails/account_registered.html",
        rezident=rezident,
    )
    send_email(
        "auth/account_registered",
        subject=f"[IntraRez] {subject}",
        recipients={rezident.email: rezident.full_name},
        html_body=html_body,
    )


def send_password_reset_email(rezident: Rezident) -> None:
    """Send a password reset email.

    Args:
        rezident: The rezident to reset password of.
    """
    with flask_babel.force_locale(rezident.locale or "en"):
        # Render mail content in rezident's language (if doas, ...)
        subject = _("Réinitialisation du mot de passe")
        html_body = flask.render_template(
            "auth/mails/reset_password.html",
            rezident=rezident,
            token=rezident.get_reset_password_token(),
        )

    send_email(
        "auth/reset_password",
        subject=f"[IntraRez] {subject}",
        recipients={rezident.email: rezident.full_name},
        html_body=html_body,
    )

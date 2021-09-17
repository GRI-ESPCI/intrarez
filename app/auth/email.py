"""Intranet de la Rez - Authentication Emails"""

import flask
from flask_babel import lazy_gettext as _l

from app import email


def send_password_reset_email(user):
    """Send a password reset email.

    Args:
        user (models.User): the user to reset password of.
    """
    subject = _l("[IntraRez] Réinitialisation du mot de passe")
    sender = "noreply@intrarez"
    recipients = [user.email]
    token = user.get_reset_password_token()
    text_body = flask.render_template("mails/reset_password.txt",
                                      user=user, token=token)
    html_body = flask.render_template("mails/reset_password.html",
                                      user=user, token=token)
    email.send_email(subject, sender, recipients, text_body, html_body)

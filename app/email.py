"""Intranet de la Rez Flask App - Emails System"""

import threading

import flask
import flask_mail

from app import mail


def _send_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    """Send an email using Flask-Mail, asynchroniously.

    Args:
        subject (str): The mail subject.
        sender (str): The sender address.
        recipients (list[str]): The recipients addresses.
        text_body (str): The mail content to print in raw text mode.
        html_body (str): The mail content to print in HTML mode.
    """
    msg = flask_mail.Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    threading.Thread(
        target=_send_email,
        args=(flask.current_app._get_current_object(), msg)
    ).start()

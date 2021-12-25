"""Intranet de la Rez Flask App - Emails System"""

import threading

import flask
import flask_mail
import premailer

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
    msg.html = process_html(html_body)
    threading.Thread(
        target=_send_email,
        args=(flask.current_app._get_current_object(), msg)
    ).start()

    # TEMPORARY
    return msg.html


def process_html(body):
    """Transform a screen-optimized HTML body to a mail-optimized one.

    Relies on :func:`premailer.transform` to include styles in HTML body
    and optimize content.

    Args:
        body (str): The HTML string to process.

    Returns:
        :class:`str`: The processed HTML mail body.
    """
    return premailer.transform(
        body,
        base_url="https://intrarez.pc-est-magique.fr/",
        allow_loading_external_files=True,
        remove_classes=True,
        external_styles=[
            flask.url_for("static",
                          filename="css/compiled/custom-bootstrap.css"),
            flask.url_for("static", filename="css/custom.css")
        ],
        disable_validation=True,
        disable_leftover_css=True
    )

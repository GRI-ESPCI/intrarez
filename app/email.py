"""Intranet de la Rez Flask App - Emails System"""

import logging
import threading

import html2text
import flask
import flask_mail
import premailer

from app import IntraRezApp, mail, typing


# Set up specific logging for mails
mail_logger = logging.Logger("email")
_mail_handler = logging.FileHandler("logs/mails.log")
_mail_formatter = logging.Formatter("{asctime} -- {message}", "%x %X", "{")
_mail_handler.setFormatter(_mail_formatter)
mail_logger.addHandler(_mail_handler)

# Class files used when transforming HTML body (styles inlining)
class_files = [
    "app/static/css/compiled/custom-bootstrap.css",
    "app/static/css/custom.css",
]

# Mail-formatting objects, built by init_premailer() / init_textifier()
# registered by app.before_first_request
_premailer = typing.cast(premailer.Premailer, None)
_textifier = typing.cast(html2text.HTML2Text, None)


def _send_email(app: IntraRezApp, template: str, msg: flask_mail.Message) -> None:
    # To be called in a separate tread
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:
            mail_logger.error(f"ERROR: {type(exc).__name__}: {exc}")
            app.logger.error(
                f"ATTENTION : Échec lors de l'envoi du mail '{template}' "
                f"à {msg.recipients} :\n{type(exc).__name__}: {exc}"
            )


def send_email(
    template: str,
    *,
    subject: str,
    recipients: dict[str | None, str],
    html_body: str,
    text_body: str | None = None,
) -> None:
    """Send an email using Flask-Mail, asynchronously.

    Args:
        template: The mail template name.
        subject: The mail subject.
        sender: The sender address.
        recipients: The recipients addresses -> names dict.
        html_body: The mail content to print in HTML mode.
        text_body: The mail content to print in plain text mode.
            If not set, it will be constructed from ``html_body`` using
            :func:`.html_to_plaintext`.
    """
    # Prepare body
    html_body = process_html(html_body)
    if text_body is None:
        text_body = html_to_plaintext(html_body)

    # Construct mail
    recipients_f = {addr: name for addr, name in recipients.items() if addr}
    sender_mail = flask.current_app.config["ADMINS"][0]
    msg = flask_mail.Message(
        subject=subject,
        sender=f"IntraRez <{sender_mail}>",
        recipients=[f"{name} <{addr}>" for addr, name in recipients_f.items()],
        body=text_body,
        html=html_body,
        extra_headers={
            "List-Unsubscribe": f"<mailto: {sender_mail}?subject=Unsubscribe: "
            f"{', '.join(recipients_f.keys())}>"
        },
    )

    # Send mail
    mail_logger.info(f"Sending '{template}' to {msg.recipients}")
    app = typing.cast(IntraRezApp, flask.current_app._get_current_object())
    threading.Thread(target=_send_email, args=(app, template, msg)).start()


def init_premailer() -> None:
    """Construct the :class:`premailer.Premailer` object used to prepare
    mails HTML body."""
    global _premailer

    class_files_contents = []
    for file in class_files:
        with open(file, "r") as fp:
            class_files_contents.append(fp.read())

    scheme = flask.current_app.config["PREFERRED_URL_SCHEME"]
    server = flask.current_app.config["SERVER_NAME"]
    root = flask.current_app.config["APPLICATION_ROOT"]

    _premailer = premailer.Premailer(
        base_url=f"{scheme}://{server}{root}",
        remove_classes=True,
        css_text="\n".join(class_files_contents),
        disable_validation=True,
        disable_leftover_css=True,
        cssutils_logging_level=logging.CRITICAL,
    )


def init_textifier() -> None:
    """Construct the :class:`html2text.HTML2Text` object used to prepare
    mails plain text body."""
    global _textifier
    _textifier = html2text.HTML2Text()
    _textifier.body_width = 79
    _textifier.protect_links = True
    _textifier.images_to_alt = True
    _textifier.wrap_list_items = True
    _textifier.default_image_alt = "(image)"
    _textifier.emphasis_mark = "*"


def process_html(body):
    """Transform a screen-optimized HTML body to a mail-optimized one.

    Relies on :class:`premailer.Premailer` to include styles in HTML body
    and optimize content.

    Args:
        body (str): The HTML string to process.

    Returns:
        :class:`str`: The processed HTML mail body.
    """
    return _premailer.transform(body)


def html_to_plaintext(body):
    """Transform a mail-optimized HTML body to readable plain text.

    Relies on :func:`html2text.HTML2Text` to include styles in HTML body
    and optimize content.

    Args:
        body (str): The HTML string to process.

    Returns:
        :class:`str`: The processed plain text mail body.
    """
    return _textifier.handle(body)

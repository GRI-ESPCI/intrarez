"""Intranet de la Rez - Custom Flask Loggers"""

import os
import logging
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
import threading

import flask
from discord_webhook import DiscordWebhook
import requests

from app import IntraRezApp
from app.tools import typing


def _execute_webhook(app: IntraRezApp,
                     webhook: DiscordWebhook) -> None:
    # To be called in a separate tread
    with app.app_context():
        response = webhook.execute()        # type: ignore
        if not response:
            app.logger.error(
                f"ATTENTION : Échec lors de l'envoi du webhook {webhook.url} "
                f"({webhook.content}): {response.code} {response.text}"
            )


class DiscordHandler(StreamHandler):
    """Logging handler using a webhook to send log to a Discord server

    Args:
        webhook: Webhook URL to use
            (``"https://discord.com/api/webhooks/<server>/<id>"``)
    """
    def __init__(self, webhook: str) -> None:
        """Initializes self."""
        super().__init__()
        self.webhook = webhook

    def emit(self, record: logging.LogRecord) -> requests.Response:
        """Method called to make this handler send a record."""
        content = self.format(record)
        webhook = DiscordWebhook(url=self.webhook, content=content, rate_limit_retry=True)
        # Send in a separate thread
        app = typing.cast(IntraRezApp, flask.current_app._get_current_object())
        threading.Thread(target=_execute_webhook, args=(app, webhook)).start()


class InfoErrorFormatter(logging.Formatter):
    """Utility formatter allowing to use different formats for info and errors.

    Args:
        info_fmt: Formatter format to use for levels DEBUG and INFO.
        error_fmt: Formatter format to use for levels above INFO.
        *args, **kwargs: Passed to :class:`logging.Formatter`
    """
    def __init__(self, info_fmt: str, error_fmt: str, *args, **kwargs) -> None:
        """Initializes self."""
        super().__init__(info_fmt, *args, **kwargs)
        self.info_fmt = info_fmt
        self.error_fmt = error_fmt

    def format(self, record: logging.LogRecord) -> str:
        """Method called to make this formatter format a record."""
        format_orig = self._fmt
        if record.levelno > logging.INFO:
            self._fmt = self.error_fmt
        else:
            self._fmt = self.info_fmt
        result = super().format(record)
        self._fmt = format_orig
        return record.name.ljust(12) + result


class DiscordFormatter(logging.Formatter):
    """Base formatter preparing a record to be send to a Discord server.

    Args:
        role_id (str): Optional 18-digit ID used to mention a specific role
            in subclasses using :attr:`DiscordFormatter.role_mention`.
    """
    def __init__(self, role_id: str | None = None) -> None:
        """Initializes self."""
        super().__init__()
        self.role_mention = f"<@&{role_id}> " if role_id else ""

    def format(self, record: logging.LogRecord) -> str:
        """Method called to make this formatter format a record.

        Truncates message to 1900 characters (Discord limits to 2000).
        """
        msg = record.getMessage()
        if len(msg) > 1900:     # Discord limitation
            msg = "[...]\n" + msg[-1900:]
        return msg


class DiscordErrorFormatter(DiscordFormatter):
    """:class:`.DiscordFormatter` subclass used to transmit error messages."""
    def format(self, record: logging.LogRecord) -> str:
        """Method called to make this formatter format a record.

        Retrieves request IP and logged-in rezident name if applicable.
        """
        msg = super().format(record)
        try:
            remote_ip = flask.g.remote_ip or "<missing header>"
        except AttributeError:
            remote_ip = "<unknown IP>"
        else:
            try:
                if flask.g.logged_in:
                    remote_ip += f" / {flask.g.rezident.full_name[:25]}"
            except AttributeError:
                pass

        return (f"{self.role_mention}ALED ça a planté ! (chez {remote_ip})\n"
                f"```{msg}```")


# Custom formatter
class DiscordLoggingFormatter(DiscordFormatter):
    """:class:`.DiscordFormatter` subclass used to transmit actions infos."""
    def format(self, record: logging.LogRecord) -> str:
        """Method called to make this formatter format a record.

        Retrieves logged-in rezident and doaser names if applicable.
        """
        msg = super().format(record)
        try:
            if flask.g.logged_in:
                user = flask.g.logged_in_user.username
                if flask.g.doas:
                    user += f" AS {flask.g.rezident.username}"
            else:
                user = "(anonymous)"
        except AttributeError:
            user = "(before context)"
        if record.levelno > logging.INFO:
            return f"`{user}: {record.levelname}: {msg}` ({self.role_mention})"
        else:
            return f"`{user}: {msg}`"


def configure_logging(app: IntraRezApp) -> None:
    """Configure logging for the IntraRez web app.

    Setup :attr:`app.logger <flask.Flask.logger>` to log errors to
    ``app.config["ERROR_WEBHOOK"]`` Discord webhook and everything to a
    journalized file, and adds a child logger  ``app.actions_logger``
    ("app.actions") logging actions to ``app.config["LOGGING_WEBHOOK"]``.
    """
    if app.config["ERROR_WEBHOOK"] and not (app.debug or app.testing):
        # Alert messages for errors
        discord_errors_handler = DiscordHandler(app.config["ERROR_WEBHOOK"])
        discord_errors_handler.setLevel(logging.ERROR)
        discord_errors_handler.setFormatter(DiscordErrorFormatter(
            app.config.get("GRI_ROLE_ID")
        ))
        app.logger.addHandler(discord_errors_handler)

    if app.config["LOGGING_WEBHOOK"]:
        # Logging messages for actions
        discord_actions_handler = DiscordHandler(app.config["LOGGING_WEBHOOK"])
        discord_actions_handler.setLevel(logging.DEBUG if app.debug
                                         else logging.INFO)
        discord_actions_handler.setFormatter(DiscordLoggingFormatter(
            app.config.get("GRI_ROLE_ID")
        ))
        app.actions_logger.addHandler(discord_actions_handler)

    # File logging
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = TimedRotatingFileHandler("logs/intrarez.log", when="D")
    file_handler.setFormatter(InfoErrorFormatter(
        "{asctime} {levelname}: {message}",
        "{asctime} {levelname}: {message} [in {pathname}:{lineno}]",
        style="{",
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # Start logs
    app.logger.setLevel(logging.INFO)
    app.actions_logger.setLevel(logging.INFO)

"""Intranet de la Rez - Custom Flask Loggers"""

import os
import logging
from logging import StreamHandler
from logging.handlers import SMTPHandler, RotatingFileHandler

import flask
from discord_webhook import DiscordWebhook


class DiscordHandler(StreamHandler):
    def __init__(self, webhook, role_id=None):
        super().__init__()
        self.webhook = webhook
        self.gri_mention = f"<@&{role_id}> " if role_id else ""

    def emit(self, record):
        msg = self.format(record)
        if len(msg) > 1900:     # Discord limitation
            msg = "[...]\n" + msg[-1900:]

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

        content = (f"{self.gri_mention}ALED ça a planté ! (chez {remote_ip})\n"
                   f"```{msg}```")
        webhook = DiscordWebhook(url=self.webhook, content=content)
        webhook.execute()


# Custom formatter
class InfoErrorFormatter(logging.Formatter):
    def __init__(self, info_fmt, error_fmt, *args, **kwargs):
        super().__init__(info_fmt, *args, **kwargs)
        self.info_fmt = info_fmt
        self.error_fmt = error_fmt

    def format(self, record):
        format_orig = self._fmt
        if record.levelno > logging.INFO:
            self._fmt = self.error_fmt
        else:
            self._fmt = self.info_fmt
        result = super().format(record)
        self._fmt = format_orig
        return result


def set_handlers(app):
    if app.config["MAIL_SERVER"] and not (app.debug or app.testing):
        # Alert mails
        server = app.config["MAIL_SERVER"]
        auth = None
        if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
            auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
        secure = () if app.config["MAIL_USE_TLS"] else None
        mail_handler = SMTPHandler(
            mailhost=(server, app.config["MAIL_PORT"]),
            fromaddr=f"no-reply@{server}",
            toaddrs=app.config["ADMINS"],
            subject="IntraRez Internal Error",
            credentials=auth,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    if app.config["ERROR_WEBHOOK"] and not (app.debug or app.testing):
        # Alert webhooks
        discord_handler = DiscordHandler(app.config["ERROR_WEBHOOK"],
                                         app.config.get("GRI_ROLE_ID"))
        discord_handler.setLevel(logging.ERROR)
        app.logger.addHandler(discord_handler)

    # File logs
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler("logs/intrarez.log", maxBytes=10240,
                                       backupCount=100)
    file_handler.setFormatter(InfoErrorFormatter(
        "{asctime} {levelname}: {message}",
        "{asctime} {levelname}: {message} [in {pathname}:{lineno}]",
        style="{",
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # Start logs
    app.logger.setLevel(logging.INFO)

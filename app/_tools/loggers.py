"""Intranet de la Rez - Custom Flask Loggers"""

import os
import logging
from logging import StreamHandler
from logging.handlers import SMTPHandler, RotatingFileHandler

from discord_webhook import DiscordWebhook


class DiscordHandler(StreamHandler):
    def __init__(self, webhook):
        super().__init__()
        self.webhook = webhook

    def emit(self, record):
        msg = self.format(record)
        webhook = DiscordWebhook(url=self.webhook, content=msg)
        webhook.execute()


def set_handlers(logger, config):
    if config["MAIL_SERVER"]:
        # Alert mails
        server = config["MAIL_SERVER"]
        auth = None
        if config["MAIL_USERNAME"] or config["MAIL_PASSWORD"]:
            auth = (config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
        secure = () if config["MAIL_USE_TLS"] else None
        mail_handler = SMTPHandler(
            mailhost=(server, config["MAIL_PORT"]),
            fromaddr=f"no-reply@{server}",
            toaddrs=config["ADMINS"],
            subject="IntraRez Internal Error",
            credentials=auth,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        logger.addHandler(mail_handler)

    if config["ERROR_WEBHOOK"]:
        # Alert webhooks
        discord_handler = DiscordHandler(config["ERROR_WEBHOOK"])
        discord_handler.setLevel(logging.ERROR)
        logger.addHandler(discord_handler)

    # File logs
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler("logs/intrarez.log", maxBytes=10240,
                                       backupCount=100)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    ))
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Start logs
    logger.setLevel(logging.INFO)

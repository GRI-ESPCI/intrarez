"""Intranet de la Rez Flask App - Configuration"""

import os

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


def get_or_die(name):
    """Check availability and get the value of an environment variable.

    Args:
        name (str): The envrionment variable to get.

    Returns:
        The environment variable value, if it is set.

    Raises:
        RuntimeError: if the environment variable is not set.
    """
    var = os.environ.get(name)
    if var is None:
        raise RuntimeError(f"Missing environment variable '{name}'")
    return var


class Config():
    """IntraRez Flask Web App Configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY")

    LANGUAGES = ["fr", "en"]

    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME")
    SERVER_NAME = os.environ.get("SERVER_NAME")
    APPLICATION_ROOT = os.environ.get("APPLICATION_ROOT")

    SQLALCHEMY_DATABASE_URI = get_or_die("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMINS = os.environ.get("ADMINS", "").split(";")

    ERROR_WEBHOOK = os.environ.get("ERROR_WEBHOOK")
    MESSAGE_WEBHOOK = os.environ.get("MESSAGE_WEBHOOK")
    MAIL_WEBHOOK = os.environ.get("MAIL_WEBHOOK")
    GRI_ROLE_ID = os.environ.get("GRI_ROLE_ID")

    GOOGLE_RECAPTCHA_SITEKEY = os.environ.get("GOOGLE_RECAPTCHA_SITEKEY")
    GOOGLE_RECAPTCHA_SECRET = os.environ.get("GOOGLE_RECAPTCHA_SECRET")

    BRANCH = os.environ.get("BRANCH")
    FORCE_IP = os.environ.get("FORCE_IP")
    FORCE_MAC = os.environ.get("FORCE_MAC")

    NETLOCS = os.environ.get("NETLOCS")
    if NETLOCS is not None:
        NETLOCS = NETLOCS.split(";")

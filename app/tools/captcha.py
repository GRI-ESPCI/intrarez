"""Intranet de la Rez - Captcha Utilities"""

import flask
import requests


def verify_captcha() -> bool:
    """Query Google reCAPTCHA v2 API to verify just posted captcha.

    Should only be called from a route after form validation
    if the form contains a reCAPTCHA widget.

    Implements https://developers.google.com/recaptcha/docs/verify.

    Returns:
        Whether the verification succeeded.
    """
    response = flask.request.form.get("g-recaptcha-response")
    if not response:
        return False

    verify_endpoint = "https://www.google.com/recaptcha/api/siteverify"
    secret = flask.current_app.config["GOOGLE_RECAPTCHA_SECRET"]

    res = requests.post(verify_endpoint,
                        data=dict(secret=secret, response=response))
    if not res:
        return False

    return res.json()["success"]

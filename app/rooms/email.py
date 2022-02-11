"""Intranet de la Rez - Rooms-related Emails"""

import flask
import flask_babel
from flask_babel import _

from app.email import send_email
from app.models import Rezident


def send_room_transferred_email(rezident: Rezident) -> None:
    """Send an email informing a rezident someone else took its room.

    Args:
        rezident (models.Rezident): the rezident that lost its room.
    """
    with flask_babel.force_locale(rezident.locale or "en"):
        # Render mail content in rezident's language
        subject = _("Attention : Chambre transférée, Internet coupé")
        html_body = flask.render_template(
            "rooms/mails/room_transferred.html",
            rezident=rezident,
        )

    send_email(
        "rooms/room_transferred",
        subject=f"[IntraRez] {subject}",
        recipients={rezident.email: rezident.full_name},
        html_body=html_body,
    )

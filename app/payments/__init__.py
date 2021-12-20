"""Intranet de la Rez - Payments-related Pages Blueprint"""

import flask

bp = flask.Blueprint("payments", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.payments import routes

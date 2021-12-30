"""Intranet de la Rez - Authentication Blueprint"""

import flask

bp = flask.Blueprint("auth", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.auth import routes

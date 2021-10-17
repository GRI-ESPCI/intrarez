"""Intranet de la Rez - Gris-only Pages Blueprint"""

import flask

bp = flask.Blueprint("gris", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.gris import routes

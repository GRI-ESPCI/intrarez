"""Intranet de la Rez - Errors Blueprint"""

import flask

bp = flask.Blueprint("errors", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.routes.errors import handlers

"""Intranet de la Rez - Devices Pages Blueprint"""

import flask

bp = flask.Blueprint("devices", __name__)

# ! Keep at the bottom to avoid circular import issues !
from app.devices import routes

check_device = routes.check_device

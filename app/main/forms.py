"""Intranet de la Rez - Main Pages Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app._tools.validators import DataRequired


class EmptyForm(FlaskForm):
    """WTForm used to absolutely nothing."""
    submit = wtforms.SubmitField(_l("Connexion"))

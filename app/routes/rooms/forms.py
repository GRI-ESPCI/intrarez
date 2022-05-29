"""Intranet de la Rez - Rooms-related Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import DataRequired, Optional, ValidRoom, PastDate, FutureDate


class RentalRegistrationForm(FlaskForm):
    """WTForm used to register a room rental."""

    room = html5.IntegerField(_l("Chambre"), validators=[DataRequired(), ValidRoom()])
    start = html5.DateField(
        _l("Début de la location"), validators=[DataRequired(), PastDate()]
    )
    end = html5.DateField(
        _l("Fin de la location (optionnel)"), validators=[Optional(), FutureDate()]
    )
    submit = wtforms.SubmitField(_l("Enregistrer"))


class RentalModificationForm(FlaskForm):
    """WTForm used to modify a room rental."""

    start = html5.DateField(
        _l("Début de la location"), validators=[DataRequired(), PastDate()]
    )
    end = html5.DateField(
        _l("Fin de la location (optionnel)"), validators=[Optional(), FutureDate()]
    )
    submit = wtforms.SubmitField(_l("Modifier"))


class RentalTransferForm(FlaskForm):
    """WTForm used to terminate a room rental, before creating a new one."""

    end = html5.DateField(
        _l("Fin de la location"), validators=[DataRequired(), PastDate()]
    )
    submit = wtforms.SubmitField(_l("Terminer la location"))

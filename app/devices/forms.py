"""Intranet de la Rez - Devices-related Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.tools.validators import DataRequired, Optional, Length, MacAddress


class DeviceRegistrationForm(FlaskForm):
    """WTForm used to register devices."""
    nom = wtforms.StringField(_l("Nom (optionnel)"),
                              validators=[Optional(), Length(max=64)])
    mac = wtforms.StringField(_l("Adresse MAC*"),
                              validators=[DataRequired(), MacAddress()])
    type = wtforms.StringField(_l("Type (optionnel)"),
                               validators=[Optional(), Length(max=64)])
    submit = wtforms.SubmitField(_l("Enregistrer l'appareil"))


class DeviceTransferForm(FlaskForm):
    """WTForm used to transfer a device."""
    nom = wtforms.StringField(_l("Nom (optionnel)"),
                              validators=[Optional(), Length(max=64)])
    mac = wtforms.StringField(_l("Adresse MAC"),
                              validators=[DataRequired(), MacAddress()])
    type = wtforms.StringField(_l("Type (optionnel)"),
                               validators=[Optional(), Length(max=64)])
    submit = wtforms.SubmitField(_l("Transférer l'appareil"))

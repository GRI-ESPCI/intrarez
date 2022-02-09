"""Intranet de la Rez - Payment Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.tools.validators import Optional, PhoneNumber


class LydiaPaymentForm(FlaskForm):
    """WTForm used to get Lydia payment information."""
    phone = html5.TelField(_l("Numéro de téléphone associé à Lydia"),
                           validators=[Optional(), PhoneNumber()])
    submit_lydia = wtforms.SubmitField(_l("Envoyer une demande via Lydia"))
    submit_cb = wtforms.SubmitField(_l("Payer par carte bancaire"))

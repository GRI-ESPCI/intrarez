"""Intranet de la Rez - Custom Flask Forms Validators"""

import wtforms
from flask_babel import lazy_gettext as _l

from app.models import User


class CustomValidator():
    message = "Invalid field."
    def __init__(self, _message=None):
        if _message is None:
            _message = self.message
        self._message = _message
    def __call__(self, form, field):
        if not self.validate(form, field):
            raise wtforms.validators.ValidationError(self._message)


class DataRequired(wtforms.validators.DataRequired):
    def __init__(self, message=None):
        if message is None:
            message = _l("Ce champ est requis.")
        super().__init__(message)

class Email(wtforms.validators.Email):
    def __init__(self, message=None, **kwargs):
        if message is None:
            message = _l("Adresse email invalide.")
        super().__init__(message, **kwargs)

class EqualTo(wtforms.validators.EqualTo):
    def __init__(self, fieldname, message=None):
        if message is None:
            message = _l("Valeur différente du champ précédent.")
        super().__init__(fieldname, message)

class NewUsername(CustomValidator):
    message = _l("Nom d'utilisateur déjà utilisé.")
    def validate(self, form, field):
        return (User.query.filter_by(username=field.data).first() is None)

class NewEmail(CustomValidator):
    message = _l("Adresse e-mail déjà liée à un autre compte.")
    def validate(self, form, field):
        return (User.query.filter_by(email=field.data).first() is None)

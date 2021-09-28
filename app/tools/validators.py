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


Optional = wtforms.validators.Optional


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

class MacAddress(wtforms.validators.MacAddress):
    def __init__(self, message=None):
        if message is None:
            message = _l("Adresse MAC invalide (format attendu :"
                         " xx:xx:xx:xx:xx:xx).")
        super().__init__(message)

class Length(wtforms.validators.Length):
    def __init__(self, min=-1, max=-1, message=None):
        if min < 0 and max < 0:
            raise ValueError("Length validator cannot have both min and max "
                             "arguments not set or < 0.")
        if message is None:
            if min < 0:
                message = _l("Doit faire moins de %(max)d caractères.",
                             max=max)
            elif max < 0:
                message = _l("Doit faire au moins %(min)d caractères.",
                             min=min)
            else:
                message = _l("Doit faire entre %(min)d et %(max)d caractères.",
                             min=min, max=max)
        super().__init__(min, max, message)

class NewUsername(CustomValidator):
    message = _l("Nom d'utilisateur déjà utilisé.")

    def validate(self, form, field):
        return (User.query.filter_by(username=field.data).first() is None)


class NewEmail(CustomValidator):
    message = _l("Adresse e-mail déjà liée à un autre compte.")

    def validate(self, form, field):
        return (User.query.filter_by(email=field.data).first() is None)


class ValidRoom(CustomValidator):
    message = _l("Numéro de chambre invalide.")

    def validate(self, form, field):
        return (101 <= field.data <= 126
                or 201 <= field.data <= 226
                or 301 <= field.data <= 326
                or 401 <= field.data <= 426
                or 501 <= field.data <= 526
                or 601 <= field.data <= 626
                or 701 <= field.data <= 726)

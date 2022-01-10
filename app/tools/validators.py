"""Intranet de la Rez - Custom Flask Forms Validators"""

import datetime

import flask
import wtforms
from flask_babel import lazy_gettext as _l

from app.models import Rezident, Room
from app.tools.typing import JinjaStr


class CustomValidator():
    message = "Invalid field."

    def __init__(self, _message: JinjaStr | None = None) -> None:
        if _message is None:
            _message = self.message
        self._message = _message

    def __call__(self, form: wtforms.Form, field: wtforms.Field) -> None:
        if not self.validate(form, field):
            raise wtforms.validators.ValidationError(self._message)

    def validate(self, form: wtforms.Form, field: wtforms.Field) -> bool:
        raise NotImplementedError       # Implement in subclasses


Optional = wtforms.validators.Optional


class DataRequired(wtforms.validators.DataRequired):
    def __init__(self, message: JinjaStr | None = None) -> None:
        if message is None:
            message = _l("Ce champ est requis.")
        super().__init__(message)


class Email(wtforms.validators.Email):
    def __init__(self, message: JinjaStr | None = None, **kwargs) -> None:
        if message is None:
            message = _l("Adresse email invalide.")
        super().__init__(message, **kwargs)


class EqualTo(wtforms.validators.EqualTo):
    def __init__(self,
                 fieldname: str,
                 message: JinjaStr | None = None) -> None:
        if message is None:
            message = _l("Valeur différente du champ précédent.")
        super().__init__(fieldname, message)


class MacAddress(wtforms.validators.MacAddress):
    def __init__(self, message: JinjaStr | None = None) -> None:
        if message is None:
            message = _l("Adresse MAC invalide (format attendu : "
                         "xx:xx:xx:xx:xx:xx).")
        super().__init__(message)


class Length(wtforms.validators.Length):
    def __init__(self,
                 min: int = -1,
                 max: int = -1,
                 message: JinjaStr | None = None) -> None:
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


class NewEmail(CustomValidator):
    message = _l("Adresse e-mail déjà liée à un autre compte.")

    def validate(self, form: wtforms.Form, field: wtforms.Field) -> bool:
        rezident = Rezident.query.filter_by(email=field.data).first()
        return (rezident is None) or (rezident == flask.g.rezident)


class ValidRoom(CustomValidator):
    message = _l("Numéro de chambre invalide.")

    def validate(self, form: wtforms.Form, field: wtforms.Field) -> bool:
        return bool(Room.query.get(field.data))


class PastDate(CustomValidator):
    message = _l("Cette date doit être dans le passé !")

    def validate(self, form: wtforms.Form, field: wtforms.Field) -> bool:
        if not field.data:
            return True
        return (field.data <= datetime.date.today())


class FutureDate(CustomValidator):
    message = _l("Cette date doit être dans le futur !")

    def validate(self, form: wtforms.Form, field: wtforms.Field) -> bool:
        if not field.data:
            return True
        return (field.data >= datetime.date.today())

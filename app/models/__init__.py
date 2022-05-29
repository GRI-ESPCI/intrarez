"""Intranet de la Rez Flask App - Database Models"""

import typing

from app import db


Model = typing.cast(type[type], db.Model)  # type checking hack


from app.enums import PaymentStatus, SubState

from app.models.auth import Rezident
from app.models.gris import Ban
from app.models.intrarez import Allocation, Device, Rental, Room
from app.models.payments import Offer, Payment, Subscription

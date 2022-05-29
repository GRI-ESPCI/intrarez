"""Intranet de la Rez Flask App - Database Models"""

from __future__ import annotations

import datetime
import typing

from dateutil import relativedelta
import sqlalchemy as sa

from app import db
from app.utils.columns import (
    column,
    many_to_one,
    Column,
    Relationship,
)

Model = typing.cast(type[type], db.Model)  # type checking hack


class Ban(Model):
    """A ban of a Rezident from accessing the Internet."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"), nullable=False)
    rezident: Relationship[models.Rezident] = many_to_one("Rezident.bans")
    start: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    end: Column[datetime.datetime | None] = column(sa.DateTime())
    reason: Column[str | None] = column(sa.String(32), nullable=False)
    message: Column[str | None] = column(sa.String(2000))

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Ban #{self.id} of {self.rezident} (-> {self.end})>"

    @property
    def duration(self) -> relativedelta.relativedelta | None:
        """Relative delta ``end - start``, or ``None`` if no end."""
        if self.end:
            return relativedelta.relativedelta(self.end, self.start)
        else:
            return None

    @property
    def is_active(self) -> bool:
        """Whether the ban is currently active."""
        now = datetime.datetime.utcnow()
        return (self.start <= now) and ((not self.end) or now < self.end)


from app import models

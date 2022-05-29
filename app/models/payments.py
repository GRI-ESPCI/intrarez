"""Intranet de la Rez Flask App - Database Models"""

from __future__ import annotations

import datetime
import typing

from dateutil import relativedelta
import flask_babel
import sqlalchemy as sa

from app import db
from app.enums import PaymentStatus
from app.utils.columns import (
    column,
    one_to_many,
    many_to_one,
    my_enum,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack
Enum = my_enum  # type checking hack


class Subscription(Model):
    """An subscription to Internet of a Rezident."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"), nullable=False)
    rezident: Relationship[models.Rezident] = many_to_one("Rezident.subscriptions")
    _offer_slug: Column[str] = column(sa.ForeignKey("offer.slug"), nullable=False)
    offer: Relationship[Offer] = many_to_one("Offer.subscriptions")
    _payment_id: Column[int | None] = column(sa.ForeignKey("payment.id"))
    payment: Relationship[Payment | None] = many_to_one("Payment.subscriptions")
    start: Column[datetime.date] = column(sa.Date(), nullable=False)
    end: Column[datetime.date] = column(sa.Date(), nullable=False)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Subscription #{self.id} of {self.rezident}>"

    @property
    def cut_day(self) -> datetime.date:
        """The day Internet access is cut if no other subscription is made."""
        return self.end + relativedelta.relativedelta(months=1, days=1)

    @property
    def renew_day(self) -> datetime.date:
        """The day the subscription replacing this one will start.

        E.g. on cut day if this subscription is active, else immediately.
        """
        if self.is_active:
            return self.cut_day
        else:
            return datetime.date.today()

    @property
    def is_active(self) -> bool:
        """Whether the subscription is active or in trial period."""
        return datetime.date.today() < self.cut_day

    @property
    def is_trial(self) -> bool:
        """Whether the subscription is in trial period."""
        return self.end <= datetime.date.today() < self.cut_day


class Payment(Model):
    """An payment made by a Rezident."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"), nullable=False)
    rezident: Relationship[models.Rezident] = many_to_one(
        "Rezident.payments", foreign_keys=_rezident_id
    )
    amount: Column[float] = column(sa.Numeric(6, 2, asdecimal=False), nullable=False)
    created: Column[datetime.date] = column(sa.DateTime(), nullable=False)
    payed: Column[datetime.date] = column(sa.DateTime())
    status: Column[PaymentStatus] = column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.creating
    )
    lydia_uuid: Column[str | None] = column(sa.String(32))
    lydia_transaction_id: Column[str | None] = column(sa.String(32))
    _gri_id: Column[int | None] = column(sa.ForeignKey("rezident.id"))
    gri: Relationship[models.Rezident] = many_to_one(
        "Rezident.payments_created", foreign_keys=_gri_id
    )

    subscriptions: Relationship[list[Subscription]] = one_to_many(
        "Subscription.payment"
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Payment #{self.id} of €{self.amount} by {self.rezident}>"


class Offer(Model):
    """An offer to subscribe to the Internet connection."""

    slug: Column[str] = column(sa.String(32), primary_key=True)
    name_fr: Column[str] = column(sa.String(64), nullable=False)
    name_en: Column[str] = column(sa.String(64), nullable=False)
    description_fr: Column[str | None] = column(sa.String(2000))
    description_en: Column[str | None] = column(sa.String(2000))
    price: Column[float | None] = typing.cast(
        Column[float | None], column(sa.Numeric(6, 2, asdecimal=False))
    )
    months: Column[int] = column(sa.Integer(), nullable=False, default=0)
    days: Column[int] = column(sa.Integer(), nullable=False, default=0)
    visible: Column[bool] = column(sa.Boolean(), nullable=False, default=True)
    active: Column[bool] = column(sa.Boolean(), nullable=False, default=True)

    subscriptions: Relationship[list[Subscription]] = one_to_many("Subscription.offer")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Offer '{self.slug}'>"

    @property
    def delay(self) -> relativedelta.relativedelta:
        """The delay of Internet granted by this offer.

        Relies on :attr:`Offer.months` and :attr:`Offer.days`.
        """
        return relativedelta.relativedelta(months=self.months, days=self.days)

    @property
    def total_delay(self) -> relativedelta.relativedelta:
        """The delay of Internet granted by this offer, plus offered month.

        Relies on :attr:`Offer.months` and :attr:`Offer.days`.
        """
        return self.delay + relativedelta.relativedelta(months=1)

    @property
    def name(self) -> str:
        """Context-localized offer name.

        One of :attr:`.name_fr` or :attr:`.name_en`, depending on the
        request context (user preferred language). Read-only property.

        Raises:
            RuntimeError: If acceded outside of a request context.
        """
        locale = flask_babel.get_locale()
        if locale is None:
            raise RuntimeError("Outside of request context")
        return self.name_fr if locale.language[:2] == "fr" else self.name_en

    @property
    def description(self) -> str:
        """Context-localized offer description.

        One of :attr:`.name_fr` or :attr:`.name_en`, depending on the
        request context (user preferred language). Read-only property.

        Raises:
            RuntimeError: If acceded outside of a request context.
        """
        locale = flask_babel.get_locale()
        if locale is None:
            raise RuntimeError("Outside of request context")
        return (
            self.description_fr if locale.language[:2] == "fr" else self.description_en
        ) or ""

    @classmethod
    def first_offer(cls) -> Offer:
        """Query method: get the welcome offer (1 free month)."""
        offer = cls.query.get("_first")
        if not offer:
            raise RuntimeError("First offer not created!")
        return offer

    @classmethod
    def create_first_offer(cls) -> Offer:
        """Factory method: create the welcome offer (1 free month)."""
        return cls(
            slug="_first",
            name_fr="<call `flask script update_offers`>",
            name_en="<call `flask script update_offers`>",
            price=0.0,
            visible=False,
            active=True,
        )


from app import models

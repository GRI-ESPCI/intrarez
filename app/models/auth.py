"""Intranet de la Rez Flask App - Database Models"""

from __future__ import annotations

import datetime
import time

import jwt
import flask
import flask_login
import sqlalchemy as sa
from werkzeug import security as wzs

from app import db
from app.enums import SubState
from app.tools import typing, utils
from app.tools.columns import (
    column,
    one_to_many,
    my_enum,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack
Enum = my_enum  # type checking hack


class Rezident(flask_login.UserMixin, Model):
    """A Rezident.

    :class:`flask_login.UserMixin` adds the following properties and methods:
        * is_authenticated: a property that is True if the rezident has
            valid credentials or False otherwise.
        * is_active: a property that is True if the rezident's account is
            active or False otherwise.
        * is_anonymous: a property that is False for regular rezidents, and
            True for a special, anonymous rezident.
        * get_id(): a method that returns a unique identifier for the
            rezident as a string.
    """

    id: Column[int] = column(sa.Integer(), primary_key=True)
    username: Column[str | None] = column(sa.String(64), unique=True)
    nom: Column[str | None] = column(sa.String(64))
    prenom: Column[str | None] = column(sa.String(64))
    promo: Column[str | None] = column(sa.String(8))
    email: Column[str | None] = column(sa.String(120), unique=True)
    locale: Column[str | None] = column(sa.String(8))
    is_gri: Column[bool] = column(sa.Boolean(), nullable=False, default=False)
    sub_state: Column[SubState] = column(
        Enum(SubState), nullable=False, default=SubState.trial
    )
    _password_hash: Column[str | None] = column(sa.String(128))

    devices: Relationship[list[models.Device]] = one_to_many("Device.rezident")
    rentals: Relationship[list[models.Rental]] = one_to_many("Rental.rezident")
    subscriptions: Relationship[list[models.Subscription]] = one_to_many(
        "Subscription.rezident"
    )
    payments: Relationship[list[models.Payment]] = one_to_many(
        "Payment.rezident", foreign_keys="Payment._rezident_id"
    )
    payments_created: Relationship[list[models.Payment]] = one_to_many(
        "Payment.gri", foreign_keys="Payment._gri_id"
    )
    bans: Relationship[list[models.Ban]] = one_to_many("Ban.rezident")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Rezident #{self.id} ('{self.username}')>"

    @property
    def full_name(self) -> str:
        """The rezidents's first + last names."""
        return f"{self.prenom} {self.nom}"

    @property
    def first_seen(self) -> datetime.datetime:
        """The first time the rezident registered a device, or now."""
        if not self.devices:
            return datetime.datetime.utcnow()
        return min(device.registered for device in self.devices)

    @property
    def current_device(self) -> models.Device | None:
        """The rezidents's last seen device, or ``None``."""
        if not self.devices:
            return None
        return max(self.devices, key=lambda device: device.last_seen_time)

    @property
    def last_seen(self) -> datetime.datetime | None:
        """The last time the rezident logged in, or ``None``."""
        if not self.current_device:
            return None
        return self.current_device.last_seen

    @property
    def other_devices(self) -> list[models.Device]:
        """The rezidents's non-current* devices.

        Sorted from most recently seen to latest seen.

        *If the rezident's "current_device" is not the device currently
        making the request (connection from outside/GRIs list), it is
        included in this list.
        """
        all = sorted(
            self.devices, key=lambda device: device.last_seen_time, reverse=True
        )
        if flask.g.internal and self == flask.g.rezident:
            # Really connected from current device: exclude it from other
            return all[1:]
        else:
            # Connected from outside/an other device: include it
            return all

    @property
    def current_rental(self) -> models.Rental | None:
        """The rezidents's current rental, or ``None``."""
        try:
            return next(rent for rent in self.rentals if rent.is_current)
        except StopIteration:
            return None

    @property
    def old_rentals(self) -> list[models.Rental]:
        """The rezidents's non-current rentals."""
        return [rental for rental in self.rentals if not rental.is_current]

    @property
    def current_room(self) -> models.Room | None:
        """The rezidents's current room, or ``None``."""
        current_rental = self.current_rental
        return current_rental.room if current_rental else None

    @property
    def has_a_room(self) -> bool:
        """Whether the rezident has currently a room rented."""
        return self.current_rental is not None

    @property
    def current_subscription(self) -> models.Subscription | None:
        """:class:`Subscription`: The rezidents's current subscription, or
        ``None``."""
        if not self.subscriptions:
            return None
        return max(self.subscriptions, key=lambda sub: sub.start)

    @property
    def old_subscriptions(self) -> list[models.Subscription]:
        """:class:`list[Subscription]`: The rezidents's non-current
        subscriptions.

        Sorted from most recent to last recent subscription."""
        return sorted(
            (sub for sub in self.subscriptions if not sub.is_active),
            key=lambda sub: sub.end,
            reverse=True,
        )

    def compute_sub_state(self) -> SubState:
        """Compute the rezidents's subscription state.

        Theoretically returns :attr:`~Rezident.sub_state`, but computed
        from :attr:`~Rezident.subscriptions`: it will differ the first
        minutes of the day of state change, before the daily scheduled
        script ``update_sub_states`` changes it.

        Returns:
            :class:.SubState`:
        """
        sub = self.current_subscription
        if not sub:
            # Default: trial
            return SubState.trial
        elif not sub.is_active:
            return SubState.outlaw
        elif sub.is_trial:
            return SubState.trial
        else:
            return SubState.subscribed

    def add_first_subscription(self) -> None:
        """ "Add subscription to first offer (free month).

        The subscription starts the day the Rezident registered its first
        device (usually today), and ends today.
        """
        if not self.devices:
            return
        offer = models.Offer.first_offer()
        start = self.first_seen.date()
        sub = models.Subscription(
            rezident=self,
            offer=offer,
            payment=None,
            start=start,
            end=datetime.date.today(),
        )
        db.session.add(sub)
        self.sub_state = SubState.trial
        db.session.commit()
        utils.log_action(
            f"Added {sub} to {offer}, with no payment, "
            f"granting Internet access for {start} – {start + offer.delay}"
        )

    @property
    def current_ban(self) -> models.Ban | None:
        """The rezident's current ban, or ``None``."""
        try:
            return next(ban for ban in self.bans if ban.is_active)
        except StopIteration:
            return None

    @property
    def is_banned(self) -> bool:
        """Whether the rezident is currently under a ban."""
        return self.current_ban is not None

    def set_password(self, password: str) -> None:
        """Save or modify rezident password.

        Relies on :func:`werkzeug.security.generate_password_hash` to
        store a password hash only.

        Args:
            password: The password to store. Not stored.
        """
        self._password_hash = wzs.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check that a given password matches stored rezident password.

        Relies on :func:`werkzeug.security.check_password_hash` to
        compare tested password with stored password hash.

        Args:
            password: The password to check. Not stored.

        Returns:
            Whether the password is correct.
        """
        return wzs.check_password_hash(self._password_hash or "", password)

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        """Forge a JWT reset password token for the rezident.

        Relies on :func:`jwt.encode`.

        Args:
            expires_in: The time before the token expires, in seconds.

        Returns:
            The created JWT token.
        """
        return jwt.encode(
            {"reset_password": self.id, "exp": time.time() + expires_in},
            flask.current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @classmethod
    def verify_reset_password_token(cls, token: str) -> Rezident | None:
        """Verify a rezident password reset token (class method).

        Relies on :func:`jwt.decode`.

        Args:
            token: The JWT token to decode.

        Returns:
            The rezident to reset password of if the token is valid and the
            rezident exists, else ``None``.
        """
        try:
            id = jwt.decode(
                token, flask.current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except Exception:
            return
        return cls.query.get(id)


from app import models

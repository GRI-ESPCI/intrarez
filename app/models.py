"""Intranet de la Rez Flask App - Database Models"""

from __future__ import annotations

import datetime
import time

from dateutil import relativedelta
import jwt
import flask
import flask_babel
import flask_login
import sqlalchemy as sa
from werkzeug import security as wzs

from app import db
from app.enums import SubState
from app.tools import typing, utils
from app.tools.columns import (column, one_to_many, many_to_one, my_enum,
                               Column, Relationship)


Model = typing.cast(type[type], db.Model)   # type checking hack
sa.Enum = my_enum                           # type checking hack


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
    sub_state: Column[SubState] = column(sa.Enum(SubState), nullable=False,
                                         default=SubState.trial)
    _password_hash: Column[str | None] = column(sa.String(128))

    devices: Relationship[list[Device]] = one_to_many("Device.rezident")
    rentals: Relationship[list[Rental]] = one_to_many("Rental.rezident")
    subscriptions: Relationship[list[Subscription]] = one_to_many(
        "Subscription.rezident"
    )
    payments: Relationship[list[Payment]] = one_to_many(
        "Payment.rezident", foreign_keys="Payment._rezident_id"
    )
    payments_created: Relationship[list[Payment]] = one_to_many(
        "Payment.gri", foreign_keys="Payment._gri_id"
    )

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
            return datetime.datetime.now()
        return min(device.registered for device in self.devices)

    @property
    def current_device(self) -> Device | None:
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
    def other_devices(self) -> list[Device]:
        """The rezidents's non-current* devices.

        Sorted from most recently seen to latest seen.

        *If the rezident's "current_device" is not the device currently
        making the request (connection from outside/GRIs list), it is
        included in this list.
        """
        all = sorted(self.devices, key=lambda device: device.last_seen_time,
                     reverse=True)
        if flask.g.internal and self == flask.g.rezident:
            # Really connected from current device: exclude it from other
            return all[1:]
        else:
            # Connected from outside/an other device: include it
            return all

    @property
    def current_rental(self) -> Rental | None:
        """The rezidents's current rental, or ``None``."""
        try:
            return next(rent for rent in self.rentals if rent.is_current)
        except StopIteration:
            return None

    @property
    def old_rentals(self) -> list[Rental]:
        """The rezidents's non-current rentals."""
        return [rental for rental in self.rentals if not rental.is_current]

    @property
    def current_room(self) -> Room | None:
        """The rezidents's current room, or ``None``."""
        current_rental = self.current_rental
        return current_rental.room if current_rental else None

    @property
    def has_a_room(self) -> bool:
        """Whether the rezident has currently a room rented."""
        return (self.current_rental is not None)

    @property
    def current_subscription(self) -> Subscription | None:
        """:class:`Subscription`: The rezidents's current subscription, or
        ``None``."""
        if not self.subscriptions:
            return None
        return max(self.subscriptions, key=lambda sub: sub.start)

    @property
    def old_subscriptions(self) -> list[Subscription]:
        """:class:`list[Subscription]`: The rezidents's non-current
        subscriptions.

        Sorted from most recent to last recent subscription."""
        return sorted((sub for sub in self.subscriptions if not sub.is_active),
                      key=lambda sub: sub.end, reverse=True)

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
        """"Add subscription to first offer (free month).

        The subscription starts the day the Rezident registered its first
        device (usually today), and ends today.
        """
        if not self.devices:
            return
        offer = Offer.first_offer()
        start = self.first_seen.date()
        sub = Subscription(rezident=self, offer=offer,
                           payment=None, start=start,
                           end=datetime.date.today())
        db.session.add(sub)
        self.sub_state = SubState.trial
        db.session.commit()
        utils.log_action(
            f"Added {sub} to {offer}, with no payment, "
            f"granting Internet access for {start} – {start + offer.delay}"
        )

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
            algorithm="HS256"
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
                token,
                flask.current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )["reset_password"]
        except Exception:
            return
        return cls.query.get(id)


class Device(Model):
    """A device of a Rezident."""
    id: Column[int] = column(sa.Integer(), primary_key=True)
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"),
                                       nullable=False)
    rezident: Relationship[Rezident] = many_to_one("Rezident.devices")
    mac_address: Column[str] = column(sa.String(17), nullable=False,
                                      unique=True)
    name: Column[str | None] = column(sa.String(64))
    type: Column[str | None] = column(sa.String(64))
    registered: Column[datetime.datetime] = column(sa.DateTime(),
                                                   nullable=False)
    last_seen: Column[datetime.datetime | None] = column(sa.DateTime())

    allocations: Relationship[list[Allocation]] = one_to_many(
        "Allocation.device"
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Device #{self.id} ('{self.name}') of {self.rezident}>"

    @property
    def last_seen_time(self) -> datetime.datetime:
        """Same as :attr:`.Device.last_seen`, but cannot be ``None``.

        If a device was never seen, :attr:`.last_seen` is ``None`` but
        :attr:`.last_seen_time` is the oldest possible timestamp.
        """
        return self.last_seen or datetime.datetime(1, 1, 1)

    def update_last_seen(self) -> None:
        """Change :attr:`.Device.last_seen` timestamp to now."""
        self.last_seen = datetime.datetime.utcnow()
        db.session.commit()

    def allocate_ip_for(self, room: Room) -> str:
        """Get the specific IP to use this device in a given room.

        Create the :class`.Allocation` instance if it does not exist.

        Args:
            room: The room to allocate / get allocation for.

        Returns:
            The allocated IP.
        """
        alloc = Allocation.query.filter_by(device=self, room=room).first()
        if alloc:
            # Already allocated
            return alloc.ip
        # Create allocation
        ip = f"10.{room.ips_allocated % 256}.{room.base_ip}"
        alloc = Allocation(device=self, room=room, ip=ip)
        db.session.add(alloc)
        room.ips_allocated += 1
        db.session.commit()
        return ip

    @property
    def current_ip(self) -> str:
        """The current IP this device is connected to."""
        room = self.rezident.current_room
        if not room:
            return "[no room]"
        alloc = Allocation.query.filter_by(device=self, room=room).first()
        if not alloc:
            return "[not allocated]"
        return alloc.ip


class Rental(Model):
    """A rental of a Rezidence room by a Rezident."""
    id: Column[int] = column(sa.Integer(), primary_key=True)
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"),
                                       nullable=False)
    rezident: Relationship[Rezident] = many_to_one("Rezident.rentals")
    _room_num: Column[int] = column(sa.ForeignKey("room.num"), nullable=False)
    room: Relationship[Room] = many_to_one("Room.rentals")
    start: Column[datetime.date] = column(sa.Date(), nullable=False)
    end: Column[datetime.date | None] = column(sa.Date())

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Rental #{self.id} of {self.room} by {self.rezident}>"

    @property
    def is_current(self) -> bool:
        """Whether the rental is current."""
        return (self.end is None) or (self.end > datetime.date.today())


class Room(Model):
    """A Rezidence room."""
    num: Column[int] = column(sa.Integer(), primary_key=True)
    floor: Column[int | None] = column(sa.Integer())
    base_ip: Column[str | None] = column(sa.String(4))
    ips_allocated: Column[int] = column(sa.Integer(), nullable=False,
                                        default=0)

    rentals: Relationship[list[Rental]] = one_to_many("Rental.room")
    allocations: Relationship[list[Allocation]] = one_to_many(
        "Allocation.room"
    )

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Room {self.num}>"

    @property
    def current_rental(self) -> Rental | None:
        """The room current rental, or ``None``."""
        try:
            return next(rent for rent in self.rentals if rent.is_current)
        except StopIteration:
            return None

    @classmethod
    def create_rez_rooms(cls):
        """Create the list of existing Rezidence rooms.

        Returns:
            list[Room]
        """
        doors_per_floor = {
            1: 16,
            2: 26,
            3: 26,
            4: 26,
            5: 26,
            6: 20,
            7: 20,
        }
        rooms = []
        for floor, max_door in doors_per_floor.items():
            for door in range(1, max_door + 1):
                rooms.append(cls(num=100*floor + door, floor=floor,
                                 base_ip=f"{floor}.{door}"))
        return rooms


class Allocation(Model):
    """An allocation of an IP address to a tuple Device-Room."""
    id: Column[int] = column(sa.Integer(), primary_key=True)
    _device_id: Column[int] = column(sa.ForeignKey("device.id"),
                                     nullable=False)
    device: Relationship[Device] = many_to_one("Device.allocations")
    _room_num: Column[int] = column(sa.ForeignKey("room.num"), nullable=False)
    room: Relationship[Room] = many_to_one("Room.allocations")
    ip: Column[str] = column(sa.String(16), nullable=False)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Allocation #{self.id}: {self.ip} to {self.device}>"


class Subscription(Model):
    """An subscription to Internet of a Rezident."""
    id: Column[int] = column(sa.Integer(), primary_key=True)
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"),
                                       nullable=False)
    rezident: Relationship[Rezident] = many_to_one("Rezident.subscriptions")
    _offer_slug: Column[str] = column(sa.ForeignKey("offer.slug"),
                                      nullable=False)
    offer: Relationship[Offer] = many_to_one("Offer.subscriptions")
    _payment_id: Column[int | None] = column(sa.ForeignKey("payment.id"))
    payment: Relationship[Payment | None] = many_to_one(
        "Payment.subscriptions"
    )
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
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"),
                                       nullable=False)
    rezident: Relationship[Rezident] = many_to_one("Rezident.payments",
                                     foreign_keys=_rezident_id)
    amount: Column[float] = typing.cast(    # Decimal -> float cast
        Column[float], column(sa.Numeric(6, 2, asdecimal=False),
                              nullable=False)
    )
    timestamp: Column[datetime.date] = column(sa.DateTime(), nullable=False)
    lydia: Column[bool] = column(sa.Boolean(), nullable=False)
    lydia_id: Column[int | None] = column(sa.BigInteger())
    _gri_id: Column[int | None] = column(sa.ForeignKey("rezident.id"))
    gri: Relationship[Rezident] = many_to_one("Rezident.payments_created",
                                foreign_keys=_gri_id)

    subscriptions: Relationship[list[Subscription]] = one_to_many("Subscription.payment")

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Payment #{self.id} of €{self.amount} by {self.rezident}>"


import dataclasses

# @dataclasses.dataclass
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

    subscriptions: Relationship[list[Subscription]] = one_to_many(
        "Subscription.offer"
    )

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
        return (self.description_fr if locale.language[:2] == "fr"
                else self.description_en) or ""

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
            visible="False",
            active=True,
        )

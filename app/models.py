"""Intranet de la Rez Flask App - Database Models"""

import time
import datetime

from dateutil import relativedelta
import jwt
import flask
import flask_login
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug import security as wzs

from app import db
from app.enums import *
from app.tools import utils


class Rezident(flask_login.UserMixin, db.Model):
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
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(64), unique=True)
    nom = db.Column(db.String(64))
    prenom = db.Column(db.String(64))
    promo = db.Column(db.String(8))
    email = db.Column(db.String(120), unique=True)
    is_gri = db.Column(db.Boolean(), nullable=False, default=False)
    sub_state = db.Column(db.Enum(SubState), nullable=False,
                          default=SubState.trial)
    _password_hash = db.Column(db.String(128))

    devices = db.relationship("Device", back_populates="rezident")
    rentals = db.relationship("Rental", back_populates="rezident")
    subscriptions = db.relationship("Subscription", back_populates="rezident")
    payments = db.relationship("Payment", back_populates="rezident",
                               foreign_keys="Payment._rezident_id")
    payments_created = db.relationship("Payment", back_populates="gri",
                                       foreign_keys="Payment._gri_id")

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Rezident #{self.id} ('{self.username}')>"

    @property
    def full_name(self):
        """:class:`str`: The rezidents's first + last names."""
        return f"{self.prenom} {self.nom}"

    @property
    def first_seen(self):
        """:class:`.datetime.datetime`: The first time the rezident registered
        a device, or ``None``."""
        if not self.devices:
            return None
        return min(device.registered for device in self.devices)

    @property
    def current_device(self):
        """:class:`.Device`: The rezidents's last seen device, or ``None``."""
        if not self.devices:
            return None
        return max(self.devices, key=lambda device: device.last_seen_time)

    @property
    def last_seen(self):
        """:class:`datetime.datetime`: The last time the rezident logged in,
        or ``None``."""
        if not self.current_device:
            return None
        return self.current_device.last_seen

    @property
    def other_devices(self):
        """:class:`list[Device]`: The rezidents's non-current* devices.

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
    def current_rental(self):
        """:class:`Rental`: The rezidents's current rental, or ``None``."""
        try:
            return next(rent for rent in self.rentals if rent.is_current)
        except StopIteration:
            return None

    @property
    def old_rentals(self):
        """:class:`list[Rental]`: The rezidents's non-current rentals."""
        return [rental for rental in self.rentals if not rental.is_current]

    @property
    def current_room(self):
        """:class:`Room`: The rezidents's current room, or ``None``."""
        current_rental = self.current_rental
        return current_rental.room if current_rental else None

    @hybrid_property
    def has_a_room(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (class):
        Whether the rezident has currently a room rented.

        Hybrid property (:class:`sqlalchemy.ext.hybrid.hybrid_property`):
            - On the instance, returns directly the boolean value;
            - On the class, returns the clause to use to filter rezidents that
              have a room.

        Examples::

            rezident.has_a_room         # bool
            Rezident.query.filter(Rezident.has_a_room).all()
        """
        return (self.current_rental is not None)

    @has_a_room.expression
    def has_a_room(cls):
        return cls.rentals.any(Rental.is_current)

    @property
    def current_subscription(self):
        """:class:`Subscription`: The rezidents's current subscription, or
        ``None``."""
        if not self.subscriptions:
            return None
        return max(self.subscriptions, key=lambda sub: sub.start)

    @property
    def old_subscriptions(self):
        """:class:`list[Subscription]`: The rezidents's non-current
        subscriptions.

        Sorted from most recent to last recent subscription."""
        return sorted((sub for sub in self.subscriptions if not sub.is_active),
                      key=lambda sub: sub.end, reverse=True)

    @property
    def computed_sub_state(self):
        """:class:.SubState`: The rezidents's subscription state.

        Theorically identical to :attr:`~Rezident.sub_state`, but computed
        from :attr:`~Rezident.subscriptions`. It might differ the first
        minutes of the day of state change.
        """
        sub = self.current_subscription
        if not sub.is_active:
            return SubState.outlaw
        elif sub.is_trial:
            return SubState.trial
        else:
            return SubState.subscribed

    def add_first_subscription(self, start=None):
        """"Add subscription to first offer (free month).

        The subscription starts the day the Rezident registered its first
        device (usually today), and ends today.
        """
        start = (self.first_seen.date() if self.devices
                 else datetime.date.today())
        sub = Subscription(rezident=self, offer=Offer.first_offer(),
                           payment=None, start=start,
                           end=datetime.date.today())
        db.session.add(sub)
        self.sub_state = SubState.trial
        db.session.commit()

    def set_password(self, password):
        """Save or modify rezident password.

        Relies on :func:`werkzeug.security.generate_password_hash` to
        store a password hash only.

        Args:
            password (str): The password to store. Not stored.
        """
        self._password_hash = wzs.generate_password_hash(password)

    def check_password(self, password):
        """Check that a given password matches stored rezident password.

        Relies on :func:`werkzeug.security.check_password_hash` to
        compare tested password with stored password hash.

        Args:
            password (str): The password to check. Not stored.

        Returns:
            Whether the password is correct (bool).
        """
        return wzs.check_password_hash(self._password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        """Forge a JWT reset password token for the rezident.

        Relies on :func:`jwt.encode`.

        Args:
            expires_in (int): The time before the token expires, in seconds.

        Returns:
            The created JWT token (str).
        """
        return jwt.encode(
            {"reset_password": self.id, "exp": time.time() + expires_in},
            flask.current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

    @classmethod
    def verify_reset_password_token(cls, token):
        """Verify a rezident password reset token (class method).

        Relies on :func:`jwt.decode`.

        Args:
            token (str): The JWT token to decode.

        Returns:
            The rezident to reset password of if the token is valid and the
            rezident exists, else ``None``.
        """
        try:
            id = jwt.decode(token, flask.current_app.config["SECRET_KEY"],
                            algorithms=["HS256"])["reset_password"]
        except Exception:
            return
        return cls.query.get(id)


class Device(db.Model):
    """A device of a Rezident."""
    id = db.Column(db.Integer(), primary_key=True)
    _rezident_id = db.Column(db.ForeignKey("rezident.id"), nullable=False)
    rezident = db.relationship("Rezident", back_populates="devices")
    name = db.Column(db.String(64))
    mac_address = db.Column(db.String(17), nullable=False, unique=True)
    type = db.Column(db.String(64))
    registered = db.Column(db.DateTime(), nullable=False)
    last_seen = db.Column(db.DateTime(), nullable=True)

    allocations = db.relationship("Allocation", back_populates="device")

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Device #{self.id} ('{self.name}') of {self.rezident}>"

    @property
    def last_seen_time(self):
        """:class:`datetime.datetime`: Same as :attr:`.Device.last_seen`
        with very old timestamp instead ``None`` (if never seen)."""
        return self.last_seen or datetime.datetime(1, 1, 1)

    def update_last_seen(self):
        """Update :attr:`.Device.last_seen` timestamp."""
        self.last_seen = datetime.datetime.utcnow()
        db.session.commit()

    def allocate_ip_for(self, room):
        """Get the specific IP to use this device in a given room.

        Create the :class`.Allocation` instance if it does not exist.

        Args:
            room (.Room): The room to allocate / get allocation for.

        Returns:
            :class:`str`: The allocated IP.
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
    def current_ip(self):
        """str: The current IP this device is connected to."""
        room = self.rezident.current_room
        if not room:
            return "[no room]"
        alloc = Allocation.query.filter_by(device=self, room=room).first()
        if not alloc:
            return "[not allocated]"
        return alloc.ip


class Rental(db.Model):
    """A rental of a Rezidence room by a Rezident."""
    id = db.Column(db.Integer(), primary_key=True)
    _rezident_id = db.Column(db.ForeignKey("rezident.id"), nullable=False)
    rezident = db.relationship("Rezident", back_populates="rentals")
    _room_num = db.Column(db.ForeignKey("room.num"), nullable=False)
    room = db.relationship("Room", back_populates="rentals")
    start = db.Column(db.Date(), nullable=False)
    end = db.Column(db.Date())

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Rental #{self.id} of {self.room} by {self.rezident}>"

    @hybrid_property
    def is_current(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (class):
        Whether the rental is current.

        Hybrid property (see :meth:`Rezident.has_a_room`).
        """
        today = datetime.date.today()
        return (self.end is None) or (self.end > today)

    @is_current.expression
    def is_current(cls):
        today = datetime.date.today()
        return ((cls.end.is_(None)) | (cls.end > today))

    def terminate(self):
        """Set the rental end date to today (not current)"""
        today = datetime.date.today()
        self.end = today
        db.session.commit()


class Room(db.Model):
    """A Rezidence room."""
    num = db.Column(db.Integer(), primary_key=True)
    floor = db.Column(db.Integer())
    base_ip = db.Column(db.String(4))
    ips_allocated = db.Column(db.Integer(), nullable=False, default=0)

    rentals = db.relationship("Rental", back_populates="room")
    allocations = db.relationship("Allocation", back_populates="room")

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Room {self.num}>"

    @property
    def current_rental(self):
        """:class:`Rental`: The room current rental, or ``None``."""
        try:
            return next(rent for rent in self.rentals if rent.is_current)
        except StopIteration:
            return None

    @hybrid_property
    def is_currently_rented(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (class):
        Whether the room is currently rented.

        Hybrid property (see :meth:`Rezident.has_a_room`).
        """
        return (self.current_rental is not None)

    @is_currently_rented.expression
    def is_currently_rented(cls):
        return cls.rentals.any(Rental.is_current)

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


class Allocation(db.Model):
    """An allocation of an IP address to a tuple Device-Room."""
    id = db.Column(db.Integer(), primary_key=True)
    _device_id = db.Column(db.ForeignKey("device.id"), nullable=False)
    device = db.relationship("Device", back_populates="allocations")
    _room_num = db.Column(db.ForeignKey("room.num"), nullable=False)
    room = db.relationship("Room", back_populates="allocations")
    ip = db.Column(db.String(16), nullable=False)

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Allocation #{self.id}: {self.ip}>"


class Subscription(db.Model):
    """An subscription to Internet of a Rezident."""
    id = db.Column(db.Integer(), primary_key=True)
    _rezident_id = db.Column(db.ForeignKey("rezident.id"), nullable=False)
    rezident = db.relationship("Rezident", back_populates="subscriptions")
    _offer_slug = db.Column(db.ForeignKey("offer.slug"), nullable=False)
    offer = db.relationship("Offer", back_populates="subscriptions")
    _payment_id = db.Column(db.ForeignKey("payment.id"))
    payment = db.relationship("Payment", back_populates="subscriptions")
    start = db.Column(db.Date(), nullable=False)
    end = db.Column(db.Date(), nullable=False)

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Subscription #{self.id} of {self.rezident}>"

    @property
    def cut_day(self):
        """:class:`datetime.date`: The day Internet acces is cut if no
        other subscription is made."""
        return self.end + relativedelta.relativedelta(months=1, days=1)

    @property
    def is_active(self):
        """:class:`bool`: Whether the subscription is active or in trial
        period."""
        return datetime.date.today() < self.cut_day

    @property
    def is_trial(self):
        """:class:`bool`: Whether the subscription is in trial period."""
        return self.end <= datetime.date.today() < self.cut_day


class Payment(db.Model):
    """An payment made by a Rezident."""
    id = db.Column(db.Integer(), primary_key=True)
    _rezident_id = db.Column(db.ForeignKey("rezident.id"), nullable=False)
    rezident = db.relationship("Rezident", back_populates="payments",
                               foreign_keys=_rezident_id)
    amount = db.Column(db.Numeric(6, 2, asdecimal=False), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    lydia = db.Column(db.Boolean(), nullable=False)
    lydia_id = db.Column(db.BigInteger())
    _gri_id = db.Column(db.ForeignKey("rezident.id"))
    gri = db.relationship("Rezident", back_populates="payments_created",
                               foreign_keys=_gri_id)

    subscriptions = db.relationship("Subscription", back_populates="payment")

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Payment #{self.id} of €{self.amount} by {self.rezident}>"

    @property
    def amount_format(self):
        """:class:`str`: :attr:`Payment.amount` formatted depending on current
        user locale."""
        famt = format(self.amount, ".2f")
        if utils.get_locale() == "fr":
            famt = famt.replace(".", ",")
        return flask.Markup(f"{famt}&nbsp;€")


class Offer(db.Model):
    """An offer to subscibe to the Internet connection."""
    slug = db.Column(db.String(32), primary_key=True)
    name_fr = db.Column(db.String(64), nullable=False)
    name_en = db.Column(db.String(64), nullable=False)
    description_fr = db.Column(db.String(2000))
    description_en = db.Column(db.String(2000))
    price = db.Column(db.Numeric(6, 2, asdecimal=False))
    months = db.Column(db.Integer(), nullable=False, default=0)
    days = db.Column(db.Integer(), nullable=False, default=0)
    visible = db.Column(db.Boolean(), nullable=False, default=True)
    active = db.Column(db.Boolean(), nullable=False, default=True)

    subscriptions = db.relationship("Subscription", back_populates="offer")

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Offer '{self.slug}'>"

    @property
    def delay(self):
        """:class:`.dateutil.relativedelta.relativedelta'`: The delay of
        Internet granted by this offer.

        Relies on :attr:`Offer.months` and :attr:`Offer.days`.
        """
        return relativedelta.relativedelta(months=self.months, days=self.days)

    @property
    def price_format(self):
        """:class:`str`: :attr:`Offer.price` formatted depending on current
        user locale."""
        famt = format(self.price, ".2f")
        if utils.get_locale() == "fr":
            famt = famt.replace(".", ",")
        return flask.Markup(f"{famt}&nbsp;€")

    @property
    def name(self):
        """str: Context-localized offer name.

        One of :attr:`.name_fr` or :attr:`.name_en`, depending on the
        request context (user prefered language). Read-only property.

        Raises:
            RuntimeError: If acceded outside of a request context.
        """
        locale = utils.get_locale()
        return self.name_fr if locale == "fr" else self.name_en

    @property
    def description(self):
        """str: Context-localized offer description.

        One of :attr:`.name_fr` or :attr:`.name_en`, depending on the
        request context (user prefered language). Read-only property.

        Raises:
            RuntimeError: If acceded outside of a request context.
        """
        locale = utils.get_locale()
        return self.description_fr if locale == "fr" else self.description_en

    @classmethod
    def first_offer(cls):
        """Query method: get the welcome offer (1 free month).

        Returns:
            :class:`.Offer`
        """
        return cls.query.get("_first")

    @classmethod
    def create_first_offer(cls):
        """Factory method: create the welcome offer (1 free month).

        Returns:
            :class:`.Offer`
        """
        return cls(
            slug="_first",
            name_fr="Offre de bienvenue",
            name_en="Welcoming offer",
            description_fr="Un mois d'accès à Internet offert à votre "
                           "première connexion !",
            description_en="One month of Internet access gifted when you "
                           "connect for the first time!",
            price=0.0,
            visible=False,
            active=True,
        )

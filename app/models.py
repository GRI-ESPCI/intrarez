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
    _password_hash = db.Column(db.String(128))

    devices = db.relationship("Device", back_populates="rezident")
    rentals = db.relationship("Rental", back_populates="rezident")

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Rezident #{self.id} ('{self.username}')>"

    @property
    def full_name(self):
        """:class:`str`: The rezidents's first + last names."""
        return f"{self.prenom} {self.nom}"

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
        """:class:`list[Device]`: The rezidents's non-current devices.

        Sorted from most recently seen to latest seen.
        """
        return sorted(self.devices, key=lambda device: device.last_seen_time,
                      reverse=True)[1:]

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

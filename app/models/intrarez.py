"""Intranet de la Rez Flask App - Database Models"""

from __future__ import annotations

import datetime

import sqlalchemy as sa

from app import db
from app.tools import typing
from app.tools.columns import (
    column,
    one_to_many,
    many_to_one,
    my_enum,
    Column,
    Relationship,
)


Model = typing.cast(type[type], db.Model)  # type checking hack
Enum = my_enum  # type checking hack


class Device(Model):
    """A device of a Rezident."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"), nullable=False)
    rezident: Relationship[models.Rezident] = many_to_one("Rezident.devices")
    mac_address: Column[str] = column(sa.String(17), nullable=False, unique=True)
    name: Column[str | None] = column(sa.String(64))
    type: Column[str | None] = column(sa.String(64))
    registered: Column[datetime.datetime] = column(sa.DateTime(), nullable=False)
    last_seen: Column[datetime.datetime | None] = column(sa.DateTime())

    allocations: Relationship[list[Allocation]] = one_to_many("Allocation.device")

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
        if self.rezident.is_banned:
            # Rezident banned: IP in 10.0.8-255.0-255 (encoding ban ID)
            # (i.e. a range of 126975 bans)
            ban = self.rezident.current_ban
            return f"10.0.{8 + (ban.id // 256)}.{ban.id % 256}"

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
    _rezident_id: Column[int] = column(sa.ForeignKey("rezident.id"), nullable=False)
    rezident: Relationship[models.Rezident] = many_to_one("Rezident.rentals")
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
    ips_allocated: Column[int] = column(sa.Integer(), nullable=False, default=0)

    rentals: Relationship[list[Rental]] = one_to_many("Rental.room")
    allocations: Relationship[list[Allocation]] = one_to_many("Allocation.room")

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
                rooms.append(
                    cls(num=100 * floor + door, floor=floor, base_ip=f"{floor}.{door}")
                )
        return rooms


class Allocation(Model):
    """An allocation of an IP address to a tuple Device-Room."""

    id: Column[int] = column(sa.Integer(), primary_key=True)
    _device_id: Column[int] = column(sa.ForeignKey("device.id"), nullable=False)
    device: Relationship[Device] = many_to_one("Device.allocations")
    _room_num: Column[int] = column(sa.ForeignKey("room.num"), nullable=False)
    room: Relationship[Room] = many_to_one("Room.allocations")
    ip: Column[str] = column(sa.String(16), nullable=False)

    def __repr__(self) -> str:
        """Returns repr(self)."""
        return f"<Allocation #{self.id}: {self.ip} to {self.device}>"


from app import models

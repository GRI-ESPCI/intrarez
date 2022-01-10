"""Intranet de la Rez Flask App - Database Enums"""

import enum


__all__ = ["SubState"]


class SubState(enum.Enum):
    """"The subscription state of a Rezident."""
    subscribed = enum.auto()
    trial = enum.auto()
    outlaw = enum.auto()

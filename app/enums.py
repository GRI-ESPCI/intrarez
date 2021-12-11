"""Intranet de la Rez Flask App - Database Enums"""

import enum


__all__ = ["SubState"]


class SubState(enum.Enum):
    """"The subsciption state of a Rezident."""
    subscribed = enum.auto()
    trial = enum.auto()
    outlaw = enum.auto()

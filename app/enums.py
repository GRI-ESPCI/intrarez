"""Intranet de la Rez Flask App - Database Enums"""

import enum


__all__ = ["SubState", "PaymentStatus"]


class SubState(enum.Enum):
    """"The subscription state of a Rezident."""
    subscribed = enum.auto()
    trial = enum.auto()
    outlaw = enum.auto()


class PaymentStatus(enum.Enum):
    """"The status of a Payment."""
    manual = enum.auto()
    creating = enum.auto()
    waiting = enum.auto()
    accepted = enum.auto()
    refused = enum.auto()
    cancelled = enum.auto()
    error = enum.auto()

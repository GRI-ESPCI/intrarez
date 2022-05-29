"""Intranet de la Rez Flask App - Database Models"""

import enum
import typing

import sqlalchemy


Column = sqlalchemy.Column
Relationship = sqlalchemy.orm.RelationshipProperty

_Q = typing.TypeVar("_Q")


@typing.overload  # Primary column
def column(
    sa_type: sqlalchemy.types.TypeEngine[_Q],
    *,
    primary_key: bool,
) -> Column:  # [_Q]:
    ...


@typing.overload  # Non-nullable column
def column(
    sa_type: sqlalchemy.types.TypeEngine[_Q],
    *,
    nullable: bool,
    default: _Q | None = None,
    unique: bool = False,
) -> Column:  # [_Q]:
    ...


@typing.overload  # Nullable column
def column(
    sa_type: sqlalchemy.types.TypeEngine[_Q],
    *,
    default: _Q | None = None,
    unique: bool = False,
) -> Column:  # [_Q | None]:
    ...


@typing.overload  # Non-nullable foreign column
def column(
    sa_type: sqlalchemy.ForeignKey,
    *,
    nullable: bool,
) -> Column:  # [typing.Any]:
    ...


@typing.overload  # Nullable foreign column
def column(sa_type: sqlalchemy.ForeignKey) -> Column:  # [typing.Any]:
    ...


def column(sa_type, *, primary_key=False, nullable=False, default=None, unique=False):
    """Constructs a SQLAlchemy column.

    Args:
        sa_type: The SQLAlchemy type of the column.
        primary_key, nullable, default, unique: Passed to
            :class:`sqlalchemy.Column`.
    """
    column = Column(
        sa_type,
        primary_key=primary_key,
        nullable=nullable,
        default=default,
        unique=unique,
    )
    if isinstance(sa_type, sqlalchemy.ForeignKey):
        return typing.cast(Column, column)  # [object]
    else:
        return typing.cast(Column, column)  # [sa_type.python_type]


def _relationship(table_dot_back_populates: str, **kwargs) -> Relationship:
    try:
        table, back_populates = table_dot_back_populates.split(".")
    except ValueError:
        raise RuntimeError(
            f"Value '{table_dot_back_populates}' must be " "of form 'Table.column'"
        )
    return sqlalchemy.orm.relationship(table, back_populates=back_populates, **kwargs)


def one_to_many(
    table_dot_back_populates: str, **kwargs
) -> "Relationship":  # [list[typing.Any]]":
    """Constructs a one-to-many relationship to an other table.

    Args:
        table_dot_back_populates: The foreign column linked to this one,
            of form ``Table.column` (**many elements** of ``Table`` are
            linked to **one element** in this table).
    """
    return _relationship(table_dot_back_populates, **kwargs)


def many_to_one(
    table_dot_back_populates: str, **kwargs
) -> "Relationship":  # [typing.Any]":
    """Constructs a many-to-one relationship to an other table.

    Args:
        table_dot_back_populates: The foreign column linked to this one,
            of form ``Table.column` (**one element** of ``Table`` is
            linked to **many elements** in this table).
    """
    return _relationship(table_dot_back_populates, **kwargs)


_Enum = sqlalchemy.Enum


def my_enum(enum: type[enum.Enum]) -> sqlalchemy.types.TypeEngine:
    """:class:`sqlalchemy.Enum` but better typed.

    Args:
        enum: A Python :class:`~enum.Enum` to represent as a SQL Enum.

    Returns:
        The SQLAlchemy Enum column type related to this enum.
    """
    return typing.cast(sqlalchemy.types.TypeEngine[enum], _Enum(enum))

"""IntraRez typing utilities."""

from typing import (Any, Literal, Generic, Callable, TypeVar, ParamSpec,
                    overload, cast)

from flask import typing as flask_typing
import flask_babel


RouteReturn = flask_typing.ResponseReturnValue | str | tuple[str, int]
JinjaStr = str | flask_babel.LazyString

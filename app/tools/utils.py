"""Useful miscellaneous functions."""

import datetime
import logging
import os
import importlib

import flask
from flask_babel import lazy_gettext as _l
import werkzeug
from werkzeug import urls as wku

from app import IntraRezApp
from app.tools import typing


def log_action(message: str, warning: bool = False) -> None:
    """Report an action to Discord using :attr:`.IntraRezApp.actions_logger`.

    Args:
        message: The action description to log.
        warning: If ``True``, logs with level ``WARNING``, else ``INFO``.
    """
    current_app = flask.current_app
    if not isinstance(current_app, IntraRezApp):
        raise RuntimeError("Current app is not an IntraRezApp!?!")
    current_app.actions_logger.log(
        logging.WARNING if warning else logging.INFO,
        message
    )


def safe_redirect(endpoint: str,
                  **params: str | bool | None) -> typing.RouteReturn | None:
    """Redirect to a specific page, except if we are already here.

    Avoids infinite redirection loops caused by redirecting to the
    current request endpoint.

    It also automatically add the following URL parameters if not present:
      * ``next``, allowing to go back to the original request later if
        necessary (see :func:`tools.utils.redirect_to_next`). To disable
        this behavior, pass ``next=None``;
      * ``doas``, allowing to preserve doas mode through redirection
        (see :attr:`flask.g.doas`).

    Args:
        endpoint (str): The endpoint to redirect to (e.g. ``"main.index"``)
        **params: URL parameters to pass to :func:`flask.url_for`

    Returns:
        The redirection response, or ``None`` if unsafe.
    """
    if endpoint == flask.request.endpoint:
        # Do not redirect to request endpoint (infinite loop!)
        return None

    if "next" not in params:
        params["next"] = flask.request.endpoint
    elif params["next"] is None:
        del params["next"]

    try:
        doas = flask.g.doas
    except AttributeError:
        pass
    else:
        if doas and "doas" not in params:
            params["doas"] = flask.g.rezident.id

    return flask.redirect(flask.url_for(endpoint, **params))


def ensure_safe_redirect(endpoint: str,
                         **params: str | bool | None) -> typing.RouteReturn:
    """Like :func:`.safe_redirect`, but raises an exception if cannot redirect.

    Args:
        endpoint, *params: Passed to :func:`.safe_redirect`.

    Returns:
        The redirection response.

    Raises:
        RuntimeError: If the redirect is unsafe. Should never happend if
            calls to this function are well designed.
    """
    redirect = safe_redirect(endpoint, **params)
    if not redirect:
        raise RuntimeError(
            f"Could not safely redirect to {endpoint} with params {params} "
            f"(from {flask.request.url} / {flask.request.endpoint}"
        )
    return redirect


def redirect_to_next(**params: str | bool | None) -> typing.RouteReturn:
    """Redirect to the ``next`` request parameter, or to homepage.

    Includes securities to avoid redirecting to the same page (infinite
    loop) or to external pages (security breach).

    Args:
        **params: The query arguments, passed to :func:`flask.url_for`.

    Returns:
        The redirection response.
    """
    next_endpoint = flask.request.args.get("next", "")
    if next_endpoint == flask.request.endpoint:
        next_endpoint = "main.index"

    try:
        next_page = flask.url_for(next_endpoint, **params)
    except werkzeug.routing.BuildError:     # type: ignore
        next_page = None

    if not next_page or wku.url_parse(next_page).netloc != "":
        # Do not redirect to absolute links (possible attack)
        next_endpoint = "main.index"

    params["next"] = None
    return ensure_safe_redirect(next_endpoint, **params)


_promotions = None
_promotions_last_update = datetime.date(1, 1, 1)


def _build_promotions_list() -> dict[str, typing.JinjaStr]:
    year = datetime.datetime.now().year
    max_promo = year - 1882         # Promotion 1 en 1882
    if datetime.datetime.now().month > 6:       # > juin : nouvelle promotion
        max_promo += 1
    promos = {}
    for promo in range(max_promo, max_promo - 6, - 1):
        promos[str(promo)] = str(promo)
    # Special values
    promos["ext"] = _l("Locataire non-ESPCI")
    promos["sousloc"] = _l("Sous-locataire")
    return promos


def promotions() -> dict[str, typing.JinjaStr]:
    """Build the possible promotions depending on the current date.

    Returns:
        The mapping of promotion slug (stored in database) to name.
    """
    global _promotions, _promotions_last_update
    # Caching mechanism: build promotions list max. once a day
    if not _promotions or _promotions_last_update < datetime.date.today():
        _promotions = _build_promotions_list()
        _promotions_last_update = datetime.date.today()
    return _promotions


def run_script(name: str) -> None:
    """Run an IntraRez script.

    Args:
        name: the name of a file in scripts/, with or without the .py

    Raises:
        FileNotFoundError: if the given name is not an existing script.
    """
    if name.endswith(".py"):
        name = name[:-3]
    file = os.path.join("scripts", f"{name}.py")
    if not os.path.isfile(file):
        raise FileNotFoundError(
            f"Script '{name}' not found (should be '{os.path.abspath(file)}')"
        )
    script = importlib.import_module(f"scripts.{name}")
    script.main()


def print_progressbar(iteration: int,
                      total: int,
                      prefix: str = "",
                      suffix: str = "",
                      decimals: int = 1,
                      length: int = 100,
                      fill: str = "█",
                      print_end: str = "\r"
    ) -> None:
    """Call in a loop to create a terminal progress bar.

    Args:
        iteration: Current iteration.
        total: Total iterations.
        prefix: Prefix string.
        suffix: Suffix string.
        decimals: Positive number of decimals in percent complete.
        length: Character length of bar.
        fill: Bar fill character.
        print_end: End character (e.g. "\r", "\r\n").
    """
    percent = f"{{0:.{decimals}f}}".format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end)
    # Print new line on complete
    if iteration == total:
        print()

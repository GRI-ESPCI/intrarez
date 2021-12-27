"""Useful miscellaneous functions."""

import os
import importlib

import flask
import werkzeug
from werkzeug import urls as wku


def safe_redirect(endpoint, **params):
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
        :class:`flask.Response` | ``None``
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


def redirect_to_next(**params):
    """Redirect to the ``next`` request parameter, or to homepage.

    Includes a security to avoid redirecting to external pages.

    Args:
        **params: The query arguments, passed to :func:`flask.url_for`.

    Returns:
        The result of :func:`flask.redirect`.
    """
    next_endpoint = flask.request.args.get("next", "")

    try:
        next_page = flask.url_for(next_endpoint, **params)
    except werkzeug.routing.BuildError:
        next_page = None

    if not next_page or wku.url_parse(next_page).netloc != "":
        # Do not redirect to absolute links (possible attack)
        next_endpoint = "main.index"

    params["next"] = None
    return safe_redirect(next_endpoint, **params)


def get_bootstrap_icon(name):
    """Build the SVG code used to include a Bootstrap icon.

    Args:
        name (str): the name of the Bootstrap icon.

    return:
        A :class:`flask.Markup` with the SVG code to include the icon.
    """
    file = flask.url_for("static", filename="svg/bootstrap-icons.svg")
    return flask.Markup(f"<use href=\"{file}#{name}\" />")


def run_script(name):
    """Run an IntraRez script.

    Args:
        name (str): the name of a file in scripts/, with or without the .py

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


def print_progressbar(iteration, total, prefix='', suffix='', decimals=1,
                      length=100, fill='█', print_end="\r"):
    """Call in a loop to create a terminal progress bar.

    Args:
        iteration (int): current iteration.
        total (int): total iterations.
        prefix (str): prefix string.
        suffix (str): suffix string.
        decimals (int): positive number of decimals in percent complete.
        length (int): character length of bar.
        fill (str): bar fill character.
        print_end (str): end character (e.g. "\r", "\r\n").
    """
    percent = f"{{0:.{decimals}f}}".format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end)
    # Print new line on complete
    if iteration == total:
        print()

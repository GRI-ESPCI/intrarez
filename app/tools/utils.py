"""Useful miscellaneous functions."""

import os
import importlib

import flask
import werkzeug
from werkzeug import urls as wku


def get_locale():
    """Get the application language prefered by the remote user."""
    return flask.request.accept_languages.best_match(
        flask.current_app.config["LANGUAGES"]
    )


def redirect_to_next(**kwargs):
    """Redirect to the ``next`` request GET argument, or to homepage.

    Includes a security to avoid redirecting to external pages.

    Args:
        **kwargs: The query arguments, passed to :func:`flask.url_for`.

    Returns:
        The result of :func:`flask.redirect`.
    """
    next = flask.request.args.get("next", "")
    try:
        next_page = flask.url_for(next, **kwargs)
    except werkzeug.routing.BuildError:
        next_page = ""
    if not next_page or wku.url_parse(next_page).netloc != "":
        # Do not redirect to absolute links (possible attack)
        next_page = flask.url_for("main.index")
    return flask.redirect(next_page)


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

"""Useful miscellaneous functions."""

import flask
import werkzeug
from werkzeug import urls as wku


def redirect_to_next():
    """Redirect to the ``next`` request GET argument, or to homepage.

    Includes a security to avoid redirecting to external pages.

    Returns:
        The result of :func:`flask.redirect`.
    """
    next = flask.request.args.get("next", "")
    try:
        next_page = flask.url_for(next)
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


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1,
                     length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

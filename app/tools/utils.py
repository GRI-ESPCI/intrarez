
from werkzeug import urls as wku
import flask

def redirect_to_next():
    """Redirect to the ``next`` request GET argument, or to homepage.

    Includes a security to avoid redirecting to external pages.

    Returns:
        The result of :func:`flask.redirect`.
    """
    next_page = flask.url_for(flask.request.args.get("next", ""))
    if not next_page or wku.url_parse(next_page).netloc != "":
        # Do not redirect to absolute links (possible attack)
        next_page = flask.url_for("main.index")
    return flask.redirect(next_page)

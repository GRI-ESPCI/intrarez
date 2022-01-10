""""IntraRez - Custom request context"""

from ipaddress import IPv4Address
import functools
import re
import subprocess

import flask
from flask import g
from flask_babel import _
import flask_login

from app.models import Device, Rezident
from app.tools import utils, typing


def create_request_context() -> typing.RouteReturn | None:
    """Make checks about current request and define custom ``g`` properties.

    Intended to be registered by :func:`before_request`.

    Defines:
      * :attr:`flask.g.remote_ip` (default ``None``):
            The caller's IP. Should never be ``None``, except if there is
            a problem with Nginx and that the current user is GRI.
      * :attr:`flask.g.internal` (default ``False``):
            ``True`` if the request comes from the internal Rez network,
            ``False`` if it comes from the Internet.
      * :attr:`flask.g.mac` (default ``None``):
            The caller's MAC address. Defined only if
            :attr:`flask.g.internal` is ``True``.
      * :attr:`flask.g.logged_in` (default ``False``):
            Shorthand for :attr:`flask_login.current_user.is_authenticated`.
      * :attr:`flask.g.logged_in_user` (default ``None``):
            Shorthand for :attr:`flask_login.current_user`. Warning: ignores
            doas mechanism; please use :attr:`flask.g.rezident` instead.
      * :attr:`flask.g.doas` (default ``False``):
            If ``True``, the logged in user is a GRI that is doing an action
            as another rezident.
      * :attr:`flask.g.rezident` (default ``None``):
            The rezident the request is made as: ``None`` if not
            :attr:`flask.g.logged_in`, the controlled rezident if
            :attr:`~flask.g.doas`, or :attr:`flask.g.logged_in_user`.
      * :attr:`flask.g.is_gri` (default ``False``):
            ``True`` if the user is logged in and is a GRI.
      * :attr:`flask.g.has_a_room` (default ``False``):
            ``True`` if the user is logged in and has a current rental.
      * :attr:`flask.g.device` (default ``None``):
            The :class:`~.models.Device` of the current request, if
            registered. Not defined if attr:`flask.g.internal` is ``False``.
      * :attr:`flask.g.own_device` (default ``False``):
            ``True`` if the user is logged in and that :attr:`flask.g.device`
            is defined and owned by the user.
      * :attr:`flask.g.all_good` (default ``True``):
            ``False`` if either:
              * The user is not logged in;
              * The user is logged in but do not have a room;
              * The user is logged in, has a room but connects from
                the internal network from a device not registered;
              * The user is logged in, has a room and connects from the
                internal network from a device registered but not owned
                by him.
      * :attr:`flask.g.redemption_endpoint` (default ``None``):
            The endpoint of the page that the user must visit first to
            regularize its situation (see :func:`.all_good_only`).
            Defined only if attr:`flask.g.all_good` is ``False``.
      * :attr:`flask.g.redemption_params` (default ``{}``):
            The query parameters for attr:`flask.g.redemption_endpoint`.
    """
    # Defaults
    g.remote_ip = None
    g.mac = None
    g.internal = False
    g.logged_in = False
    g.logged_in_user = None
    g.rezident = None
    g.is_gri = False
    g.doas = False
    g.has_a_room = False
    g.device = None
    g.own_device = False
    g.all_good = True
    g.redemption_endpoint = None
    g.redemption_params = {}

    # Get user
    current_user = typing.cast(
        flask_login.AnonymousUserMixin | Rezident,
        flask_login.current_user
    )
    g.logged_in = current_user.is_authenticated
    if g.logged_in:
        g.logged_in_user = typing.cast(Rezident, current_user)
        g.rezident = g.logged_in_user       # May be overridden later if doas
        g.is_gri = g.rezident.is_gri
    else:
        g.all_good = False
        g.redemption_endpoint = "auth.auth_needed"

    # Check doas
    doas_id = flask.request.args.get("doas", "")
    doas = Rezident.query.get(doas_id) if doas_id.isdigit() else None
    if doas:
        if g.is_gri:
            g.rezident = doas
            g.is_gri = g.rezident.is_gri
            g.doas = True
        else:
            # Not authorized to do things as other rezidents!
            new_args = flask.request.args.copy()
            del new_args["doas"]
            return flask.redirect(flask.url_for(
                flask.request.endpoint or "main.index", **new_args
            ))

    # Check maintenance
    if flask.current_app.config["MAINTENANCE"]:
        if g.is_gri:
            flask.flash(_("Le site est en mode maintenance : seuls les GRI "
                          "peuvent y accéder."), "warning")
        else:
            flask.abort(503)    # 503 Service Unavailable

    # Get IP
    g.remote_ip = flask.current_app.config["FORCE_IP"] or _get_remote_ip()
    if not g.remote_ip:
        # X-Real-Ip header not set by Nginx: application bug?
        if g.is_gri:
            flask.flash("X-Real-Ip header not present! Check Nginx config!",
                        "danger")
        else:
            g.all_good = False
            g.redemption_endpoint = "devices.error"
            g.redemption_params = {"reason": "ip"}
            return utils.safe_redirect("devices.error", reason="ip")

    # Get MAC
    g.mac = flask.current_app.config["FORCE_MAC"] or _get_mac(g.remote_ip)
    g.internal = bool(g.mac)
    if not g.internal and not g.all_good:
        g.redemption_endpoint = "main.external_home"

    if not g.logged_in:
        # All further checks need a logged-in user
        return None

    # Inform type-checker we now have a real rezident
    g.rezident = typing.cast(Rezident, g.rezident)

    # Check room
    g.has_a_room = g.rezident.has_a_room
    if not g.has_a_room:
        g.all_good = False
        g.redemption_endpoint = "rooms.register"
        if not g.doas:
            g.redemption_params = {"hello": True}

    if g.internal:
        # Get device
        g.device = Device.query.filter_by(mac_address=g.mac).first()
        if g.device:
            g.device.update_last_seen()
        else:
            if g.all_good:
                # Internal but device not registered: must register
                g.all_good = False
                g.redemption_endpoint = "devices.register"
                g.redemption_params = {"mac": g.mac}
                if not g.doas:
                    g.redemption_params["hello"] = True
            # Last check need a device
            return None

        # Check device owner
        g.own_device = (g.rezident == g.device.rezident)
        if g.all_good and not g.own_device:
            # Internal, device but not owned: must transfer
            g.all_good = False
            g.redemption_endpoint = "devices.transfer"
            g.redemption_params = {"mac": g.mac}
            if not g.doas:
                g.redemption_params["hello"] = True
            return None

    # Check at least one device
    if g.all_good and not g.rezident.devices:
        g.all_good = False
        g.redemption_endpoint = "devices.register"
        return None

    # Add first subscription if necessary
    if g.all_good and not g.rezident.current_subscription:
        g.rezident.add_first_subscription()

    # All set!
    return None


def _get_remote_ip() -> str | None:
    """Fetch the remote IP from the request headers.

    Returns:
        The calling IP, or ``None`` if the header is missing.
    """
    return flask.request.headers.get("X-Real-Ip")


def _get_mac(remote_ip) -> str | None:
    """Fetch the remote rezident MAC address from the ARP table.

    Args:
        remote_ip: The IP of the remote rezident.

    Returns:
        The corresponding MAC address, or ``None`` if not in the list.
    """
    output = subprocess.run(["/sbin/arp", "-a"], capture_output=True)
    # arp -a liste toutes les correspondances IP - mac connues
    # résultat : lignes "domain (ip) at mac_address ..."
    match = re.search(rf"^.*? \({remote_ip}\) at ([0-9a-f:]{{17}}).*",
                      output.stdout.decode(), re.M)
    if match:
        return match.group(1)
    else:
        return None


# Type variables for decoraters below
_RP = typing.ParamSpec("_RP")
_Route = typing.Callable[_RP, typing.RouteReturn]


def all_good_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to all-good users.

    Redirects user to :attr:`flask.g.redemption_endpoint` if
    :attr:`flask.g.all_good` is ``False``.

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """
    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.all_good:
            return route(*args, **kwargs)
        else:
            return (utils.safe_redirect(g.redemption_endpoint,
                                        **g.redemption_params) or route())

    return new_route


def internal_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to internal network.

    Aborts with a 401 Unauthorized if the request comes from the Internet
    (:attr:`flask.g.internal` is ``False``).

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """
    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.internal:
            return route(*args, **kwargs)
        else:
            flask.abort(401)    # 401 Unauthorized
            raise   # never reached, just to tell the type checker

    return new_route


def logged_in_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to logged in users.

    Redirects user to "auth.auth_needed" if :attr:`flask.g.logged_in`
    is ``False``.

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """
    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.logged_in:
            return route(*args, **kwargs)
        else:
            flask.flash(_("Veuillez vous authentifier pour accéder "
                          "à cette page."), "warning")
            return utils.ensure_safe_redirect("auth.auth_needed")

    return new_route


def gris_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to logged in GRIs.

    Aborts with a 403 if :attr:`flask.g.is_gri` is ``False``.

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """
    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.is_gri:
            return route(*args, **kwargs)
        elif g.logged_in:
            flask.abort(403)    # 403 Not Authorized
            raise   # never reached, just to tell the type checker
        else:
            flask.flash(_("Veuillez vous authentifier pour accéder "
                          "à cette page."), "warning")
            return utils.ensure_safe_redirect("auth.login")

    return new_route


def _address_in_range(address: str, start: str, stop: str) -> bool:
    return (IPv4Address(start) <= IPv4Address(address) <= IPv4Address(stop))


def capture() -> typing.RouteReturn | None:
    """"Redirect request to the adequate page based on its remote IP.

    Function called by the captive portal if the requested address is not one
    of the IntraRez.

    Returns:
        The return value of :func:`flask.redirect`, or ``None`` if we are
        already on the adequate page (process request).
    """
    remote_ip = _get_remote_ip()
    if not remote_ip:
        # X-Real-Ip header not set by Nginx: application bug?
        return utils.safe_redirect("devices.error", reason="ip")
    if _address_in_range(remote_ip, "10.0.0.100", "10.0.0.199"):
        # 10.0.0.100 - 10.0.0.199: Not registered
        return utils.safe_redirect("main.index")
    if _address_in_range(remote_ip, "10.0.8.0", "10.0.8.255"):
        # 10.0.8.x: Not subscribed
        return utils.safe_redirect("main.index")    # Not implemented
    if _address_in_range(remote_ip, "10.0.9.0", "10.0.9.255"):
        # 10.0.9.x: Banned
        return utils.safe_redirect("main.index")    # Not implemented

    return utils.safe_redirect("main.index")

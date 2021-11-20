"""Intranet de la Rez - Devices Pages Routes"""

import datetime
import functools
import subprocess
import random
import re

import flask
import flask_login
from flask_babel import _

from app import db
from app.models import Device
from app.devices import bp, forms
from app.tools.utils import redirect_to_next, run_script


def get_mac(remote_ip):
    """Fetch the remote rezident MAC address from the ARP table.

    Args:
        remote_ip: The IP of the remote rezident.

    Returns:
        The corresponding MAC address, or ``None`` if not in the list.
    """
    result = subprocess.run(["/sbin/arp", "-a"], capture_output=True)
    # arp -a liste toutes les correspondances IP - mac connues
    # résultat : lignes "domain (ip) at mac_address ..."
    mtch = re.search(rf"^.*? \({remote_ip}\) at ([0-9a-f:]{{17}}).*",
                     result.stdout.decode(), re.M)
    if mtch:
        return mtch.group(1)
    else:
        return None


def check_device(routine):
    """Route function decorator to check the current device status is OK.

    Args:
        routine (function): The route function to restrict access to.

    Returns:
        The protected routine.
    """
    def _redirect_if_safe(endpoint, **params):
        if endpoint == flask.request.endpoint:
            # Ne pas regireiger vers le même endpoint (boucle infinie !)
            return routine()
        else:
            return flask.redirect(flask.url_for(endpoint, **params))

    @functools.wraps(routine)
    def new_routine():
        # Si on renvoie vers une autre page (opération nécessaire),
        # rediriger vers la requête originale ensuite
        next = flask.request.endpoint

        remote_ip = flask.request.headers.get("X-Real-Ip")
        if not remote_ip:
            # Header X-Real-Ip non présent : il est créé par Nginx en
            # transférant la requête, donc on doit être en mode test
            return _redirect_if_safe("devices.error", next=next, reason="ip")

        mac = get_mac(remote_ip)
        if not mac:
            # MAC non présente dans la table ARP : ???
            return _redirect_if_safe("devices.error", next=next, reason="mac")

        # Pour la suite, on a besoin que l'utilisateur soit connecté...
        if not flask_login.current_user.is_authenticated:
            return _redirect_if_safe("devices.auth_needed", next=next)

        # ...et qu'il ait une location en cours
        if not flask_login.current_user.has_a_room:
            return _redirect_if_safe("rooms.register", next=next)

        # On cherche l'appareil avec cette adresse MAC
        device = Device.query.filter_by(mac_address=mac).first()
        device.update_last_seen()
        if not device:
            # Appareil inconnu => enregistrer l'appareil
            return _redirect_if_safe("devices.register", mac=mac, next=next)

        # L'appareil est enregistré : on vérifie son propriétaire
        if flask_login.current_user != device.rezident:
            # Appareil lié à un autre utilisateur => Transférer
            return _redirect_if_safe("devices.transfer", mac=mac, next=next)

        # L'appareil est lié à l'utilisateur connecté => OK !
        if (flask.request.endpoint.startswith("devices.")
            and not flask.request.args.get("force")
            and not flask.request.endpoint.endswith("connect_check")):
            # Si procédure d'enrgistrement d'appareil en cours, on dégage
            return _redirect_if_safe("main.index")

        return routine()

    return new_routine


@bp.route("/auth_needed")
@check_device
def auth_needed():
    """Device auth_needed page."""
    return flask.render_template("devices/auth_needed.html",
                                 title=_("Bienvenue sur l'IntraRez !"))


@bp.route("/register", methods=["GET", "POST"])
@check_device
def register():
    """Device register page."""
    form = forms.DeviceRegistrationForm()
    if form.validate_on_submit():
        # Check not already registered
        if Device.query.filter_by(mac_address=form.mac.data).first():
            flask.flash(_("Cet appareil est déjà enregistré !"), "danger")
        else:
            now = datetime.datetime.now(datetime.timezone.utc)
            device = Device(
                rezident=flask_login.current_user, name=form.nom.data,
                mac_address=form.mac.data.lower(), type=form.type.data,
                registered=now, last_seen=None,
            )
            db.session.add(device)
            db.session.commit()
            run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Appareil enregistré avec succès !"), "success")
            # OK
            if flask.request.args.get("force"):
                return redirect_to_next()
            return flask.redirect(flask.url_for("devices.connect_check",
                                                **flask.request.args))

    return flask.render_template("devices/register.html",
                                 title=_("Enregistrer l'appareil"), form=form)


@check_device
@bp.route("/transfer", methods=["GET", "POST"])
def transfer():
    """Device transfer page."""
    form = forms.DeviceTransferForm()
    if form.validate_on_submit():
        # Check not already registered
        device = Device.query.filter_by(mac_address=form.mac.data).first()
        if not device:
            flask.flash(_("Cet appareil n'est pas encore enregistré !"),
                        "danger")
        elif device.rezident == flask_login.current_user:
            flask.flash(_("Cet appareil vous appartient déjà !"), "danger")
        else:
            device.rezident = flask_login.current_user
            db.session.commit()
            run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Appareil transféré avec succès !"), "success")
            # OK
            if flask.request.args.get("force"):
                return redirect_to_next()
            else:
                return flask.redirect(flask.url_for("devices.connect_check",
                                                    **flask.request.args))

    mac = flask.request.args.get("mac", "")
    device = Device.query.filter_by(mac_address=mac).first()
    if not device:
        # Block accessing this form to transfer a non-existing device
        flask.redirect(flask.url_for("main.index"))
    elif device.rezident == flask_login.current_user:
        return redirect_to_next()

    return flask.render_template("devices/transfer.html",
                                 title=_("Transférer l'appareil"),
                                 form=form, device=device)


@bp.route("/error")
@check_device
def error():
    """Device error page."""
    messages = {
        "ip": "Missing X-Real-Ip header",
        "mac": "X-Real-Ip address not in ARP table",
    }
    blabla = [
        "",
        _("Hmm, ça n'a pas marché..."),
        _("Non, toujours pas..."),
        _("Ah ! Ah non, non plus..."),
        _("Nan mais quand ça veut pas, ça veut pas..."),
        _("Ça va sinon ?"),
        _("Il ne va plus se passer grand chose, hein, je pense."),
        _("Après on sait jamais, sur un malentendu..."),
        _("zzzzzzzzzzzzzzzzzzzzzzzzz"),
        _("Attention, je vais commencer à dire des choses aléatoires."),
        _("Je vous aurai prévenu !"),
    ]
    reason = flask.request.args.get("reason")
    step = flask.request.args.get("step", 0)
    try:
        step = int(step)
    except ValueError:
        step = 0
    if step >= len(blabla):
        step = random.randrange(1, len(blabla))
    return flask.render_template("devices/error.html",
                                 title=_("Détection d'appareil impossible"),
                                 reason=messages.get(reason, "Unknown"),
                                 message=blabla[step])


@bp.route("/connect_check")
@check_device
def connect_check():
    """Connect check page."""
    return flask.render_template("devices/connect_check.html",
                                 title=_("Accès à Internet"))

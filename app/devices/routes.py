"""Intranet de la Rez - Devices Pages Routes"""

import datetime
import random

import flask
from flask import g
from flask_babel import _

from app import db, context
from app.devices import bp, forms
from app.models import Device
from app.tools import utils, typing


@bp.route("/register", methods=["GET", "POST"])
@context.all_good_only
def register() -> typing.RouteReturn:
    """Device register page."""
    form = forms.DeviceRegistrationForm()
    if form.validate_on_submit():
        # Check not already registered
        mac_address = form.mac.data.lower()
        if Device.query.filter_by(mac_address=mac_address).first():
            flask.flash(_("Cet appareil est déjà enregistré !"), "danger")
        else:
            device = Device(
                rezident=g.rezident,
                name=form.nom.data,
                mac_address=mac_address,
                type=form.type.data,
                registered=datetime.datetime.now(datetime.timezone.utc),
            )
            db.session.add(device)
            db.session.commit()
            utils.log_action(
                f"Registered {device} ({mac_address}, type '{device.type}')"
            )
            utils.run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Appareil enregistré avec succès !"), "success")
            # OK
            if flask.request.args.get("hello"):
                # First connection: go to connect check
                return utils.ensure_safe_redirect("main.connect_check",
                                                  hello=True)
            return utils.redirect_to_next()

    return flask.render_template("devices/register.html",
                                 title=_("Enregistrer l'appareil"),
                                 form=form)


@bp.route("/modify", methods=["GET", "POST"])
@bp.route("/modify/<device_id>", methods=["GET", "POST"])
@context.all_good_only
def modify(device_id: str | None = None) -> typing.RouteReturn:
    """Rental modification page."""
    device = None
    if device_id is None:
        device = flask.g.rezident.current_device
    elif device_id.isdigit():
        device = Device.query.get(device_id)

    if not device:
        flask.flash(_("Appareil inconnu !"), "danger")

    form = forms.DeviceModificationForm()
    if form.validate_on_submit():
        if form.submit.data:
            # The submit button used was the form one: modify the device
            device.name = form.nom.data
            device.type = form.type.data
            flask.flash(_("Appareil modifié avec succès !"), "success")
        else:
            # The submit button used was not the form one (so it was the
            # confirm-delete one): delete the device
            # device.active = False
            flask.flash(_("Action non implémentée"), "warning")

        db.session.commit()
        utils.log_action(
            f"Modified {device} (type '{device.type}')"
        )
        return utils.redirect_to_next()

    return flask.render_template("devices/modify.html",
                                 title=_("Modifier un appareil"),
                                 device=device, form=form)


@bp.route("/transfer", methods=["GET", "POST"])
@context.all_good_only
def transfer() -> typing.RouteReturn:
    """Device transfer page."""
    form = forms.DeviceTransferForm()
    if form.validate_on_submit():
        # Check not already registered
        device = Device.query.filter_by(mac_address=form.mac.data).first()
        if not device:
            flask.flash(_("Cet appareil n'est pas encore enregistré !"),
                        "danger")
        elif device.rezident == g.rezident:
            flask.flash(_("Cet appareil vous appartient déjà !"), "danger")
        elif device.rezident.is_banned:
            flask.flash(_("Cet appareil appartient à un utilisateur banni. "
                          "Son transfert est donc bloqué pour éviter les "
                          "tentatives de contournement ; contactez-nous si "
                          "la demande est légitime."), "danger")
        else:
            old_rezident = device.rezident
            device.rezident = g.rezident
            db.session.commit()
            utils.log_action(
                f"Transferred {device}, formerly owned by {old_rezident}"
            )
            utils.run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Appareil transféré avec succès !"), "success")
            # OK
            if flask.request.args.get("hello"):
                # First connection: go to connect check
                return utils.ensure_safe_redirect("main.connect_check",
                                                  hello=True)
            return utils.redirect_to_next()

    mac = flask.request.args.get("mac", "")
    device = Device.query.filter_by(mac_address=mac).first()
    if (not device) or (device.rezident == g.rezident):
        # Block accessing this form to transfer a non-existing device
        return utils.redirect_to_next()

    return flask.render_template("devices/transfer.html",
                                 title=_("Transférer l'appareil"),
                                 form=form, device=device)


@bp.route("/error")
@context.all_good_only
def error() -> typing.RouteReturn:
    """Device error page."""
    if g.all_good:
        # All good: no error, so out of here!
        return utils.redirect_to_next()

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
    reason = flask.request.args.get("reason") or "Unknown"
    step = flask.request.args.get("step", 0)
    try:
        step = int(step)
    except ValueError:
        step = 0
    if step >= len(blabla):
        step = random.randrange(1, len(blabla))
    return flask.render_template("devices/error.html",
                                 title=_("Détection d'appareil impossible"),
                                 reason=messages.get(reason),
                                 message=blabla[step])

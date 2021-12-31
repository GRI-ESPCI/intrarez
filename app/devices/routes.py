"""Intranet de la Rez - Devices Pages Routes"""

import datetime
import random

import flask
from flask import g
from flask_babel import _

from app import db, context
from app.devices import bp, forms
from app.models import Device
from app.tools import utils


@bp.route("/register", methods=["GET", "POST"])
@context.all_good_only
def register():
    """Device register page."""
    form = forms.DeviceRegistrationForm()
    if form.validate_on_submit():
        # Check not already registered
        mac_address = form.mac.data.lower()
        if Device.query.filter_by(mac_address=mac_address).first():
            flask.flash(_("Cet appareil est déjà enregistré !"), "danger")
        else:
            now = datetime.datetime.now(datetime.timezone.utc)
            device = Device(
                rezident=g.rezident, name=form.nom.data,
                mac_address=mac_address, type=form.type.data,
                registered=now, last_seen=None,
            )
            db.session.add(device)
            db.session.commit()
            utils.run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Appareil enregistré avec succès !"), "success")
            # OK
            if flask.g.doas or flask.request.args.get("force"):
                return utils.redirect_to_next()
            return utils.safe_redirect("main.connect_check",
                                       **flask.request.args)

    return flask.render_template("devices/register.html",
                                 title=_("Enregistrer l'appareil"),
                                 form=form)


@bp.route("/modify", methods=["GET", "POST"])
@bp.route("/modify/<device_id>", methods=["GET", "POST"])
@context.all_good_only
def modify(device_id=None):
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
        device.name = form.nom.data
        device.type = form.type.data
        mac_address = form.mac.data.lower()
        if device.mac_address != mac_address:
            device.mac_address = mac_address
            utils.run_script("gen_dhcp.py")       # Update DHCP rules
        db.session.commit()
        flask.flash(_("Appareil modifié avec succès !"), "success")
        return utils.redirect_to_next()

    return flask.render_template("devices/modify.html",
                                 title=_("Modifier un appareil"),
                                 device=device, form=form)


@bp.route("/transfer", methods=["GET", "POST"])
@context.all_good_only
def transfer():
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
        else:
            device.rezident = g.rezident
            db.session.commit()
            utils.run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Appareil transféré avec succès !"), "success")
            # OK
            if flask.g.doas or flask.request.args.get("force"):
                return utils.redirect_to_next()
            else:
                return utils.safe_redirect("main.connect_check",
                                           **flask.request.args)

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
def error():
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

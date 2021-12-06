"""Intranet de la Rez - Rooms Pages Routes"""

import datetime

import flask
import flask_login
from flask_babel import _

from app import db
from app.devices import check_device
from app.models import Rezident, Room, Rental
from app.rooms import bp, forms
from app.tools.utils import redirect_to_next, run_script


@bp.before_app_first_request
def create_rez_rooms():
    """Create Rezidence rooms if not already present."""
    if not Room.query.first():
        rooms = Room.create_rez_rooms()
        db.session.add_all(rooms)
        db.session.commit()


@bp.route("/register", methods=["GET", "POST"])
@check_device
def register():
    """Room register page."""
    doas = flask.request.args.get("doas", type=Rezident.query.get)
    if doas and not flask_login.current_user.is_gri:
        # Not authorized to do things as other rezidents!
        flask.abort(403)
    rezident = doas or flask_login.current_user

    room = rezident.current_room
    if room:
        # Already a room: abort
        flask.flash(_("Vous avez déjà une location en cours !"), "warning")
        return redirect_to_next()

    form = forms.RentalRegistrationForm()
    already_rented = None
    if form.validate_on_submit():
        room = Room.query.get(form.room.data)

        def _register_room():
            rental = Rental(rezident=rezident, room=room,
                            start=form.start.data, end=form.end.data)
            db.session.add(rental)
            db.session.commit()
            run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Chambre enregistrée avec succès !"), "success")
            # OK
            return redirect_to_next()

        if not room.current_rental:
            # No problem: register room
            return _register_room()

        if not form.submit.data:
            # The submit button used was not the form one (so it was the
            # warning one): already warned and chose to process, transfer room
            room.current_rental.terminate()
            return _register_room()

        # Else: Do not validate form, but put a warning message
        already_rented = room.num

    return flask.render_template("rooms/register.html", form=form,
                                 title=_("Nouvelle location"), doas=doas,
                                 already_rented=already_rented)


@bp.route("/terminate", methods=["GET", "POST"])
@check_device
def terminate():
    """Room terminate page."""
    doas = flask.request.args.get("doas", type=Rezident.query.get)
    if doas and not flask_login.current_user.is_gri:
        # Not authorized to do things as other rezidents!
        flask.abort(403)
    rezident = doas or flask_login.current_user

    room = rezident.current_room
    if not room:
        # No current rental: go to register
        return flask.redirect(flask.url_for(
            "rooms.register",
            doas=flask.request.args.get("doas"),
            next=flask.request.args.get("next"),
        ))

    form = forms.RentalTransferForm()
    if form.validate_on_submit():
        rental = rezident.current_rental
        rental.end = form.end.data
        db.session.commit()
        # Test if doas => redirect to room register
        return redirect_to_next()

    return flask.render_template("rooms/terminate.html", form=form,
                                 title=_("Changer de chambre"),
                                 doas=doas, room=room.num,
                                 today=datetime.date.today())

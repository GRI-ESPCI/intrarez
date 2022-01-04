"""Intranet de la Rez - Rooms Pages Routes"""

import datetime

import flask
from flask_babel import _

from app import context, db
from app.models import Room, Rental
from app.rooms import bp, email, forms
from app.tools import utils


@bp.before_app_first_request
def create_rez_rooms():
    """Create Rezidence rooms if not already present."""
    if not Room.query.first():
        rooms = Room.create_rez_rooms()
        db.session.add_all(rooms)
        db.session.commit()
        flask.current_app.actions_logger.info(f"Created all rooms")


@bp.route("/register", methods=["GET", "POST"])
@context.all_good_only
def register():
    """Room register page."""
    room = flask.g.rezident.current_room
    if room:
        # Already a room: abort
        flask.flash(_("Vous avez déjà une location en cours !"), "warning")
        return utils.redirect_to_next()

    form = forms.RentalRegistrationForm()
    already_rented = None
    if form.validate_on_submit():
        room = Room.query.get(form.room.data)

        def _register_room():
            start = form.start.data
            end = form.end.data
            rental = Rental(rezident=flask.g.rezident, room=room,
                            start=start, end=end)
            db.session.add(rental)
            db.session.commit()
            flask.current_app.actions_logger.info(
                f"Added {rental} for period {start} – {end}"
            )
            utils.run_script("gen_dhcp.py")       # Update DHCP rules
            flask.flash(_("Chambre enregistrée avec succès !"), "success")
            # OK
            return utils.redirect_to_next()

        if not room.current_rental:
            # No problem: register room
            return _register_room()

        if not form.submit.data:
            # The submit button used was not the form one (so it was the
            # warning one): already warned and chose to process, transfer room
            old_rezident = room.current_rental.rezident
            room.current_rental.end = datetime.date.today()     # = not current
            db.session.commit()
            flask.current_app.actions_logger.warning(
                f"Rented {room}, formerly occupied by {old_rezident}"
            )
            email.send_room_transferred_email(old_rezident)
            return _register_room()

        # Else: Do not validate form, but put a warning message
        already_rented = room.num

    return flask.render_template("rooms/register.html", form=form,
                                 title=_("Nouvelle location"),
                                 already_rented=already_rented)


@bp.route("/modify", methods=["GET", "POST"])
@context.all_good_only
def modify():
    """Rental modification page."""
    form = forms.RentalModificationForm()
    if form.validate_on_submit():
        rental = flask.g.rezident.current_rental
        if rental:
            rental.start = form.start.data
            rental.end = form.end.data
            db.session.commit()
            flask.current_app.actions_logger.info(
                f"Modified {rental}: {form.start.data} – {form.end.data}"
            )
            flask.flash(_("Location modifiée avec succès !"), "success")
        else:
            flask.flash(_("Pas de location en cours !"), "danger")
        return utils.redirect_to_next()

    return flask.render_template("rooms/modify.html",
                                 title=_("Mettre à jour ma location"),
                                 form=form)


@bp.route("/terminate", methods=["GET", "POST"])
@context.all_good_only
def terminate():
    """Room terminate page."""
    room = flask.g.rezident.current_room
    if not room:
        # No current rental: go to register
        return utils.safe_redirect(
            "rooms.register",
            doas=flask.g.doas,
            next=flask.request.args.get("next"),
        )

    form = forms.RentalTransferForm()
    if form.validate_on_submit():
        rental = flask.g.rezident.current_rental
        rental.end = form.end.data
        db.session.commit()
        flask.current_app.actions_logger.info(
            f"Terminated {rental} (end date {form.end.data})"
        )
        return utils.redirect_to_next()

    return flask.render_template("rooms/terminate.html", form=form,
                                 title=_("Changer de chambre"),
                                 room=room.num, today=datetime.date.today())

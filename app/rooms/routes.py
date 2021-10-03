"""Intranet de la Rez - Rooms Pages Routes"""

import datetime

import flask
import flask_login
from flask_babel import _

from app import db
from app.models import User, Room, Rental
from app.rooms import bp, forms
from app.devices import check_device
from app.tools.utils import redirect_to_next


@bp.before_app_first_request
def create_rez_rooms():
    """Create Rezidence rooms if not already present."""
    if not Room.query.first():
        rooms = Room.create_rez_rooms()
        db.session.add_all(rooms)
        db.session.commit()


def register_rental(rental):
    db.session.add(rental)
    db.session.commit()


@bp.route("/register", methods=["GET", "POST"])
@check_device
def register():
    """Room register page."""
    form = forms.RentalRegistrationForm()
    if form.validate_on_submit():
        rental = Rental(
            user=flask_login.current_user,
            room=Room.query.get(form.room.data),
            start=form.start.data, end=form.end.data,
        )
        register_rental(rental)
        flask.flash(_("Chambre enregistrée avec succès !"), "success")
        # OK
        return redirect_to_next()

    return flask.render_template("rooms/register.html", form=form,
                                 title=_("Nouvelle location"))

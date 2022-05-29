"""IntraRez - Mise à jour de l'état des abonnements

Pour tous les Rezidents, vérifie que leur état actuel (abonné, mois offert,
paiement nécessaire) correspond bien à leurs abonnements en cours.

Conçu pour être appelé tous les jours à minuit. Envoie également un mail
au Rezident l'informant du changement d'état.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/intrarez/intrarez; ./env/bin/flask script update_sub_states.py

12/2021 Loïc 137
"""

import datetime
import sys

import flask_babel
from flask_babel import _

try:
    from app import db
    from app.models import Rezident, Ban, SubState
    from app.routes.payments import email
    from app.utils import helpers
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/intrarez/intrarez; "
        "    ./env/bin/flask script update_sub_states.py\n"
    )
    sys.exit(1)


def main() -> None:
    rezidents = Rezident.query.all()
    in_a_week = datetime.date.today() + datetime.timedelta(days=7)

    for rezident in rezidents:
        print(f"{rezident.full_name} : ", end="")

        sub_state = rezident.compute_sub_state()
        if rezident.sub_state == sub_state:
            if (
                sub_state == SubState.trial
                and rezident.current_subscription
                and rezident.current_subscription.cut_day == in_a_week
                and rezident.has_a_room
            ):
                # Coupure dans une semaine : mail de rappel
                print("coupure dans une semaine, rappel")
                email.send_reminder_email(rezident)
            else:
                # État à jour
                print(f"à jour ({rezident.sub_state.name})")
        else:
            # État pas à jour : changer et envoyer un mail
            print(f"{rezident.sub_state.name} -> {sub_state}")

            if sub_state == SubState.outlaw:
                # Expiration mois gratuit : BANNEZ-MOI ÇA LES MODOS
                with flask_babel.force_locale(rezident.locale or "en"):
                    ban = Ban(
                        rezident=rezident,
                        start=datetime.datetime.now(datetime.timezone.utc),
                        end=None,
                        reason=_("Pas d'abonnement actif"),
                        message=_(
                            "Afin de retrouver l'accès à Internet, "
                            "connectez-vous à votre compte et prenez "
                            "un abonnement à Internet."
                        ),
                    )
                    db.session.add(ban)
                    helpers.log_action(
                        f"Subscription of {rezident} expired, added {ban}"
                    )
                    db.session.commit()

            rezident.sub_state = sub_state
            db.session.commit()  # On commit à chaque fois, au cas où
            helpers.log_action(f"Sub state of {rezident} changed to {sub_state}")
            if rezident.has_a_room:
                email.send_state_change_email(rezident, rezident.sub_state)

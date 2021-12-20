"""IntraRez - Mise à jour de l'état des abonnements

Pour tous les Rezidents, vérifie que leur état actuel (abonné, mois offert,
paiement nécessaire) correspond bien à leurs abonnements en cours.

Conçu pour être appelé tous les jours à minuit. Envoie également un mail
au Rezident l'informant du changement d'état.

Ce script peut uniquement être appelé depuis Flask :
/home/intrarez/intrarez/env/bin/flask script update_sub_states.py

12/2021 Loïc 137
"""

import sys

try:
    from app import db
    from app.models import Rezident
    from app.payments import email
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "/home/intrarez/intrarez/env/bin/flask script update_sub_states.py\n"
    )
    sys.exit(1)


def main():
    rezidents = Rezident.query.all()

    for rezident in rezidents:
        if rezident.sub_state != rezident.computed_sub_state:
            # État pas à jour
            rezident.sub_state = rezident.computed_sub_state
            email.send_state_change_email(rezident, rezident.sub_state)

    db.session.commit()

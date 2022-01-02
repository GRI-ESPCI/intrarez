"""IntraRez - Mise en place des paiements

Pour tous les Rezidents qui ont enregistré un appareil mais qui n'ont pas
d'abonnement :
  * Crée le premier abonnement
  * Envoie un mail d'information d'expiration dans un mois

Ce script ne fait a priori rien passé le premier appel (étant donné que
l'enregistrement du premier appareil déclenche le premier abonnement).

Il sera probablement détruit lors d'une prochaine mise à jour.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/intrarez/intrarez; " ./env/bin/flask script setup_payments.py

12/2021 Loïc 137
"""

import sys

import flask
import flask_babel
from flask_babel import _

try:
    from app import db
    from app.email import send_email
    from app.models import Rezident
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/intrarez/intrarez; "
        "    ./env/bin/flask script setup_payments.py\n"
    )
    sys.exit(1)


def send_on_setup_email(rezident):
    with flask_babel.force_locale(rezident.locale or "fr"):
        # Render mail content, in rezident language
        subject = _("IMPORTANT - Paiement d'Internet")
        html_body = flask.render_template(
            f"payments/mails/on_setup.html",
            rezident=rezident,
            sub=rezident.current_subscription,
        )

    # Send email
    send_email(
        f"payments/on_setup",
        subject=f"[IntraRez] {subject}",
        recipients={rezident.email: rezident.full_name},
        html_body=html_body,
    )


def main():
    rezidents = Rezident.query.all()
    n_rez = len(rezidents)

    for i_rez, rezident in enumerate(rezidents):
        print(f"[{i_rez + 1}/{n_rez}] {rezident.full_name} : ", end="")
        sys.stdout.flush()

        if not rezident.devices:
            print("Pas d'appareils, skip")
            continue
        if rezident.subscriptions:
            print("Déjà un abonnement, skip")
            continue

        # Un appareil mais pas d'abonnement : c tipar
        print(f"Ajout de l'abonnement... ", end="")
        sys.stdout.flush()
        rezident.add_first_subscription()
        db.session.commit()     # On commit à chaque fois, au cas où ça crash
        print(f"Envoi du mail... ", end="")
        sys.stdout.flush()
        send_on_setup_email(rezident)
        print(f"Fait !")

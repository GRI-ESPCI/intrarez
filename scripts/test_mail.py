"""IntraRez - Envoi d'un mail d'expiration d'abonnement à l'utilisateur actuel

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/intrarez/intrarez; " ./env/bin/flask script update_sub_states.py

12/2021 Loïc 137
"""

import sys
import tempfile
import webbrowser

import flask
import flask_babel

try:
    from app.enums import SubState
    from app.models import Rezident
    from app.payments import email
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/intrarez/intrarez; "
        "    ./env/bin/flask script update_sub_states.py\n"
    )
    sys.exit(1)


def main():
    for rezident in Rezident.query.all():
        if not rezident.current_subscription:
            continue

        body = email.send_state_change_email(rezident, SubState.trial)

        with tempfile.NamedTemporaryFile("w+", suffix=".html") as fp:
            fp.write(body)
            webbrowser.open(f"file:///{fp.name}")

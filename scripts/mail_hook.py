"""IntraRez - Transfert des mails reçus vers Discord

Récupère et analyse le mail reçu, en fait un Embed Discord
et l'envoie via un webhook (variable d'environnement MAIL_WEBHOOK).

Conçu pour être appelé comme commande dans `/etc/aliases`:
http://www.postfix.org/aliases.5.html.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/intrarez/intrarez; " ./env/bin/flask script mail_hook.py

Cependant, cela ne servirait à rien de l'appeler autrement que via
`/etc/aliases`, vu que le script attend le contenu du mail dans stdin.

12/2021 Loïc 137
"""

import email
import email.policy
import email.utils
import time
import sys

import flask
from discord_webhook import DiscordEmbed, DiscordWebhook

try:
    from app.models import Rezident
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/intrarez/intrarez; "
        "    ./env/bin/flask script update_sub_states.py\n"
    )
    sys.exit(1)


def report_mail() -> None:
    """"Get mail, process it into an Embed and send it to Discord."""
    # Parse email contents from stdin
    mail = email.message_from_file(sys.stdin, policy=email.policy.default)
    if not mail:
        # Not a real mail (no headers)
        print("Pas de mail dans l'entrée standard (normal si exécution "
              "manuelle, ce script n'est pas fait pour ça).")
        return

    # Extract email parts
    sender = mail.get("From", "<no sender>")
    print(f"Mail de {sender} réceptionné...")
    subject = mail.get("Subject", "<no subject>")
    recipient = mail.get("To", "<no recipient>")
    raw_timestamp = email.utils.parsedate(mail.get("Date"))
    if raw_timestamp:
        timestamp = time.mktime(raw_timestamp)
    else:
        timestamp = None

    body = mail.get_body("text/plain") or mail.get_body()
    content = body.get_content() if body else "<no content>"

    # Build embed
    embed = DiscordEmbed(title=subject, description=content[:2000],
                         color="64b9e9")
    embed.set_author(name=sender)
    embed.set_footer(text=f"Mail à {recipient}")
    embed.set_timestamp(timestamp)

    # Get matching Rezident and complete Embed
    sender_name, sender_address = email.utils.parseaddr(sender)
    if "@" in sender_address:
        rezident = Rezident.query.filter_by(email=sender_address).first()
        if rezident:
            embed.add_embed_field(
                name="Rezident correspondant :",
                value=rezident.full_name,
            )
            embed.add_embed_field(
                name="Profil (compte GRI nécessaire) :",
                value=flask.url_for("profile.main", doas=rezident.id),
            )

    # Send webhook
    url = flask.current_app.config["MAIL_WEBHOOK"]
    role_id = flask.current_app.config["GRI_ROLE_ID"]
    webhook = DiscordWebhook(url,  content=f"<@&{role_id}> Nouveau mail !")
    webhook.add_embed(embed)
    response = webhook.execute()

    if not response:
        raise RuntimeError(
            f"Discord API responded with {response.code}: {response.text}"
        )

    print(f"Mail de {sender} transmis.")


def main() -> None:
    try:
        report_mail()
    except Exception:
        raise RuntimeError("Sorry, your mail could not reach our team. "
                           "Please use our individual contacts at "
                           f"{flask.url_for('main.contact', _external=True)}.")

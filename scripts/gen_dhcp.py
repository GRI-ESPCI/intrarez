"""IntraRez - Génération des tables DHCP

Pour toutes les chambres, attribue une adresse IP aux appareils de
l'occupant actuel. L'attribution d'IP elle-même (y compris en cas de
bannissement est gérée par `Device.allocate_ip_for`).

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/intrarez/intrarez; ./env/bin/flask script gen_dhcp.py

10/2021 Loïc 137
"""

import os
import sys

import flask

try:
    from app.models import Room
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/intrarez/intrarez; "
        "    ./env/bin/flask script gen_dhcp.py\n"
    )
    sys.exit(1)


def main() -> None:
    rules = ""

    rooms = Room.query.order_by(Room.num).all()
    for room in rooms:
        if not room.current_rental:
            print(f"Chambre {room.num} non occupée, on passe")
            continue

        rezident = room.current_rental.rezident
        print(f"Chambre {room.num} occupée par {rezident.full_name}")
        if rezident.is_banned:
            print(f"    -- BANNI : {rezident.current_ban} --")

        for device in rezident.devices:
            ip = device.allocate_ip_for(room)
            print(f"    Appareil #{device.id} : {device.mac_address} -> {ip}")
            rules += (
                f"host {rezident.username}-{room.num}-{device.id} {{\n"
                f"\thardware ethernet {device.mac_address};\n"
                f"\tfixed-address {ip};\n"
                "}\n"
            )

    # Écriture dans le fichier
    file = os.getenv("DHCP_HOSTS_FILE") or ""
    if not os.path.isfile(file):
        raise FileNotFoundError(
            f"Le ficher d'hôtes DHCP '{file}' n'existe "
            "pas (variable d'environment DHCP_HOSTS_FILE)"
        )

    with open(file, "w") as fp:
        fp.write(
            "# Ce fichier est généré automatiquement par gen_dhcp.py\n"
            f"# ({__file__}).\n"
            "# Ne PAS le modifier à la main, ce serait écrasé !\n#\n"
            "#   * Pour ajouter un appareil à un Rezident,\n"
            "#       - utiliser l'interface en ligne \n"
            f"#         ({flask.url_for('gris.rezidents')})\n"
            "#       - OU utiliser `flask shell` pour l'ajouter en base,\n"
            "#         puis régénérer avec `flask script gen_dhcp.py`\n"
            "#         (flask = /home/intrarez/intrarez/env/bin/flask)\n#\n"
            "#   * Pour ajouter toute autre règle, modifier directement\n"
            "#     /env/dhcp/dhcpd.conv\n#\n"
        )
        fp.write(rules)

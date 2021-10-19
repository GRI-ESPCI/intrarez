"""IntraRez - Génération des tables DHCP

Pour toutes les chambres, attribue une adresse IP aux appareils de
l'occupant actuel.

Ce script peut uniquement être appelé depuis Flask :
/home/intrarez/intrarez/env/bin/flask script gen_dhcp.py

10/2021 Loïc 137
"""

import os
import sys

try:
    from app.models import Room
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "/home/intrarez/intrarez/env/bin/flask script gen_dhcp.py\n"
    )
    sys.exit(1)


rules = ""

rooms = Room.query.all()
for room in rooms:
    if not room.current_rental:
        print(f"Chambre {room.num} non occupée, on passe")
        continue

    rezident = room.current_rental.rezident
    print(f"Chambre {room.num} occupée par {rezident.full_name}")

    for i_dev, device in enumerate(rezident.devices):
        ip = f"10.{i_dev}.{room.base_ip}"
        print(f"    Appareil #{device.id} : {device.mac_address} -> {ip}")
        rules += (
            f"host {rezident.username}-{room.num}-{i_dev} {{\n"
            f"\thardware ethernet {device.mac_address};\n"
            f"\tfixed-address {ip};\n"
            "}\n"
        )

# Écriture dans le fichier
file = os.getenv("DHCP_HOSTS_FILE")
if not os.path.isfile(file):
    raise FileNotFoundError(f"Le ficher d'hôtes DHCP '{file}' n'existe pas "
                            "(variable d'environment DHCP_HOSTS_FILE)")

with open(file, "w") as fp:
    fp.write(
        "# Ce fichier est généré automatiquement par gen_dhcp.py\n"
        f"# ({__file__}).\n"
        "# Ne PAS le modifier à la main, ce serait écrasé !\n#\n"
        "#   * Pour ajouter un appareil à un Rezident,\n"
        "#       - utiliser l'interface en ligne\n"
        "#       - OU utiliser `flask shell` pour ajouter l'entrée en base,\n"
        "#         puis regénérer le fichier avec `flask script gen_dhcp.py`\n"
        "#         (flask = /home/intrarez/intrarez/env/bin/flask)\n#\n"
        "#   * Pour ajouter toute autre règle, modifier directement\n"
        "#     /env/dhcp/dhcpd.conv\n#\n"
    )
    fp.write(rules)

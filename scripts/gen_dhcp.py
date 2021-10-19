"""IntraRez - Génération des tables DHCP

Pour toutes les chambres, attribue une adresse IP aux appareils de
l'occupant actuel.

Ce script peut uniquement être appelé depuis Flask :
    cd /home/intrarez/intrarez
    source env/bin/activate
    flask script gen_dhcp.py

10/2021 Loïc 137
"""

import sys

try:
    from app.models import Room
except ImportError:
    sys.stderr.write("""--- ERREUR ---
Ce script peut uniquement être appelé depuis Flask :
    cd /home/intrarez/intrarez
    source env/bin/activate
    flask script gen_dhcp.py
""")
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
with open("../watched/dhcp_hosts", "w") as fp:
    fp.write(rules)

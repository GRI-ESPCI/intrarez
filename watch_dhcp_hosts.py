"""IntraRez - Mise à jour des règles DHCP

Ce script est lancé en root au démarrage du système par une tâche supervisor
(voir .conf_models/supervisor.conf).

Il surveille le fichier contenant les règles DHCP (variable d'environment
DHCP_HOSTS_FILE, voir .env) et relance le serveur DHCP dès qu'il est modifié.
"""

import logging
import os
import subprocess
import time

from dotenv import load_dotenv
import pyinotify


logging.basicConfig(level=logging.DEBUG, style="{",
                    format="{asctime} {levelname}:{name}:{message}")
load_dotenv()
file = os.getenv("DHCP_HOSTS_FILE")
if not file or not os.path.isfile(file):
    raise FileNotFoundError(f"Le ficher à surveiller '{file}' n'existe pas "
                            "(variable d'environment DHCP_HOSTS_FILE)")

last_event = time.time()


def restart_dhpc_server(_event) -> None:
    # Fonction appelée à chaque modification détectée
    global last_event
    now = time.time()
    if now - last_event < 1:
        # Ignorer les doubles appels (trop rapprochés)
        return
    last_event = now
    logging.info("File modification detected, restarting DHCP server...")
    try:
        retcode = subprocess.call(["systemctl", "restart", "isc-dhcp-server"])
        if retcode < 0:
            logging.error(f"ERROR - Restart terminated by signal {-retcode}")
        elif retcode == 0:
            logging.info("DHCP server restarted!")
        else:
            logging.error(f"ERROR - Restart order returned {retcode}")
    except OSError as exc:
        logging.error(f"ERROR - Restart order execution failed: {exc}")


wm = pyinotify.WatchManager()
wm.add_watch(file, pyinotify.IN_MODIFY, restart_dhpc_server)
logging.info(f"Started watching {file}...")
pyinotify.Notifier(wm).loop()
logging.info(f"Sopped watching {file}.")

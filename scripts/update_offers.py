"""IntraRez - Création / mise à jour des offres

Ce script permet de remplir / modifier la table :class:`.models.Offer`,
sans aller directement les ajouter en ``flask shell`` et en les intégrant
au VCS.

Crée les offres dont le ``slug`` n'existe pas déjà, met à jour les autres.

Ce script EMPÊCHE AUSSI LA MODIFICATION DE LA DURÉE OU DU PRIX d'une offre
existante (cela créerait des incohérences avec les abonnements déjà pris) :
pour modifier l'un ou l'autre, marquer l'offre existante comme non visible
et non active et ajouter une nouvelle offre.

Une offre supprimée de la liste NE SERA PAS SUPPRIMÉE (cela est impossible
si des abonnements ont déjà été pris) : il faut la passer en non active et/ou
non visible.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/intrarez/intrarez; ./env/bin/flask script update_offers.py

12/2021 Loïc 137
"""

import sys

try:
    from app import db, __version__
    from app.models import Offer
    from app.tools import utils, typing
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/intrarez/intrarez; "
        "    ./env/bin/flask script update_offers.py\n"
    )
    sys.exit(1)


def offers() -> dict[str, dict[str, typing.Any]]:
    """Offres à définir. Modifier cette fonction pour modifier les offres.

    L'argument `active` signifie que l'offre peut être utilisée pour créer
        de nouveaux abonnements.
    L'argument `visible` signifie que l'offre apparaît dans la liste des
        offres et peut être choisie par un Rezident.
    """
    return {

        "_first": dict(
            name_fr="Offre de bienvenue",
            name_en="Welcoming offer",
            description_fr="Un mois d'accès à Internet offert à votre "
                           "première connexion !",
            description_en="One month of free Internet access  when you "
                           "connect for the first time!",
            price=0.0,
            months=0,
            days=0,
            active=True,    # NE PAS CHANGER (offre ajoutée automatiquement)
            visible=False,
        ),

        "3months": dict(
            name_fr="3 mois",
            name_en="3 months",
            description_fr="2 mois d'abonnement à Internet, puis 1 mois "
                           "offert pendant lequel un nouvel abonnement peut "
                           "être pris.",
            description_en="2 months of Internet access, then 1 extra month "
                           "during which a new subscription can be taken.",
            price=4.0,
            months=2,
            days=0,
            active=True,
            visible=True,
        ),

        "6months": dict(
            name_fr="6 mois",
            name_en="6 months",
            description_fr="5 mois d'abonnement à Internet, puis 1 mois "
                           "offert pendant lequel un nouvel abonnement peut "
                           "être pris.",
            description_en="5 months of Internet access, then 1 extra month "
                           "during which a new subscription can be taken.",
            price=8.0,
            months=5,
            days=0,
            active=True,
            visible=True,
        ),

        "12months": dict(
            name_fr="12 mois",
            name_en="12 months",
            description_fr="11 mois d'abonnement à Internet, puis 1 mois "
                           "offert pendant lequel un nouvel abonnement peut "
                           "être pris.",
            description_en="11 months of Internet access, then 1 extra month "
                           "during which a new subscription can be taken.",
            price=15.0,
            months=11,
            days=0,
            active=True,
            visible=True,
        ),

    }


def main():
    for slug, offer_dict in offers().items():
        offer = Offer.query.get(slug)
        if offer:
            # Offer modification
            print(f"Mise à jour de {offer}...")
            if (offer.price != offer_dict["price"]
                or offer.months != offer_dict["months"]
                or offer.days != offer_dict["days"]):
                # Cannot modify price/delay
                db.session.rollback()
                raise ValueError(
                    f"Offre {offer} : tentative de modification du prix "
                    f"({offer.price} €) et/ou du délai ({offer.months} mois "
                    f"et {offer.days} jours).\n\nCela est impossible (risque "
                    "d'incohérences avec les abonnements déjà pris) :\n"
                    "il faut marquer l'offre existante comme non visible et "
                    "non active et ajouter une nouvelle offre.\n\n"
                    "Aucune modification n'a été effectuée."
                )
            for col, val in offer_dict.items():
                setattr(offer, col, val)

        else:
            # Offer creation
            print(f"Ajout de l'offre '{slug}'...")
            offer = Offer(slug=slug, **offer_dict)
            db.session.add(offer)

    db.session.commit()
    utils.log_action(
        f"Updated offers to those in 'update_offers.py' in v{__version__}"
    )
    print("Modifications effectuées.")

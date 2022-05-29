"""Intranet de la Rez - Authentication Utils"""

import re

import unidecode

from app.models import Rezident


def new_username(prenom: str, nom: str) -> str:
    """Create a new rezident unique username from a forname and a name.

    Args:
        prenom: The rezident's forname.
        nom: The rezident's last name.

    Returns:
        The first non-existing corresponding username.
    """
    pnom = prenom.lower()[0] + nom.lower()[:7]
    # Exclude non-alphanumerics characters
    base_username = re.sub(r"\W", "", unidecode.unidecode(pnom), re.A)
    # Construct first non-existing username
    username = base_username
    discr = 1
    while Rezident.query.filter_by(username=username).first():
        username = f"{base_username}{discr}"
        discr += 1
    return username

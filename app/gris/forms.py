"""Intranet de la Rez - Main Pages Forms"""

import os

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.tools.validators import DataRequired


def scripts_list() -> list[tuple[str, str]]:
    """Build the list of existing scripts in app/scripts.

    Returns:
        ``list((value, label))`` options for :class:`wtforms.SelectField`.
    """
    scripts = []
    for file in os.scandir("scripts"):
        if not file.is_file():
            continue
        name, ext = os.path.splitext(file.name)
        if ext != ".py":
            continue

        with open(file, "r") as fp:
            first_line = fp.readline()
        doc = first_line.lstrip("'\"")

        scripts.append((name, f"{name} — {doc}"))

    return scripts


class ChoseScriptForm(FlaskForm):
    """WTForm used to chose a script to execute."""
    script = wtforms.SelectField(_l("Script"), choices=scripts_list(),
                                 validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Exécuter"))

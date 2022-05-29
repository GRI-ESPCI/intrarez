"""Intranet de la Rez - Main Pages Forms"""

import datetime
import os

from dateutil import relativedelta
import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.utils.validators import (
    DataRequired,
    Optional,
    Length,
    ValidRezidentID,
    ValidBanID,
)


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

    script = wtforms.SelectField(
        _l("Script"), choices=scripts_list(), validators=[DataRequired()]
    )
    submit = wtforms.SubmitField(_l("Exécuter"))


class BanForm(FlaskForm):
    """WTForm used to ban someone."""

    rezident = wtforms.HiddenField("", validators=[DataRequired(), ValidRezidentID()])
    ban_id = wtforms.HiddenField("", validators=[Optional(), ValidBanID()])
    infinite = wtforms.BooleanField(_l("Illimité"), default=True)
    hours = html5.IntegerField(_l("Heures"), validators=[Optional()])
    days = html5.IntegerField(_l("Jours"), validators=[Optional()])
    months = html5.IntegerField(_l("Mois"), validators=[Optional()])
    reason = wtforms.TextField(
        _l("Motif court"), validators=[DataRequired(), Length(max=32)]
    )
    message = wtforms.TextAreaField(
        _l("Message détaillé"), validators=[Optional(), Length(max=2000)]
    )
    submit = wtforms.SubmitField(_l("Bannez-moi ça les modos || Mettre à jour le ban"))
    unban = wtforms.SubmitField(_l("Mettre fin au ban"))

    def get_end(self, start: datetime.datetime) -> datetime.datetime | None:
        """Get the end datetime of the ban from form data.

        Args:
            start (datetime.datetime): The beginning of the ban.

        Returns:
            The end of the ban, or ``None`` if infinite.
        """
        if self.infinite.data:
            return None
        else:
            return start + relativedelta.relativedelta(
                hours=int(self.hours.data or 0),
                days=int(self.days.data or 0),
                months=int(self.months.data or 0),
            )

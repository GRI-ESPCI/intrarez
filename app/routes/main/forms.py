"""Intranet de la Rez - Main Pages Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from discord_webhook import DiscordEmbed

from app.utils.validators import DataRequired, Optional, Email, ValidRoom


class ContactForm(FlaskForm):
    """WTForm used to send a contact request to Discord."""

    name = wtforms.StringField(_l("Nom"), validators=[DataRequired()])
    email = html5.EmailField(
        _l("Adresse e-mail (optionnel)"), validators=[Optional(), Email()]
    )
    room = html5.IntegerField(
        _l("Chambre (optionnel)"), validators=[Optional(), ValidRoom()]
    )
    title = wtforms.StringField(_l("Titre"), validators=[DataRequired()])
    message = wtforms.TextAreaField(_l("Message"), validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Envoyer"))

    def create_embed(self) -> DiscordEmbed:
        """Create a Discord embed describing the contact request."""
        embed = DiscordEmbed(
            title=self.title.data, description=self.message.data, color="64b9e9"
        )
        embed.set_author(name=self.name.data)
        embed.set_footer(text="Formulaire de contact IntraRez")
        embed.add_embed_field(
            name="E-mail :", value=self.email.data or "*Non renseigné*"
        )
        embed.add_embed_field(
            name="Chambre :", value=self.room.data or "*Non renseignée*"
        )
        embed.set_timestamp()
        return embed

"""Intranet de la Rez - Main Pages Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from discord_webhook import DiscordEmbed

from app.tools.validators import DataRequired, Optional, Email, ValidRoom


class EmptyForm(FlaskForm):
    """WTForm used to absolutely nothing."""
    submit = wtforms.SubmitField(_l("Envoyer"))


class ContactForm(FlaskForm):
    """WTForm used to send a contact request to Discord."""
    name = wtforms.StringField(_l("Nom"), validators=[DataRequired()])
    email = wtforms.StringField(_l("Adresse e-mail (optionnel)"),
                                validators=[Optional(), Email()])
    room = wtforms.IntegerField(_l("Chambre (optionnel)"),
                                validators=[Optional(), ValidRoom()])
    title = wtforms.StringField(_l("Titre"), validators=[DataRequired()])
    message = wtforms.TextAreaField(_l("Message"), validators=[DataRequired()])
    submit = wtforms.SubmitField(_l("Envoyer"))

    def create_embed(self):
        """Create a Discord embed describing the contact request.

        Returns:
            :class:`discord_webhook.DiscordEmbed`
        """
        embed = DiscordEmbed(title=self.title.data,
                             description=self.message.data,
                             color="64b9e9")
        embed.set_author(name=self.name.data)
        embed.set_footer(text="Formulaire de contact IntraRez")
        embed.add_embed_field(name="E-mail :",
                              value=self.email.data or "*Non renseigné*")
        embed.add_embed_field(name="Chambre :",
                              value=self.room.data or "*Non renseignée*")
        embed.set_timestamp()
        return embed

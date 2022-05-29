"""Intranet de la Rez - Authentication Forms"""

import wtforms
from wtforms.fields import html5
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.tools.validators import DataRequired, Email, EqualTo, Length, NewEmail
from app.tools import utils


class LoginForm(FlaskForm):
    """WTForm used to log users in."""

    login = wtforms.StringField(
        _l("Nom d'utilisateur / Adresse e-mail"), validators=[DataRequired()]
    )
    password = wtforms.PasswordField(_l("Mot de passe"), validators=[DataRequired()])
    remember_me = wtforms.BooleanField(_l("Rester connecté"))
    submit = wtforms.SubmitField(_l("Connexion"))


class RegistrationForm(FlaskForm):
    """WTForm used to register users."""

    nom = wtforms.StringField(_l("Nom"), validators=[DataRequired(), Length(max=64)])
    prenom = wtforms.StringField(
        _l("Prénom"), validators=[DataRequired(), Length(max=64)]
    )
    promo = wtforms.SelectField(
        _l("Promotion"), choices=utils.promotions().items(), validators=[DataRequired()]
    )
    email = html5.EmailField(
        _l("Adresse e-mail"),
        validators=[DataRequired(), Length(max=120), Email(), NewEmail()],
    )
    password = wtforms.PasswordField(_l("Mot de passe"), validators=[DataRequired()])
    password2 = wtforms.PasswordField(
        _l("Mot de passe (validation)"),
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = wtforms.SubmitField(_l("Créer mon compte"))


class ResetPasswordRequestForm(FlaskForm):
    """WTForm used to request a user password request."""

    email = html5.EmailField(_l("Adresse e-mail"), validators=[DataRequired(), Email()])
    submit = wtforms.SubmitField(_l("Envoyer le mail de réinitialisation"))


class ResetPasswordForm(FlaskForm):
    """WTForm used to reset a user password."""

    password = wtforms.PasswordField(
        _l("Nouveau mot de passe"), validators=[DataRequired()]
    )
    password2 = wtforms.PasswordField(
        _l("Nouveau mot de passe (validation)"),
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = wtforms.SubmitField(_l("Valider"))

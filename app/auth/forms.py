"""Intranet de la Rez - Authentication Forms"""

import wtforms
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

from app.models import User
from app._tools.validators import (DataRequired, Email, EqualTo,
                                   NewUsername, NewEmail)



class LoginForm(FlaskForm):
    """WTForm used to log users in."""
    username = wtforms.StringField(_l("Nom"), validators=[DataRequired()])
    password = wtforms.PasswordField(_l("Mot de passe"),
                                     validators=[DataRequired()])
    remember_me = wtforms.BooleanField(_l("Rester connecté"))
    submit = wtforms.SubmitField(_l("Connexion"))


class RegistrationForm(FlaskForm):
    """WTForm used to register users."""
    username = wtforms.StringField(_l("Nom"), validators=[DataRequired(),
                                                          NewUsername()])
    email = wtforms.StringField(_l("Adresse e-mail"),
                                validators=[DataRequired(), Email(),
                                            NewEmail()])
    password = wtforms.PasswordField(_l("Mot de passe"),
                                     validators=[DataRequired()])
    password2 = wtforms.PasswordField(_l("Mot de passe (validation)"),
                                      validators=[DataRequired(),
                                                  EqualTo("password")])
    submit = wtforms.SubmitField(_l("Envoyer"))


class ResetPasswordRequestForm(FlaskForm):
    """WTForm used to request a user password request."""
    email = wtforms.StringField(_l("Adresse e-mail"), validators=[DataRequired(),
                                                              Email()])
    submit = wtforms.SubmitField(_l("Envoyer le mail de réinitialisation"))


class ResetPasswordForm(FlaskForm):
    """WTForm used to reset a user password."""
    password = wtforms.PasswordField(_l("Nouveau mot de passe"),
                                     validators=[DataRequired()])
    password2 = wtforms.PasswordField(_l("Nouveau mot de passe (validation)"),
                                      validators=[DataRequired(),
                                                  EqualTo("password")])
    submit = wtforms.SubmitField(_l("Valider"))

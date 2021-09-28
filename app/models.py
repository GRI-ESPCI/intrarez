"""Intranet de la Rez Flask App - Database Models"""

import time

import jwt
import flask
import flask_login
from werkzeug import security as wzs

from app import db, login


class User(flask_login.UserMixin, db.Model):
    """A Rezident.

    :class:`flask_login.UserMixin` adds the following properties and methods:
        * is_authenticated: a property that is True if the user has
            valid credentials or False otherwise.
        * is_active: a property that is True if the user's account is
            active or False otherwise.
        * is_anonymous: a property that is False for regular users, and
            True for a special, anonymous user.
        * get_id(): a method that returns a unique identifier for the
            user as a string.
    """
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(64), unique=True)
    nom = db.Column(db.String(64))
    prenom = db.Column(db.String(64))
    promo = db.Column(db.String(8))
    email = db.Column(db.String(120), unique=True)
    is_gri = db.Column(db.Boolean(), nullable=False, default=False)
    _password_hash = db.Column(db.String(128))

    devices = db.relationship("Device", back_populates="user")

    def __repr__(self):
        """Returns repr(self)."""
        return f"<User '{self.username}'>"

    def set_password(self, password):
        """Save or modify user password.

        Relies on :func:`werkzeug.security.generate_password_hash` to
        store a password hash only.

        Args:
            password (str): The password to store. Not stored.
        """
        self._password_hash = wzs.generate_password_hash(password)

    def check_password(self, password):
        """Check that a given password matches stored user password.

        Relies on :func:`werkzeug.security.check_password_hash` to
        compare tested password with stored password hash.

        Args:
            password (str): The password to check. Not stored.

        Returns:
            Whether the password is correct (bool).
        """
        return wzs.check_password_hash(self._password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        """Forge a JWT reset password token for the user.

        Relies on :func:`jwt.encode`.

        Args:
            expires_in (int): The time before the token expires, in seconds.

        Returns:
            The created JWT token (str).
        """
        return jwt.encode(
            {"reset_password": self.id, "exp": time.time() + expires_in},
            flask.current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

    @classmethod
    def verify_reset_password_token(cls, token):
        """Verify a user password reset token (class method).

        Relies on :func:`jwt.decode`.

        Args:
            token (str): The JWT token to decode.

        Returns:
            The user to reset password of if the token is valid and the
            user exists, else ``None``.
        """
        try:
            id = jwt.decode(token, flask.current_app.config["SECRET_KEY"],
                            algorithms=["HS256"])["reset_password"]
        except Exception:
            return
        return cls.query.get(id)


class Device(db.Model):
    """A device of a Rezident."""
    id = db.Column(db.Integer(), primary_key=True)
    _user_id = db.Column(db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="devices")
    name = db.Column(db.String(64))
    mac_address = db.Column(db.String(17), nullable=False, unique=True)
    type = db.Column(db.String(64))
    registered = db.Column(db.DateTime(), nullable=False)
    last_seen = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        """Returns repr(self)."""
        return f"<Device '{self.name}' of {self.user} ({self.mac_address})>"


@login.user_loader
def load_user(id):
    """Function used by Flask-login to get the connected user.

    Args:
        id (str): the ID of the connected user (stored in the session).

    Returns:
        :class:`User`
    """
    return User.query.get(int(id))

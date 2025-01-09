from app.models.db import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_role = db.Column(db.String(255), nullable=False)
    fingerprint = db.Column(db.String(255), unique=True, nullable=False)

    def __init__(self, username, password, user_role, fingerprint):
        self.username = username
        self.password = generate_password_hash(password)
        self.user_role = user_role
        self.fingerprint = fingerprint

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'user_role': self.user_role,
            'fingerprint': self.fingerprint
        }

def is_fingerprint_registered(fingerprint):
    return User.query.filter_by(fingerprint=fingerprint).first() is not None

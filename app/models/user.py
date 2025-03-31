from app import db
from datetime import datetime
import hashlib
import base64
import os

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    salt = db.Column(db.String(64), nullable=False)  # Add salt column
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    food_entries = db.relationship('FoodEntry', backref='user', lazy=True)

    def set_password(self, password):
        # Generate a random salt
        salt = os.urandom(32)
        # Hash password with salt using SHA256
        hash_obj = hashlib.sha256()
        hash_obj.update(salt + password.encode('utf-8'))
        self.password_hash = base64.b64encode(hash_obj.digest()).decode('utf-8')
        self.salt = base64.b64encode(salt).decode('utf-8')

    def check_password(self, password):
        # Get salt from stored value
        salt = base64.b64decode(self.salt.encode('utf-8'))
        # Hash the provided password with stored salt
        hash_obj = hashlib.sha256()
        hash_obj.update(salt + password.encode('utf-8'))
        password_hash = base64.b64encode(hash_obj.digest()).decode('utf-8')
        return self.password_hash == password_hash

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        } 
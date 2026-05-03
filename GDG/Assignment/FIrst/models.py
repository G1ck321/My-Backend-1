from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # username must be unique
    username = db.Column(db.String(80), unique=True, nullable=False)

    # store hashed password, not plain text
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        # convert plain password into a hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # compare entered password with stored hash
        return check_password_hash(self.password_hash, password)
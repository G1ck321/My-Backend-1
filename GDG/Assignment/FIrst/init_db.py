#!/usr/bin/env python
"""
Initialize the database with a test user.
Run this once to set up the database before running the app.
"""

from config import app
from models import db, User

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if admin user already exists
        admin = User.query.filter_by(username="admin").first()
        if admin:
            print("✓ Admin user already exists")
            return
        
        # Create admin user with password "secret"
        admin_user = User(username="admin")
        admin_user.set_password("secret")
        db.session.add(admin_user)
        db.session.commit()
        print("✓ Admin user created (username: admin, password: secret)")

if __name__ == "__main__":
    init_database()

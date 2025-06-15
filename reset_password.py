#!/usr/bin/env python3
"""
Password reset utility for PipSqueak
"""
import os
import sys
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def reset_user_password(email, new_password):
    """Reset password for a specific user"""
    with app.app_context():
        user = User.query.filter_by(email=email.lower()).first()
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            return True
        return False

if __name__ == "__main__":
    email = "shaunbinner@gmail.com"
    temp_password = "TempPass123!"
    
    if reset_user_password(email, temp_password):
        print(f"Password reset successful for {email}")
        print(f"Temporary password: {temp_password}")
        print("Please log in and change your password immediately.")
    else:
        print(f"User not found: {email}")
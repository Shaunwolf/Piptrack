#!/usr/bin/env python3
"""
Password reset utility for PipSqueak.

Usage:
    python reset_password.py <email> [new_password]

If no password is given, a random temporary one is generated and printed
once to the console. Never hardcode credentials in this file.
"""
import argparse
import secrets
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
    parser = argparse.ArgumentParser(description="Reset a user's password")
    parser.add_argument("email", help="Email address of the account to reset")
    parser.add_argument("password", nargs="?", default=None,
                        help="New password (omit to generate a random temporary one)")
    args = parser.parse_args()

    temp_password = args.password or secrets.token_urlsafe(12)

    if reset_user_password(args.email, temp_password):
        print(f"Password reset successful for {args.email}")
        if args.password is None:
            print(f"Temporary password: {temp_password}")
        print("Please log in and change your password immediately.")
    else:
        print(f"User not found: {args.email}")

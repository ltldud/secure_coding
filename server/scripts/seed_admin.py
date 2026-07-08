"""Create (or promote) the admin account from environment variables.

Credentials are never hardcoded in source: set ADMIN_USERNAME / ADMIN_PASSWORD
in the environment (or a local .env file, see .env.example) before running.

    python scripts/seed_admin.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app import app  # noqa: E402
from extensions import db  # noqa: E402
from models import User  # noqa: E402
from config import Config  # noqa: E402
from security import is_valid_username, is_valid_password  # noqa: E402


def main():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")

    if not username or not password:
        print("ADMIN_USERNAME / ADMIN_PASSWORD environment variables are required.")
        sys.exit(1)

    if not is_valid_username(username):
        print("ADMIN_USERNAME must be 3-20 chars, letters/digits/underscore only.")
        sys.exit(1)

    if not is_valid_password(password):
        print("ADMIN_PASSWORD must be 8-64 chars with at least one letter and one digit.")
        sys.exit(1)

    with app.app_context():
        db.create_all()
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, balance=Config.STARTING_BALANCE, role="admin")
            user.set_password(password)
            db.session.add(user)
            print(f"Created new admin user '{username}'.")
        else:
            user.role = "admin"
            user.status = "active"
            user.set_password(password)
            print(f"Promoted existing user '{username}' to admin and reset password.")
        db.session.commit()


if __name__ == "__main__":
    main()

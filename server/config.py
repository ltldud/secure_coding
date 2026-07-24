import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'market.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    WTF_CSRF_TIME_LIMIT = None

    MAX_CONTENT_LENGTH = 3 * 1024 * 1024

    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads", "products")
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    MAX_IMAGE_SIZE = 2 * 1024 * 1024

    STARTING_BALANCE = 1_000_000
    REPORT_THRESHOLD_PRODUCT = 5
    REPORT_THRESHOLD_USER = 5
    LOGIN_FAIL_LIMIT = 5
    LOGIN_LOCK_MINUTES = 15

    DEBUG = False


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False

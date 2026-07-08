import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY must come from the environment in real deployments; the
    # fallback below is only for local/dev convenience and is intentionally
    # different every process start so a stale dev key can't leak into prod.
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

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB request body cap

    # Business rules
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

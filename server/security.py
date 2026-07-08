import re
import bcrypt

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
# At least one letter and one digit, 8-64 chars. Not a full complexity policy,
# just enough to keep out trivially weak/empty passwords.
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,64}$")


def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(raw_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def is_valid_username(username: str) -> bool:
    return bool(username) and bool(USERNAME_RE.match(username))


def is_valid_password(password: str) -> bool:
    return bool(password) and bool(PASSWORD_RE.match(password))

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

# ---------------------------------------------------------
# Security configuration
# ---------------------------------------------------------
# Change these before submission / deployment.
# In production, move them to environment variables.
# ---------------------------------------------------------
SECRET_KEY = "change-this-to-a-long-random-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ---------------------------------------------------------
# Password hashing
# ---------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------
# Demo admin account
# ---------------------------------------------------------
# For now, keep one admin account to protect write endpoints.
# Later, this can be moved to a users table.
# ---------------------------------------------------------
ADMIN_USERNAME = "admin"

# Generate this once using:
# from app.core.security import get_password_hash
# print(get_password_hash("admin123"))
ADMIN_PASSWORD_HASH = "$2b$12$/uoMS7a73wcSdXaGE5JWAONbCSZvTsSEFZNoYRAULsMU/bnIBca/W"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_admin(username: str, password: str) -> dict[str, Any] | None:
    """
    Authenticate the single admin user.
    """
    if username != ADMIN_USERNAME:
        return None

    if not verify_password(password, ADMIN_PASSWORD_HASH):
        return None

    return {
        "username": ADMIN_USERNAME,
        "role": "admin",
    }


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise JWTError("Invalid or expired token") from exc
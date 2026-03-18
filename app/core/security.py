import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

# Get secrets from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-long-random-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get admin credentials from environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_admin(username: str, password: str) -> dict[str, Any] | None:
    if username.strip() != ADMIN_USERNAME:
        return None

    if password != ADMIN_PASSWORD:
        return None

    return {
        "sub": ADMIN_USERNAME,
        "role": "admin",
    }


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise JWTError("Invalid or expired token") from exc
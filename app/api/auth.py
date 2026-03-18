from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_admin,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.db.database import get_db
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserSignup, UserUpdate

router = APIRouter(prefix="/auth", tags=["Auth"])

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    subject = payload.get("sub")
    role = payload.get("role")

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    if role == "admin":
        return {
            "user_id": None,
            "username": subject,
            "email": None,
            "role": "admin",
        }

    row = db.execute(
        text("""
            SELECT user_id, username, email
            FROM users
            WHERE user_id = :user_id
            LIMIT 1
        """),
        {"user_id": int(subject)},
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    user = dict(row._mapping)
    user["role"] = "user"
    return user


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.execute(
        text("""
            SELECT user_id
            FROM users
            WHERE username = :username OR email = :email
            LIMIT 1
        """),
        {
            "username": payload.username,
            "email": payload.email,
        },
    ).fetchone()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    hashed_password = get_password_hash(payload.password)

    row = db.execute(
        text("""
            INSERT INTO users (username, email, hashed_password)
            VALUES (:username, :email, :hashed_password)
            RETURNING user_id, username, email
        """),
        {
            "username": payload.username,
            "email": payload.email,
            "hashed_password": hashed_password,
        },
    ).fetchone()

    db.commit()

    user_data = dict(row._mapping)

    access_token = create_access_token(
        data={"sub": str(user_data["user_id"]), "role": "user"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data,
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT user_id, username, email, hashed_password
            FROM users
            WHERE email = :email
            LIMIT 1
        """),
        {"email": payload.email},
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = dict(row._mapping)

    if not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={"sub": str(user["user_id"]), "role": "user"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
        },
    }


@router.post("/admin/login")
def admin_login(payload: UserLogin):
    admin = authenticate_admin(payload.email, payload.password)

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )

    access_token = create_access_token(
        data=admin,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "admin",
    }
    
@router.get("/me", response_model=UserOut)
def read_me(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account does not have a user profile",
        )

    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "email": current_user["email"],
    }


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account cannot use this endpoint",
        )

    user_id = current_user["user_id"]

    existing = db.execute(
        text("""
            SELECT user_id, username, email, hashed_password
            FROM users
            WHERE user_id = :user_id
            LIMIT 1
        """),
        {"user_id": user_id},
    ).fetchone()

    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing_data = dict(existing._mapping)

    new_username = payload.username if payload.username is not None else existing_data["username"]
    new_email = payload.email if payload.email is not None else existing_data["email"]
    new_hashed_password = (
        get_password_hash(payload.password)
        if payload.password is not None
        else existing_data["hashed_password"]
    )

    duplicate = db.execute(
        text("""
            SELECT user_id
            FROM users
            WHERE (username = :username OR email = :email)
              AND user_id <> :user_id
            LIMIT 1
        """),
        {
            "username": new_username,
            "email": new_email,
            "user_id": user_id,
        },
    ).fetchone()

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    updated = db.execute(
        text("""
            UPDATE users
            SET username = :username,
                email = :email,
                hashed_password = :hashed_password
            WHERE user_id = :user_id
            RETURNING user_id, username, email
        """),
        {
            "user_id": user_id,
            "username": new_username,
            "email": new_email,
            "hashed_password": new_hashed_password,
        },
    ).fetchone()

    db.commit()

    return dict(updated._mapping)


@router.delete("/me")
def delete_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account cannot use this endpoint",
        )

    user_id = current_user["user_id"]

    db.execute(
        text("DELETE FROM favorite_drivers WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    db.execute(
        text("DELETE FROM favorite_constructors WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    db.execute(
        text("DELETE FROM favorite_circuits WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    db.execute(
        text("DELETE FROM users WHERE user_id = :user_id"),
        {"user_id": user_id},
    )

    db.commit()

    return {"message": "Account deleted successfully"}
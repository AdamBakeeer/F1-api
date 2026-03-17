from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.auth import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("/")
def get_my_favorites(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account cannot use favorites",
        )

    user_id = current_user["user_id"]

    favorite_drivers = db.execute(
        text("""
            SELECT
                d.driver_id,
                d.forename,
                d.surname,
                d.code,
                d.nationality,
                LOWER(REPLACE(d.forename || '-' || d.surname, ' ', '-')) AS driver_slug
            FROM favorite_drivers fd
            JOIN drivers d ON d.driver_id = fd.driver_id
            WHERE fd.user_id = :user_id
            ORDER BY d.surname, d.forename
        """),
        {"user_id": user_id},
    ).fetchall()

    favorite_constructors = db.execute(
        text("""
            SELECT
                c.constructor_id,
                c.name,
                c.nationality,
                LOWER(REPLACE(c.name, ' ', '-')) AS constructor_slug
            FROM favorite_constructors fc
            JOIN constructors c ON c.constructor_id = fc.constructor_id
            WHERE fc.user_id = :user_id
            ORDER BY c.name
        """),
        {"user_id": user_id},
    ).fetchall()

    favorite_circuits = db.execute(
        text("""
            SELECT
                c.circuit_id,
                c.name,
                c.location,
                c.country,
                LOWER(REPLACE(c.name, ' ', '-')) AS circuit_slug
            FROM favorite_circuits fc
            JOIN circuits c ON c.circuit_id = fc.circuit_id
            WHERE fc.user_id = :user_id
            ORDER BY c.name
        """),
        {"user_id": user_id},
    ).fetchall()

    return {
        "drivers": [dict(row._mapping) for row in favorite_drivers],
        "constructors": [dict(row._mapping) for row in favorite_constructors],
        "circuits": [dict(row._mapping) for row in favorite_circuits],
    }


@router.post("/drivers/{driver_slug}")
def add_favorite_driver(
    driver_slug: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Admin account cannot use favorites")

    user_id = current_user["user_id"]

    driver = db.execute(
        text("""
            SELECT driver_id
            FROM drivers
            WHERE LOWER(REPLACE(forename || '-' || surname, ' ', '-')) = :driver_slug
            LIMIT 1
        """),
        {"driver_slug": driver_slug},
    ).fetchone()

    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver_id = driver._mapping["driver_id"]

    exists = db.execute(
        text("""
            SELECT 1
            FROM favorite_drivers
            WHERE user_id = :user_id AND driver_id = :driver_id
            LIMIT 1
        """),
        {"user_id": user_id, "driver_id": driver_id},
    ).fetchone()

    if exists:
        return {"message": "Driver already in favorites"}

    db.execute(
        text("""
            INSERT INTO favorite_drivers (user_id, driver_id)
            VALUES (:user_id, :driver_id)
        """),
        {"user_id": user_id, "driver_id": driver_id},
    )
    db.commit()

    return {"message": "Driver added to favorites"}


@router.delete("/drivers/{driver_slug}")
def remove_favorite_driver(
    driver_slug: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Admin account cannot use favorites")

    user_id = current_user["user_id"]

    driver = db.execute(
        text("""
            SELECT driver_id
            FROM drivers
            WHERE LOWER(REPLACE(forename || '-' || surname, ' ', '-')) = :driver_slug
            LIMIT 1
        """),
        {"driver_slug": driver_slug},
    ).fetchone()

    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    db.execute(
        text("""
            DELETE FROM favorite_drivers
            WHERE user_id = :user_id
              AND driver_id = :driver_id
        """),
        {
            "user_id": user_id,
            "driver_id": driver._mapping["driver_id"],
        },
    )
    db.commit()

    return {"message": "Driver removed from favorites"}


@router.post("/constructors/{constructor_slug}")
def add_favorite_constructor(
    constructor_slug: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Admin account cannot use favorites")

    user_id = current_user["user_id"]

    constructor = db.execute(
        text("""
            SELECT constructor_id
            FROM constructors
            WHERE LOWER(REPLACE(name, ' ', '-')) = :constructor_slug
            LIMIT 1
        """),
        {"constructor_slug": constructor_slug},
    ).fetchone()

    if constructor is None:
        raise HTTPException(status_code=404, detail="Constructor not found")

    constructor_id = constructor._mapping["constructor_id"]

    exists = db.execute(
        text("""
            SELECT 1
            FROM favorite_constructors
            WHERE user_id = :user_id AND constructor_id = :constructor_id
            LIMIT 1
        """),
        {"user_id": user_id, "constructor_id": constructor_id},
    ).fetchone()

    if exists:
        return {"message": "Constructor already in favorites"}

    db.execute(
        text("""
            INSERT INTO favorite_constructors (user_id, constructor_id)
            VALUES (:user_id, :constructor_id)
        """),
        {"user_id": user_id, "constructor_id": constructor_id},
    )
    db.commit()

    return {"message": "Constructor added to favorites"}


@router.delete("/constructors/{constructor_slug}")
def remove_favorite_constructor(
    constructor_slug: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Admin account cannot use favorites")

    user_id = current_user["user_id"]

    constructor = db.execute(
        text("""
            SELECT constructor_id
            FROM constructors
            WHERE LOWER(REPLACE(name, ' ', '-')) = :constructor_slug
            LIMIT 1
        """),
        {"constructor_slug": constructor_slug},
    ).fetchone()

    if constructor is None:
        raise HTTPException(status_code=404, detail="Constructor not found")

    db.execute(
        text("""
            DELETE FROM favorite_constructors
            WHERE user_id = :user_id
              AND constructor_id = :constructor_id
        """),
        {
            "user_id": user_id,
            "constructor_id": constructor._mapping["constructor_id"],
        },
    )
    db.commit()

    return {"message": "Constructor removed from favorites"}


@router.post("/circuits/{circuit_slug}")
def add_favorite_circuit(
    circuit_slug: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Admin account cannot use favorites")

    user_id = current_user["user_id"]

    circuit = db.execute(
        text("""
            SELECT circuit_id
            FROM circuits
            WHERE LOWER(REPLACE(name, ' ', '-')) = :circuit_slug
            LIMIT 1
        """),
        {"circuit_slug": circuit_slug},
    ).fetchone()

    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")

    circuit_id = circuit._mapping["circuit_id"]

    exists = db.execute(
        text("""
            SELECT 1
            FROM favorite_circuits
            WHERE user_id = :user_id AND circuit_id = :circuit_id
            LIMIT 1
        """),
        {"user_id": user_id, "circuit_id": circuit_id},
    ).fetchone()

    if exists:
        return {"message": "Circuit already in favorites"}

    db.execute(
        text("""
            INSERT INTO favorite_circuits (user_id, circuit_id)
            VALUES (:user_id, :circuit_id)
        """),
        {"user_id": user_id, "circuit_id": circuit_id},
    )
    db.commit()

    return {"message": "Circuit added to favorites"}


@router.delete("/circuits/{circuit_slug}")
def remove_favorite_circuit(
    circuit_slug: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Admin account cannot use favorites")

    user_id = current_user["user_id"]

    circuit = db.execute(
        text("""
            SELECT circuit_id
            FROM circuits
            WHERE LOWER(REPLACE(name, ' ', '-')) = :circuit_slug
            LIMIT 1
        """),
        {"circuit_slug": circuit_slug},
    ).fetchone()

    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")

    db.execute(
        text("""
            DELETE FROM favorite_circuits
            WHERE user_id = :user_id
              AND circuit_id = :circuit_id
        """),
        {
            "user_id": user_id,
            "circuit_id": circuit._mapping["circuit_id"],
        },
    )
    db.commit()

    return {"message": "Circuit removed from favorites"}
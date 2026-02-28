from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
# All endpoints in this file are grouped under /drivers
# and tagged as "Drivers" in Swagger documentation.
# ---------------------------------------------------------

router = APIRouter(prefix="/drivers", tags=["Drivers"])


# ---------------------------------------------------------
# 1️⃣ GET /drivers
# Returns all-time drivers with optional filtering
# Supports pagination and search.
# ---------------------------------------------------------
@router.get("/")
def list_drivers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    nationality: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve all-time drivers.

    Optional:
    - limit / offset for pagination
    - nationality filter
    - q search by first or last name
    """

    sql = """
    SELECT driver_id, code, forename, surname, dob, nationality
    FROM drivers
    WHERE (:nationality IS NULL OR nationality ILIKE :nationality_like)
      AND (:q IS NULL OR (forename ILIKE :q_like OR surname ILIKE :q_like))
    ORDER BY surname, forename
    LIMIT :limit OFFSET :offset;
    """

    params = {
        "limit": limit,
        "offset": offset,
        "nationality": nationality,
        "nationality_like": f"%{nationality}%" if nationality else None,
        "q": q,
        "q_like": f"%{q}%" if q else None,
    }

    rows = db.execute(text(sql), params).fetchall()

    return {
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "data": [dict(r._mapping) for r in rows],
    }


# ---------------------------------------------------------
# 2️⃣ GET /drivers/current
# Returns drivers who participated in the latest season
# ---------------------------------------------------------
@router.get("/current")
def current_drivers(db: Session = Depends(get_db)):
    """
    Retrieve drivers who participated in the most recent season.
    """

    # Find latest season in database
    latest_year = db.execute(text("SELECT MAX(year) FROM races")).scalar()

    sql = """
    SELECT DISTINCT d.driver_id, d.code, d.forename, d.surname, d.dob, d.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN drivers d ON d.driver_id = r.driver_id
    WHERE ra.year = :year
    ORDER BY d.surname, d.forename;
    """

    rows = db.execute(text(sql), {"year": latest_year}).fetchall()

    return {
        "season": latest_year,
        "count": len(rows),
        "data": [dict(r._mapping) for r in rows],
    }


# ---------------------------------------------------------
# 3️⃣ GET /drivers/season/{year}
# Returns drivers who participated in a specific season
# ---------------------------------------------------------
@router.get("/season/{year}")
def drivers_by_season(year: int, db: Session = Depends(get_db)):
    """
    Retrieve drivers who participated in a specific season.
    """

    sql = """
    SELECT DISTINCT d.driver_id, d.code, d.forename, d.surname, d.dob, d.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN drivers d ON d.driver_id = r.driver_id
    WHERE ra.year = :year
    ORDER BY d.surname, d.forename;
    """

    rows = db.execute(text(sql), {"year": year}).fetchall()

    return {
        "season": year,
        "count": len(rows),
        "data": [dict(r._mapping) for r in rows],
    }


# ---------------------------------------------------------
# 4️⃣ GET /drivers/{driver_id}
# Returns a single driver by ID
# ---------------------------------------------------------
@router.get("/{driver_id}")
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single driver by ID.
    """

    sql = """
    SELECT driver_id, code, forename, surname, dob, nationality
    FROM drivers
    WHERE driver_id = :driver_id;
    """

    row = db.execute(text(sql), {"driver_id": driver_id}).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    return dict(row._mapping)
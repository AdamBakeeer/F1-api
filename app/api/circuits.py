from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.core.deps import require_admin

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
router = APIRouter(prefix="/circuits", tags=["Circuits"])


# ---------------------------------------------------------
# Schemas for admin CRUD
# ---------------------------------------------------------
class CircuitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    location: str | None = Field(default=None, max_length=150)
    country: str | None = Field(default=None, max_length=150)
    lat: float | None = None
    lng: float | None = None
    alt: int | None = None


class CircuitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    location: str | None = Field(default=None, max_length=150)
    country: str | None = Field(default=None, max_length=150)
    lat: float | None = None
    lng: float | None = None
    alt: int | None = None


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def ensure_circuit_exists(circuit_id: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM circuits WHERE circuit_id = :circuit_id LIMIT 1"),
        {"circuit_id": circuit_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Circuit not found")


def ensure_season_exists(year: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE year = :year LIMIT 1"),
        {"year": year},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")


# ---------------------------------------------------------
# 1️⃣ GET /circuits
# Returns all circuits with optional filtering
# ---------------------------------------------------------
@router.get("/")
def list_circuits(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    country: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve all circuits.

    Optional:
    - limit / offset for pagination
    - country filter
    - q search by circuit name or location
    """

    sql = """
    SELECT circuit_id, name, location, country, lat, lng, alt
    FROM circuits
    WHERE (:country IS NULL OR country ILIKE :country_like)
      AND (
            :q IS NULL
            OR name ILIKE :q_like
            OR location ILIKE :q_like
            OR country ILIKE :q_like
          )
    ORDER BY name
    LIMIT :limit OFFSET :offset;
    """

    rows = db.execute(
        text(sql),
        {
            "limit": limit,
            "offset": offset,
            "country": country,
            "country_like": f"%{country}%" if country else None,
            "q": q,
            "q_like": f"%{q}%" if q else None,
        },
    ).fetchall()

    return {
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 2️⃣ POST /circuits
# Create a new circuit (admin only)
# ---------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_circuit(
    payload: CircuitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Create a new circuit.
    Admin only.
    """

    new_circuit_id = db.execute(
        text("SELECT COALESCE(MAX(circuit_id), 0) + 1 AS next_id FROM circuits")
    ).scalar()

    row = db.execute(
        text("""
            INSERT INTO circuits (circuit_id, name, location, country, lat, lng, alt)
            VALUES (:circuit_id, :name, :location, :country, :lat, :lng, :alt)
            RETURNING circuit_id, name, location, country, lat, lng, alt
        """),
        {
            "circuit_id": new_circuit_id,
            "name": payload.name,
            "location": payload.location,
            "country": payload.country,
            "lat": payload.lat,
            "lng": payload.lng,
            "alt": payload.alt,
        },
    ).fetchone()

    db.commit()

    return {
        "message": "Circuit created successfully",
        "data": dict(row._mapping),
    }


# ---------------------------------------------------------
# 3️⃣ GET /circuits/current
# Returns circuits used in the latest season
# ---------------------------------------------------------
@router.get("/current")
def current_circuits(db: Session = Depends(get_db)):
    """
    Retrieve circuits used in the most recent season.
    """

    latest_year = db.execute(text("SELECT MAX(year) FROM races")).scalar()

    if latest_year is None:
        raise HTTPException(status_code=404, detail="No seasons found")

    sql = """
    SELECT DISTINCT c.circuit_id, c.name, c.location, c.country, c.lat, c.lng, c.alt
    FROM races r
    JOIN circuits c ON c.circuit_id = r.circuit_id
    WHERE r.year = :year
    ORDER BY r.round;
    """

    rows = db.execute(text(sql), {"year": latest_year}).fetchall()

    return {
        "season": latest_year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 4️⃣ GET /circuits/season/{year}
# Returns circuits used in a specific season
# ---------------------------------------------------------
@router.get("/season/{year}")
def circuits_by_season(year: int, db: Session = Depends(get_db)):
    """
    Retrieve circuits used in a specific season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT DISTINCT c.circuit_id, c.name, c.location, c.country, c.lat, c.lng, c.alt
    FROM races r
    JOIN circuits c ON c.circuit_id = r.circuit_id
    WHERE r.year = :year
    ORDER BY r.round;
    """

    rows = db.execute(text(sql), {"year": year}).fetchall()

    return {
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 5️⃣ GET /circuits/{circuit_id}/stats
# Summary statistics for a circuit
# ---------------------------------------------------------
@router.get("/{circuit_id}/stats")
def circuit_stats(circuit_id: int, db: Session = Depends(get_db)):
    """
    Retrieve summary statistics for a circuit.
    """

    ensure_circuit_exists(circuit_id, db)

    sql = """
    SELECT
        c.circuit_id,
        c.name AS circuit_name,
        c.location,
        c.country,
        COUNT(DISTINCT r.race_id) AS races_hosted,
        MIN(r.year) AS first_season,
        MAX(r.year) AS last_season,
        COUNT(res.result_id) AS total_result_rows,
        COUNT(DISTINCT res.driver_id) AS unique_drivers,
        COUNT(DISTINCT res.constructor_id) AS unique_constructors,
        COALESCE(AVG(res.points), 0) AS avg_points_awarded_per_result
    FROM circuits c
    LEFT JOIN races r ON r.circuit_id = c.circuit_id
    LEFT JOIN results res ON res.race_id = r.race_id
    WHERE c.circuit_id = :circuit_id
    GROUP BY c.circuit_id, c.name, c.location, c.country;
    """

    row = db.execute(text(sql), {"circuit_id": circuit_id}).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Circuit stats not found")

    return dict(row._mapping)


# ---------------------------------------------------------
# 6️⃣ GET /circuits/{circuit_id}/races
# Returns all races hosted at this circuit
# ---------------------------------------------------------
@router.get("/{circuit_id}/races")
def circuit_races(
    circuit_id: int,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve races held at a given circuit.

    Optional:
    - year: restrict to one season
    """

    ensure_circuit_exists(circuit_id, db)

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        race_id,
        year,
        round,
        name,
        date,
        time
    FROM races
    WHERE circuit_id = :circuit_id
      AND (:year IS NULL OR year = :year)
    ORDER BY year, round;
    """

    rows = db.execute(
        text(sql),
        {"circuit_id": circuit_id, "year": year},
    ).fetchall()

    return {
        "circuit_id": circuit_id,
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 7️⃣ GET /circuits/{circuit_id}/winners
# Returns race winners at this circuit by season
# ---------------------------------------------------------
@router.get("/{circuit_id}/winners")
def circuit_winners(circuit_id: int, db: Session = Depends(get_db)):
    """
    Retrieve race winners at a circuit across all seasons.
    """

    ensure_circuit_exists(circuit_id, db)

    sql = """
    SELECT
        ra.year,
        ra.round,
        ra.race_id,
        ra.name AS race_name,
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        c.constructor_id,
        c.name AS constructor_name
    FROM races ra
    JOIN results res ON res.race_id = ra.race_id
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    WHERE ra.circuit_id = :circuit_id
      AND res.position_order = 1
    ORDER BY ra.year, ra.round;
    """

    rows = db.execute(text(sql), {"circuit_id": circuit_id}).fetchall()

    return {
        "circuit_id": circuit_id,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 8️⃣ GET /circuits/{circuit_id}/top-drivers
# Best-performing drivers at this circuit
# ---------------------------------------------------------
@router.get("/{circuit_id}/top-drivers")
def circuit_top_drivers(
    circuit_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Retrieve top-performing drivers at a circuit.
    Ranked by wins, then podiums, then total points.
    """

    ensure_circuit_exists(circuit_id, db)

    sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_year,
        MAX(ra.year) AS last_year
    FROM races ra
    JOIN results res ON res.race_id = ra.race_id
    JOIN drivers d ON d.driver_id = res.driver_id
    WHERE ra.circuit_id = :circuit_id
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality
    ORDER BY wins DESC, podiums DESC, total_points DESC, d.surname, d.forename
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"circuit_id": circuit_id, "limit": limit},
    ).fetchall()

    return {
        "circuit_id": circuit_id,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 9️⃣ GET /circuits/{circuit_id}/top-constructors
# Best-performing constructors at this circuit
# ---------------------------------------------------------
@router.get("/{circuit_id}/top-constructors")
def circuit_top_constructors(
    circuit_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Retrieve top-performing constructors at a circuit.
    Ranked by wins, then podiums, then total points.
    """

    ensure_circuit_exists(circuit_id, db)

    sql = """
    SELECT
        c.constructor_id,
        c.name AS constructor_name,
        c.nationality,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_year,
        MAX(ra.year) AS last_year
    FROM races ra
    JOIN results res ON res.race_id = ra.race_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    WHERE ra.circuit_id = :circuit_id
    GROUP BY c.constructor_id, c.name, c.nationality
    ORDER BY wins DESC, podiums DESC, total_points DESC, constructor_name
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"circuit_id": circuit_id, "limit": limit},
    ).fetchall()

    return {
        "circuit_id": circuit_id,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 🔟 PATCH /circuits/{circuit_id}
# Update an existing circuit (admin only)
# ---------------------------------------------------------
@router.patch("/{circuit_id}")
def update_circuit(
    circuit_id: int,
    payload: CircuitUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Update a circuit.
    Admin only.
    """

    ensure_circuit_exists(circuit_id, db)

    existing = db.execute(
        text("""
            SELECT circuit_id, name, location, country, lat, lng, alt
            FROM circuits
            WHERE circuit_id = :circuit_id
        """),
        {"circuit_id": circuit_id},
    ).fetchone()

    existing_data = dict(existing._mapping)

    updated_data = {
        "circuit_id": circuit_id,
        "name": payload.name if payload.name is not None else existing_data["name"],
        "location": payload.location if payload.location is not None else existing_data["location"],
        "country": payload.country if payload.country is not None else existing_data["country"],
        "lat": payload.lat if payload.lat is not None else existing_data["lat"],
        "lng": payload.lng if payload.lng is not None else existing_data["lng"],
        "alt": payload.alt if payload.alt is not None else existing_data["alt"],
    }

    row = db.execute(
        text("""
            UPDATE circuits
            SET name = :name,
                location = :location,
                country = :country,
                lat = :lat,
                lng = :lng,
                alt = :alt
            WHERE circuit_id = :circuit_id
            RETURNING circuit_id, name, location, country, lat, lng, alt
        """),
        updated_data,
    ).fetchone()

    db.commit()

    return {
        "message": "Circuit updated successfully",
        "data": dict(row._mapping),
    }


# ---------------------------------------------------------
# 1️⃣1️⃣ DELETE /circuits/{circuit_id}
# Delete a circuit (admin only)
# ---------------------------------------------------------
@router.delete("/{circuit_id}")
def delete_circuit(
    circuit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Delete a circuit.
    Admin only.

    Prevent deletion if related races exist.
    """

    ensure_circuit_exists(circuit_id, db)

    dependency_count = db.execute(
        text("SELECT COUNT(*) FROM races WHERE circuit_id = :circuit_id"),
        {"circuit_id": circuit_id},
    ).scalar()

    if dependency_count and dependency_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete circuit because related races exist",
        )

    db.execute(
        text("DELETE FROM circuits WHERE circuit_id = :circuit_id"),
        {"circuit_id": circuit_id},
    )
    db.commit()

    return {
        "message": "Circuit deleted successfully",
        "circuit_id": circuit_id,
    }


# ---------------------------------------------------------
# 1️⃣2️⃣ GET /circuits/{circuit_id}
# Returns a single circuit by ID
# ---------------------------------------------------------
@router.get("/{circuit_id}")
def get_circuit(circuit_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single circuit by ID.
    """

    sql = """
    SELECT circuit_id, name, location, country, lat, lng, alt
    FROM circuits
    WHERE circuit_id = :circuit_id;
    """

    row = db.execute(
        text(sql),
        {"circuit_id": circuit_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Circuit not found")

    return dict(row._mapping)
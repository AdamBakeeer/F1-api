from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
import re

from app.db.database import get_db
from app.core.deps import require_admin

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
router = APIRouter(prefix="/drivers", tags=["Drivers"])


# ---------------------------------------------------------
# Pydantic schemas for admin CRUD
# ---------------------------------------------------------
class DriverCreate(BaseModel):
    code: str | None = Field(default=None, max_length=3)
    forename: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    dob: str | None = None
    nationality: str | None = Field(default=None, max_length=100)


class DriverUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=3)
    forename: str | None = Field(default=None, min_length=1, max_length=100)
    surname: str | None = Field(default=None, min_length=1, max_length=100)
    dob: str | None = None
    nationality: str | None = Field(default=None, max_length=100)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def slugify_name(forename: str, surname: str) -> str:
    full_name = f"{forename} {surname}".strip().lower()
    full_name = re.sub(r"[^a-z0-9\s-]", "", full_name)
    full_name = re.sub(r"\s+", "-", full_name)
    return full_name


def add_driver_slug(row_dict: dict) -> dict:
    row_dict["driver_slug"] = slugify_name(
        row_dict.get("forename", ""),
        row_dict.get("surname", "")
    )
    return row_dict


def ensure_season_exists(year: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE year = :year LIMIT 1"),
        {"year": year},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")


def get_driver_row_by_slug_or_404(driver_slug: str, db: Session):
    rows = db.execute(
        text("""
            SELECT driver_id, code, forename, surname, dob, nationality
            FROM drivers
            ORDER BY driver_id
        """)
    ).fetchall()

    for row in rows:
        row_dict = dict(row._mapping)
        if slugify_name(row_dict["forename"], row_dict["surname"]) == driver_slug.lower():
            return row

    raise HTTPException(status_code=404, detail="Driver not found")


def get_driver_id_by_slug(driver_slug: str, db: Session) -> int:
    row = get_driver_row_by_slug_or_404(driver_slug, db)
    return row._mapping["driver_id"]


# ---------------------------------------------------------
# 1️⃣ GET /drivers
# Browse drivers with filters
# ---------------------------------------------------------
@router.get("/")
def list_drivers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    season: int | None = Query(None, ge=1950),
    nationality: str | None = None,
    team: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Browse drivers with optional filters:
    - q
    - season
    - nationality
    - team
    """

    if season is not None:
        ensure_season_exists(season, db)

    sql = """
    SELECT DISTINCT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.dob,
        d.nationality
    FROM drivers d
    LEFT JOIN results res ON res.driver_id = d.driver_id
    LEFT JOIN races ra ON ra.race_id = res.race_id
    LEFT JOIN constructors c ON c.constructor_id = res.constructor_id
    WHERE (:q IS NULL OR d.forename ILIKE :q_like OR d.surname ILIKE :q_like)
      AND (:nationality IS NULL OR d.nationality ILIKE :nationality_like)
      AND (:season IS NULL OR ra.year = :season)
      AND (:team IS NULL OR c.name ILIKE :team_like)
    ORDER BY d.surname, d.forename
    LIMIT :limit OFFSET :offset;
    """

    rows = db.execute(
        text(sql),
        {
            "limit": limit,
            "offset": offset,
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "season": season,
            "nationality": nationality,
            "nationality_like": f"%{nationality}%" if nationality else None,
            "team": team,
            "team_like": f"%{team}%" if team else None,
        },
    ).fetchall()

    data = [add_driver_slug(dict(row._mapping)) for row in rows]

    return {
        "limit": limit,
        "offset": offset,
        "count": len(data),
        "filters": {
            "q": q,
            "season": season,
            "nationality": nationality,
            "team": team,
        },
        "data": data,
    }


# ---------------------------------------------------------
# 2️⃣ POST /drivers
# Create a new driver (admin only)
# ---------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Create a new driver.
    Admin only.
    """

    new_driver_id = db.execute(
        text("SELECT COALESCE(MAX(driver_id), 0) + 1 AS next_id FROM drivers")
    ).scalar()

    sql = """
    INSERT INTO drivers (driver_id, code, forename, surname, dob, nationality)
    VALUES (:driver_id, :code, :forename, :surname, :dob, :nationality)
    RETURNING driver_id, code, forename, surname, dob, nationality;
    """

    row = db.execute(
        text(sql),
        {
            "driver_id": new_driver_id,
            "code": payload.code,
            "forename": payload.forename,
            "surname": payload.surname,
            "dob": payload.dob,
            "nationality": payload.nationality,
        },
    ).fetchone()

    db.commit()

    data = add_driver_slug(dict(row._mapping))

    return {
        "message": "Driver created successfully",
        "data": data,
    }


# ---------------------------------------------------------
# 3️⃣ GET /drivers/current
# Returns drivers who participated in the latest season
# ---------------------------------------------------------
@router.get("/current")
def current_drivers(db: Session = Depends(get_db)):
    """
    Retrieve drivers who participated in the most recent season.
    """

    latest_year = db.execute(text("SELECT MAX(year) FROM races")).scalar()

    if latest_year is None:
        raise HTTPException(status_code=404, detail="No seasons found")

    sql = """
    SELECT DISTINCT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.dob,
        d.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN drivers d ON d.driver_id = r.driver_id
    WHERE ra.year = :year
    ORDER BY d.surname, d.forename;
    """

    rows = db.execute(text(sql), {"year": latest_year}).fetchall()
    data = [add_driver_slug(dict(row._mapping)) for row in rows]

    return {
        "season": latest_year,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 4️⃣ GET /drivers/season/{year}
# Returns drivers who participated in a specific season
# ---------------------------------------------------------
@router.get("/season/{year}")
def drivers_by_season(year: int, db: Session = Depends(get_db)):
    """
    Retrieve drivers who participated in a specific season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT DISTINCT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.dob,
        d.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN drivers d ON d.driver_id = r.driver_id
    WHERE ra.year = :year
    ORDER BY d.surname, d.forename;
    """

    rows = db.execute(text(sql), {"year": year}).fetchall()
    data = [add_driver_slug(dict(row._mapping)) for row in rows]

    return {
        "season": year,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 5️⃣ GET /drivers/standings/{year}
# Returns driver standings for a given season
# Optional: round
# ---------------------------------------------------------
@router.get("/standings/{year}")
def driver_standings(
    year: int,
    round: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    """
    Retrieve driver standings for a given season.

    Optional:
    - round: standings up to and including a given round
    """

    ensure_season_exists(year, db)

    if round is not None:
        round_exists = db.execute(
            text("""
                SELECT 1
                FROM races
                WHERE year = :year AND round = :round
                LIMIT 1
            """),
            {"year": year, "round": round},
        ).fetchone()

        if round_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Round {round} not found for season {year}",
            )

    sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        SUM(r.points) AS points,
        SUM(CASE WHEN r.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN r.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        COUNT(r.result_id) AS race_entries
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN drivers d ON d.driver_id = r.driver_id
    WHERE ra.year = :year
      AND (:round IS NULL OR ra.round <= :round)
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality
    ORDER BY points DESC, wins DESC, podiums DESC, surname ASC, forename ASC;
    """

    rows = db.execute(
        text(sql),
        {
            "year": year,
            "round": round,
        },
    ).fetchall()

    data = []
    for idx, row in enumerate(rows, start=1):
        item = add_driver_slug(dict(row._mapping))
        item["position"] = idx
        data.append(item)

    return {
        "season": year,
        "round": round,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 6️⃣ GET /drivers/{driver_slug}
# Driver profile
# ---------------------------------------------------------
@router.get("/{driver_slug}")
def get_driver(driver_slug: str, db: Session = Depends(get_db)):
    """
    Retrieve a single driver profile by slug.
    """

    row = get_driver_row_by_slug_or_404(driver_slug, db)
    data = add_driver_slug(dict(row._mapping))
    return data


# ---------------------------------------------------------
# 7️⃣ GET /drivers/{driver_slug}/stats
# Career or season-specific summary
# ---------------------------------------------------------
@router.get("/{driver_slug}/stats")
def driver_stats(
    driver_slug: str,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve career statistics for a driver.

    Optional:
    - year: restrict stats to a single season
    """

    driver_id = get_driver_id_by_slug(driver_slug, db)

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        COUNT(r.result_id) AS race_entries,
        COALESCE(SUM(r.points), 0) AS total_points,
        SUM(CASE WHEN r.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN r.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_season,
        MAX(ra.year) AS last_season,
        MIN(CASE WHEN r.position_order > 0 THEN r.position_order END) AS best_finish
    FROM drivers d
    LEFT JOIN results r ON d.driver_id = r.driver_id
    LEFT JOIN races ra ON ra.race_id = r.race_id
    WHERE d.driver_id = :driver_id
      AND (:year IS NULL OR ra.year = :year)
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality;
    """

    row = db.execute(
        text(sql),
        {"driver_id": driver_id, "year": year},
    ).fetchone()

    data = dict(row._mapping) if row else None

    if data is None:
        raise HTTPException(status_code=404, detail="Driver stats not found")

    data = add_driver_slug(data)

    return {
        "season": year,
        "data": data,
    }


# ---------------------------------------------------------
# 8️⃣ GET /drivers/{driver_slug}/results
# Full race-by-race results for a driver
# ---------------------------------------------------------
@router.get("/{driver_slug}/results")
def driver_results(
    driver_slug: str,
    year: int | None = Query(None, ge=1950),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retrieve race-by-race results for a driver.
    """

    driver_id = get_driver_id_by_slug(driver_slug, db)

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        ra.race_id,
        ra.year,
        ra.round,
        ra.name AS race_name,
        ra.date,
        c.constructor_id,
        c.name AS constructor_name,
        res.grid,
        res.position_order AS finish_position,
        res.points,
        res.laps,
        s.status
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    JOIN status s ON s.status_id = res.status_id
    WHERE res.driver_id = :driver_id
      AND (:year IS NULL OR ra.year = :year)
    ORDER BY ra.year DESC, ra.round DESC
    LIMIT :limit OFFSET :offset;
    """

    rows = db.execute(
        text(sql),
        {
            "driver_id": driver_id,
            "year": year,
            "limit": limit,
            "offset": offset,
        },
    ).fetchall()

    return {
        "driver_slug": driver_slug,
        "season": year,
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 9️⃣ GET /drivers/{driver_slug}/seasons
# Season-by-season performance progression
# ---------------------------------------------------------
@router.get("/{driver_slug}/seasons")
def driver_seasons(driver_slug: str, db: Session = Depends(get_db)):
    """
    Retrieve all seasons in which a driver competed.
    """

    driver_id = get_driver_id_by_slug(driver_slug, db)

    sql = """
    SELECT
        ra.year,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    WHERE res.driver_id = :driver_id
    GROUP BY ra.year
    ORDER BY ra.year;
    """

    rows = db.execute(text(sql), {"driver_id": driver_id}).fetchall()

    return {
        "driver_slug": driver_slug,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 🔟 GET /drivers/{driver_slug}/teams
# Constructors raced for by the driver
# Optional filter by year
# ---------------------------------------------------------
@router.get("/{driver_slug}/teams")
def driver_teams(
    driver_slug: str,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve constructors a driver raced for.
    """

    driver_id = get_driver_id_by_slug(driver_slug, db)

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        c.constructor_id,
        c.name AS constructor_name,
        c.nationality,
        MIN(ra.year) AS first_season,
        MAX(ra.year) AS last_season,
        COUNT(res.result_id) AS race_entries,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    WHERE res.driver_id = :driver_id
      AND (:year IS NULL OR ra.year = :year)
    GROUP BY c.constructor_id, c.name, c.nationality
    ORDER BY first_season, constructor_name;
    """

    rows = db.execute(
        text(sql),
        {"driver_id": driver_id, "year": year},
    ).fetchall()

    return {
        "driver_slug": driver_slug,
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 1️⃣1️⃣ GET /drivers/{driver_slug}/teammates
# Drivers who shared the same constructor in the same race
# ---------------------------------------------------------
@router.get("/{driver_slug}/teammates")
def driver_teammates(
    driver_slug: str,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve teammates of a driver.
    """

    driver_id = get_driver_id_by_slug(driver_slug, db)

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        d2.driver_id AS teammate_id,
        d2.code AS teammate_code,
        d2.forename AS teammate_forename,
        d2.surname AS teammate_surname,
        c.constructor_id,
        c.name AS constructor_name,
        MIN(ra.year) AS first_overlap_season,
        MAX(ra.year) AS last_overlap_season,
        COUNT(*) AS shared_race_entries
    FROM results res1
    JOIN results res2
        ON res1.race_id = res2.race_id
       AND res1.constructor_id = res2.constructor_id
       AND res1.driver_id <> res2.driver_id
    JOIN races ra ON ra.race_id = res1.race_id
    JOIN drivers d2 ON d2.driver_id = res2.driver_id
    JOIN constructors c ON c.constructor_id = res1.constructor_id
    WHERE res1.driver_id = :driver_id
      AND (:year IS NULL OR ra.year = :year)
    GROUP BY d2.driver_id, d2.code, d2.forename, d2.surname, c.constructor_id, c.name
    ORDER BY shared_race_entries DESC, teammate_surname, teammate_forename;
    """

    rows = db.execute(
        text(sql),
        {"driver_id": driver_id, "year": year},
    ).fetchall()

    return {
        "driver_slug": driver_slug,
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 1️⃣2️⃣ GET /drivers/{driver_slug}/best-circuits
# Top circuits for a driver
# ---------------------------------------------------------
@router.get("/{driver_slug}/best-circuits")
def driver_best_circuits(
    driver_slug: str,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Retrieve the best circuits for a driver,
    ranked by wins, podiums, then points.
    """

    driver_id = get_driver_id_by_slug(driver_slug, db)

    sql = """
    SELECT
        ci.circuit_id,
        ci.name AS circuit_name,
        ci.location,
        ci.country,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_year,
        MAX(ra.year) AS last_year
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    JOIN circuits ci ON ci.circuit_id = ra.circuit_id
    WHERE res.driver_id = :driver_id
    GROUP BY ci.circuit_id, ci.name, ci.location, ci.country
    ORDER BY wins DESC, podiums DESC, total_points DESC, circuit_name
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"driver_id": driver_id, "limit": limit},
    ).fetchall()

    return {
        "driver_slug": driver_slug,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 1️⃣3️⃣ GET /drivers/{driver_slug}/dnfs
# DNF / non-finish analysis using status
# ---------------------------------------------------------
@router.get("/{driver_slug}/dnfs")
def driver_dnfs(
    driver_slug: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve DNF / non-finish analysis for a driver.
    """

    driver_id = get_driver_id_by_slug(driver_slug, db)

    summary_sql = """
    SELECT
        COUNT(*) AS total_non_finishes
    FROM results res
    JOIN status s ON s.status_id = res.status_id
    WHERE res.driver_id = :driver_id
      AND s.status NOT ILIKE '%finished%';
    """

    breakdown_sql = """
    SELECT
        s.status,
        COUNT(*) AS count
    FROM results res
    JOIN status s ON s.status_id = res.status_id
    WHERE res.driver_id = :driver_id
      AND s.status NOT ILIKE '%finished%'
    GROUP BY s.status
    ORDER BY count DESC, s.status;
    """

    seasonal_sql = """
    SELECT
        ra.year,
        COUNT(res.result_id) AS race_entries,
        SUM(CASE WHEN s.status NOT ILIKE '%finished%' THEN 1 ELSE 0 END) AS non_finishes,
        ROUND(
            100.0 * SUM(CASE WHEN s.status NOT ILIKE '%finished%' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(res.result_id), 0),
            2
        ) AS dnf_rate_percent
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    JOIN status s ON s.status_id = res.status_id
    WHERE res.driver_id = :driver_id
    GROUP BY ra.year
    ORDER BY ra.year;
    """

    summary = db.execute(text(summary_sql), {"driver_id": driver_id}).fetchone()
    breakdown = db.execute(text(breakdown_sql), {"driver_id": driver_id}).fetchall()
    seasonal = db.execute(text(seasonal_sql), {"driver_id": driver_id}).fetchall()

    return {
        "driver_slug": driver_slug,
        "total_non_finishes": summary._mapping["total_non_finishes"] if summary else 0,
        "breakdown_by_status": [dict(row._mapping) for row in breakdown],
        "dnf_rate_by_season": [dict(row._mapping) for row in seasonal],
    }


# ---------------------------------------------------------
# 1️⃣4️⃣ PATCH /drivers/{driver_slug}
# Update an existing driver (admin only)
# ---------------------------------------------------------
@router.patch("/{driver_slug}")
def update_driver(
    driver_slug: str,
    payload: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Update a driver.
    Admin only.
    """

    driver_row = get_driver_row_by_slug_or_404(driver_slug, db)
    driver_id = driver_row._mapping["driver_id"]

    existing = db.execute(
        text("""
            SELECT driver_id, code, forename, surname, dob, nationality
            FROM drivers
            WHERE driver_id = :driver_id
        """),
        {"driver_id": driver_id},
    ).fetchone()

    existing_data = dict(existing._mapping)

    updated_data = {
        "driver_id": driver_id,
        "code": payload.code if payload.code is not None else existing_data["code"],
        "forename": payload.forename if payload.forename is not None else existing_data["forename"],
        "surname": payload.surname if payload.surname is not None else existing_data["surname"],
        "dob": payload.dob if payload.dob is not None else existing_data["dob"],
        "nationality": payload.nationality if payload.nationality is not None else existing_data["nationality"],
    }

    row = db.execute(
        text("""
            UPDATE drivers
            SET code = :code,
                forename = :forename,
                surname = :surname,
                dob = :dob,
                nationality = :nationality
            WHERE driver_id = :driver_id
            RETURNING driver_id, code, forename, surname, dob, nationality
        """),
        updated_data,
    ).fetchone()

    db.commit()

    data = add_driver_slug(dict(row._mapping))

    return {
        "message": "Driver updated successfully",
        "data": data,
    }


# ---------------------------------------------------------
# 1️⃣5️⃣ DELETE /drivers/{driver_slug}
# Delete a driver (admin only)
# ---------------------------------------------------------
@router.delete("/{driver_slug}")
def delete_driver(
    driver_slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Delete a driver.
    Admin only.

    Prevent deletion if related race results exist.
    """

    driver_row = get_driver_row_by_slug_or_404(driver_slug, db)
    driver_id = driver_row._mapping["driver_id"]

    dependency_count = db.execute(
        text("SELECT COUNT(*) FROM results WHERE driver_id = :driver_id"),
        {"driver_id": driver_id},
    ).scalar()

    if dependency_count and dependency_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete driver because related race results exist",
        )

    db.execute(
        text("DELETE FROM drivers WHERE driver_id = :driver_id"),
        {"driver_id": driver_id},
    )
    db.commit()

    return {
        "message": "Driver deleted successfully",
        "driver_slug": driver_slug,
    }
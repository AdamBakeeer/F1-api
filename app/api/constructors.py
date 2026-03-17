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
router = APIRouter(prefix="/constructors", tags=["Constructors"])


# ---------------------------------------------------------
# Pydantic schemas for admin CRUD
# ---------------------------------------------------------
class ConstructorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    nationality: str | None = Field(default=None, max_length=100)


class ConstructorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    nationality: str | None = Field(default=None, max_length=100)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def slugify_constructor_name(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    return value


def add_constructor_slug(row_dict: dict) -> dict:
    row_dict["constructor_slug"] = slugify_constructor_name(row_dict.get("name", ""))
    return row_dict


def ensure_season_exists(year: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE year = :year LIMIT 1"),
        {"year": year},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")


def get_constructor_row_by_slug_or_404(constructor_slug: str, db: Session):
    rows = db.execute(
        text("""
            SELECT constructor_id, name, nationality
            FROM constructors
            ORDER BY constructor_id
        """)
    ).fetchall()

    for row in rows:
        row_dict = dict(row._mapping)
        if slugify_constructor_name(row_dict["name"]) == constructor_slug.lower():
            return row

    raise HTTPException(status_code=404, detail="Constructor not found")


def get_constructor_id_by_slug(constructor_slug: str, db: Session) -> int:
    row = get_constructor_row_by_slug_or_404(constructor_slug, db)
    return row._mapping["constructor_id"]


# ---------------------------------------------------------
# 1️⃣ GET /constructors
# Browse constructors with filters
# ---------------------------------------------------------
@router.get("/")
def list_constructors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    nationality: str | None = None,
    season: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve constructors with optional filters:
    - q
    - nationality
    - season
    """

    if season is not None:
        ensure_season_exists(season, db)

    sql = """
    SELECT DISTINCT
        c.constructor_id,
        c.name,
        c.nationality
    FROM constructors c
    LEFT JOIN results r ON r.constructor_id = c.constructor_id
    LEFT JOIN races ra ON ra.race_id = r.race_id
    WHERE (:q IS NULL OR c.name ILIKE :q_like)
      AND (:nationality IS NULL OR c.nationality ILIKE :nationality_like)
      AND (:season IS NULL OR ra.year = :season)
    ORDER BY c.name
    LIMIT :limit OFFSET :offset;
    """

    params = {
        "limit": limit,
        "offset": offset,
        "q": q,
        "q_like": f"%{q}%" if q else None,
        "nationality": nationality,
        "nationality_like": f"%{nationality}%" if nationality else None,
        "season": season,
    }

    rows = db.execute(text(sql), params).fetchall()
    data = [add_constructor_slug(dict(row._mapping)) for row in rows]

    return {
        "limit": limit,
        "offset": offset,
        "count": len(data),
        "filters": {
            "q": q,
            "nationality": nationality,
            "season": season,
        },
        "data": data,
    }


# ---------------------------------------------------------
# 2️⃣ POST /constructors
# Create a new constructor (admin only)
# ---------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_constructor(
    payload: ConstructorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Create a new constructor.
    Admin only.
    """

    new_constructor_id = db.execute(
        text("SELECT COALESCE(MAX(constructor_id), 0) + 1 AS next_id FROM constructors")
    ).scalar()

    row = db.execute(
        text("""
            INSERT INTO constructors (constructor_id, name, nationality)
            VALUES (:constructor_id, :name, :nationality)
            RETURNING constructor_id, name, nationality
        """),
        {
            "constructor_id": new_constructor_id,
            "name": payload.name,
            "nationality": payload.nationality,
        },
    ).fetchone()

    db.commit()

    data = add_constructor_slug(dict(row._mapping))

    return {
        "message": "Constructor created successfully",
        "data": data,
    }


# ---------------------------------------------------------
# 3️⃣ GET /constructors/current
# Returns constructors who participated in the latest season
# ---------------------------------------------------------
@router.get("/current")
def current_constructors(db: Session = Depends(get_db)):
    """
    Retrieve constructors who participated in the most recent season.
    """

    latest_year = db.execute(text("SELECT MAX(year) FROM races")).scalar()

    if latest_year is None:
        raise HTTPException(status_code=404, detail="No seasons found")

    sql = """
    SELECT DISTINCT
        c.constructor_id,
        c.name,
        c.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN constructors c ON c.constructor_id = r.constructor_id
    WHERE ra.year = :year
    ORDER BY c.name;
    """

    rows = db.execute(text(sql), {"year": latest_year}).fetchall()
    data = [add_constructor_slug(dict(row._mapping)) for row in rows]

    return {
        "season": latest_year,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 4️⃣ GET /constructors/season/{year}
# Returns constructors who participated in a specific season
# ---------------------------------------------------------
@router.get("/season/{year}")
def constructors_by_season(year: int, db: Session = Depends(get_db)):
    """
    Retrieve constructors who participated in a specific season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT DISTINCT
        c.constructor_id,
        c.name,
        c.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN constructors c ON c.constructor_id = r.constructor_id
    WHERE ra.year = :year
    ORDER BY c.name;
    """

    rows = db.execute(text(sql), {"year": year}).fetchall()
    data = [add_constructor_slug(dict(row._mapping)) for row in rows]

    return {
        "season": year,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 5️⃣ GET /constructors/standings/{year}
# Returns constructor standings for a given season
# Optional: round
# ---------------------------------------------------------
@router.get("/standings/{year}")
def constructor_standings(
    year: int,
    round: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    """
    Retrieve constructor standings for a given season.

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
        c.constructor_id,
        c.name,
        c.nationality,
        SUM(r.points) AS points,
        SUM(CASE WHEN r.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN r.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        COUNT(r.result_id) AS race_entries
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN constructors c ON c.constructor_id = r.constructor_id
    WHERE ra.year = :year
      AND (:round IS NULL OR ra.round <= :round)
    GROUP BY c.constructor_id, c.name, c.nationality
    ORDER BY points DESC, wins DESC, podiums DESC, c.name ASC;
    """

    rows = db.execute(
        text(sql),
        {"year": year, "round": round},
    ).fetchall()

    data = []
    for idx, row in enumerate(rows, start=1):
        item = add_constructor_slug(dict(row._mapping))
        item["position"] = idx
        data.append(item)

    return {
        "season": year,
        "round": round,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 6️⃣ GET /constructors/{constructor_slug}
# Returns a single constructor by slug
# ---------------------------------------------------------
@router.get("/{constructor_slug}")
def get_constructor(constructor_slug: str, db: Session = Depends(get_db)):
    """
    Retrieve a single constructor by slug.
    """

    row = get_constructor_row_by_slug_or_404(constructor_slug, db)
    data = add_constructor_slug(dict(row._mapping))
    return data


# ---------------------------------------------------------
# 7️⃣ GET /constructors/{constructor_slug}/stats
# Career or season-specific summary
# ---------------------------------------------------------
@router.get("/{constructor_slug}/stats")
def constructor_stats(
    constructor_slug: str,
    year: int | None = Query(None, ge=1950),
    round: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    """
    Retrieve statistics for a constructor.

    Options:
    - no params -> full career stats
    - year -> season stats
    - year + round -> stats up to that round
    """

    constructor_id = get_constructor_id_by_slug(constructor_slug, db)

    if year is not None:
        ensure_season_exists(year, db)

    if round is not None and year is None:
        raise HTTPException(
            status_code=400,
            detail="Round filter requires a year parameter",
        )

    sql = """
    SELECT
        c.constructor_id,
        c.name,
        c.nationality,
        COUNT(r.result_id) AS race_entries,
        COALESCE(SUM(r.points), 0) AS total_points,
        SUM(CASE WHEN r.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN r.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_season,
        MAX(ra.year) AS last_season,
        MIN(CASE WHEN r.position_order > 0 THEN r.position_order END) AS best_finish
    FROM constructors c
    LEFT JOIN results r ON c.constructor_id = r.constructor_id
    LEFT JOIN races ra ON ra.race_id = r.race_id
    WHERE c.constructor_id = :constructor_id
      AND (:year IS NULL OR ra.year = :year)
      AND (:round IS NULL OR ra.round <= :round)
    GROUP BY c.constructor_id, c.name, c.nationality;
    """

    row = db.execute(
        text(sql),
        {
            "constructor_id": constructor_id,
            "year": year,
            "round": round,
        },
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Constructor stats not found")

    data = add_constructor_slug(dict(row._mapping))

    return {
        "season": year,
        "round": round,
        "data": data,
    }


# ---------------------------------------------------------
# 8️⃣ GET /constructors/{constructor_slug}/drivers
# Returns drivers who raced for this constructor
# Optional: year
# ---------------------------------------------------------
@router.get("/{constructor_slug}/drivers")
def constructor_drivers(
    constructor_slug: str,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve drivers who raced for a constructor.

    Optional:
    - year: restrict to a single season
    """

    constructor_id = get_constructor_id_by_slug(constructor_slug, db)

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        MIN(ra.year) AS first_season,
        MAX(ra.year) AS last_season,
        COUNT(r.result_id) AS race_entries,
        COALESCE(SUM(r.points), 0) AS total_points,
        SUM(CASE WHEN r.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN r.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN drivers d ON d.driver_id = r.driver_id
    WHERE r.constructor_id = :constructor_id
      AND (:year IS NULL OR ra.year = :year)
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality
    ORDER BY total_points DESC, wins DESC, d.surname ASC, d.forename ASC;
    """

    rows = db.execute(
        text(sql),
        {"constructor_id": constructor_id, "year": year},
    ).fetchall()

    return {
        "constructor_slug": constructor_slug,
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 9️⃣ GET /constructors/{constructor_slug}/seasons
# Season-by-season performance progression
# ---------------------------------------------------------
@router.get("/{constructor_slug}/seasons")
def constructor_seasons(constructor_slug: str, db: Session = Depends(get_db)):
    """
    Retrieve all seasons in which a constructor competed.
    """

    constructor_id = get_constructor_id_by_slug(constructor_slug, db)

    sql = """
    SELECT
        ra.year,
        COUNT(r.result_id) AS race_entries,
        COALESCE(SUM(r.points), 0) AS total_points,
        SUM(CASE WHEN r.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN r.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    WHERE r.constructor_id = :constructor_id
    GROUP BY ra.year
    ORDER BY ra.year;
    """

    rows = db.execute(
        text(sql),
        {"constructor_id": constructor_id},
    ).fetchall()

    return {
        "constructor_slug": constructor_slug,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 🔟 GET /constructors/{constructor_slug}/best-circuits
# Top circuits for a constructor
# ---------------------------------------------------------
@router.get("/{constructor_slug}/best-circuits")
def constructor_best_circuits(
    constructor_slug: str,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Retrieve the best circuits for a constructor,
    ranked by wins, podiums, then points.
    """

    constructor_id = get_constructor_id_by_slug(constructor_slug, db)

    sql = """
    SELECT
        ci.circuit_id,
        ci.name AS circuit_name,
        ci.location,
        ci.country,
        COUNT(r.result_id) AS race_entries,
        COALESCE(SUM(r.points), 0) AS total_points,
        SUM(CASE WHEN r.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN r.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_year,
        MAX(ra.year) AS last_year
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN circuits ci ON ci.circuit_id = ra.circuit_id
    WHERE r.constructor_id = :constructor_id
    GROUP BY ci.circuit_id, ci.name, ci.location, ci.country
    ORDER BY wins DESC, podiums DESC, total_points DESC, circuit_name
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"constructor_id": constructor_id, "limit": limit},
    ).fetchall()

    return {
        "constructor_slug": constructor_slug,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 1️⃣1️⃣ GET /constructors/{constructor_slug}/dnfs
# DNF / non-finish analysis using status
# ---------------------------------------------------------
@router.get("/{constructor_slug}/dnfs")
def constructor_dnfs(
    constructor_slug: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve DNF / non-finish analysis for a constructor.
    """

    constructor_id = get_constructor_id_by_slug(constructor_slug, db)

    summary_sql = """
    SELECT
        COUNT(*) AS total_non_finishes
    FROM results r
    JOIN status s ON s.status_id = r.status_id
    WHERE r.constructor_id = :constructor_id
      AND s.status NOT ILIKE '%finished%';
    """

    breakdown_sql = """
    SELECT
        s.status,
        COUNT(*) AS count
    FROM results r
    JOIN status s ON s.status_id = r.status_id
    WHERE r.constructor_id = :constructor_id
      AND s.status NOT ILIKE '%finished%'
    GROUP BY s.status
    ORDER BY count DESC, s.status;
    """

    seasonal_sql = """
    SELECT
        ra.year,
        COUNT(r.result_id) AS race_entries,
        SUM(CASE WHEN s.status NOT ILIKE '%finished%' THEN 1 ELSE 0 END) AS non_finishes,
        ROUND(
            100.0 * SUM(CASE WHEN s.status NOT ILIKE '%finished%' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(r.result_id), 0),
            2
        ) AS dnf_rate_percent
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN status s ON s.status_id = r.status_id
    WHERE r.constructor_id = :constructor_id
    GROUP BY ra.year
    ORDER BY ra.year;
    """

    summary = db.execute(text(summary_sql), {"constructor_id": constructor_id}).fetchone()
    breakdown = db.execute(text(breakdown_sql), {"constructor_id": constructor_id}).fetchall()
    seasonal = db.execute(text(seasonal_sql), {"constructor_id": constructor_id}).fetchall()

    return {
        "constructor_slug": constructor_slug,
        "total_non_finishes": summary._mapping["total_non_finishes"] if summary else 0,
        "breakdown_by_status": [dict(row._mapping) for row in breakdown],
        "dnf_rate_by_season": [dict(row._mapping) for row in seasonal],
    }


# ---------------------------------------------------------
# 1️⃣2️⃣ PATCH /constructors/{constructor_slug}
# Update an existing constructor (admin only)
# ---------------------------------------------------------
@router.patch("/{constructor_slug}")
def update_constructor(
    constructor_slug: str,
    payload: ConstructorUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Update a constructor.
    Admin only.
    """

    constructor_row = get_constructor_row_by_slug_or_404(constructor_slug, db)
    constructor_id = constructor_row._mapping["constructor_id"]

    existing = db.execute(
        text("""
            SELECT constructor_id, name, nationality
            FROM constructors
            WHERE constructor_id = :constructor_id
        """),
        {"constructor_id": constructor_id},
    ).fetchone()

    existing_data = dict(existing._mapping)

    updated_data = {
        "constructor_id": constructor_id,
        "name": payload.name if payload.name is not None else existing_data["name"],
        "nationality": payload.nationality if payload.nationality is not None else existing_data["nationality"],
    }

    row = db.execute(
        text("""
            UPDATE constructors
            SET name = :name,
                nationality = :nationality
            WHERE constructor_id = :constructor_id
            RETURNING constructor_id, name, nationality
        """),
        updated_data,
    ).fetchone()

    db.commit()

    data = add_constructor_slug(dict(row._mapping))

    return {
        "message": "Constructor updated successfully",
        "data": data,
    }


# ---------------------------------------------------------
# 1️⃣3️⃣ DELETE /constructors/{constructor_slug}
# Delete a constructor (admin only)
# ---------------------------------------------------------
@router.delete("/{constructor_slug}")
def delete_constructor(
    constructor_slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Delete a constructor.
    Admin only.

    Prevent deletion if related race results exist.
    """

    constructor_row = get_constructor_row_by_slug_or_404(constructor_slug, db)
    constructor_id = constructor_row._mapping["constructor_id"]

    dependency_count = db.execute(
        text("SELECT COUNT(*) FROM results WHERE constructor_id = :constructor_id"),
        {"constructor_id": constructor_id},
    ).scalar()

    if dependency_count and dependency_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete constructor because related race results exist",
        )

    db.execute(
        text("DELETE FROM constructors WHERE constructor_id = :constructor_id"),
        {"constructor_id": constructor_id},
    )
    db.commit()

    return {
        "message": "Constructor deleted successfully",
        "constructor_slug": constructor_slug,
    }
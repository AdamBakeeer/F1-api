from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
router = APIRouter(prefix="/constructors", tags=["Constructors"])


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def ensure_constructor_exists(constructor_id: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM constructors WHERE constructor_id = :constructor_id LIMIT 1"),
        {"constructor_id": constructor_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Constructor not found")


def ensure_season_exists(year: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE year = :year LIMIT 1"),
        {"year": year},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")


# ---------------------------------------------------------
# 1️⃣ GET /constructors
# Returns all constructors with optional filtering
# ---------------------------------------------------------
@router.get("/")
def list_constructors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    nationality: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve all constructors.

    Optional:
    - limit / offset for pagination
    - nationality filter
    - q search by constructor name
    """

    sql = """
    SELECT constructor_id, name, nationality
    FROM constructors
    WHERE (:nationality IS NULL OR nationality ILIKE :nationality_like)
      AND (:q IS NULL OR name ILIKE :q_like)
    ORDER BY name
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
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 2️⃣ GET /constructors/current
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
    SELECT DISTINCT c.constructor_id, c.name, c.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN constructors c ON c.constructor_id = r.constructor_id
    WHERE ra.year = :year
    ORDER BY c.name;
    """

    rows = db.execute(text(sql), {"year": latest_year}).fetchall()

    return {
        "season": latest_year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 3️⃣ GET /constructors/season/{year}
# Returns constructors who participated in a specific season
# ---------------------------------------------------------
@router.get("/season/{year}")
def constructors_by_season(year: int, db: Session = Depends(get_db)):
    """
    Retrieve constructors who participated in a specific season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT DISTINCT c.constructor_id, c.name, c.nationality
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    JOIN constructors c ON c.constructor_id = r.constructor_id
    WHERE ra.year = :year
    ORDER BY c.name;
    """

    rows = db.execute(text(sql), {"year": year}).fetchall()

    return {
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 4️⃣ GET /constructors/standings/{year}
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
        item = dict(row._mapping)
        item["position"] = idx
        data.append(item)

    return {
        "season": year,
        "round": round,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 5️⃣ GET /constructors/{constructor_id}/stats
# Career or season-specific summary
# ---------------------------------------------------------
@router.get("/{constructor_id}/stats")
def constructor_stats(
    constructor_id: int,
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

    ensure_constructor_exists(constructor_id, db)

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

    return {
        "season": year,
        "round": round,
        "data": dict(row._mapping),
    }


# ---------------------------------------------------------
# 6️⃣ GET /constructors/{constructor_id}/drivers
# Returns drivers who raced for this constructor
# Optional: year
# ---------------------------------------------------------
@router.get("/{constructor_id}/drivers")
def constructor_drivers(
    constructor_id: int,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve drivers who raced for a constructor.

    Optional:
    - year: restrict to a single season
    """

    ensure_constructor_exists(constructor_id, db)

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
        "constructor_id": constructor_id,
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 7️⃣ GET /constructors/{constructor_id}/seasons
# Season-by-season performance progression
# ---------------------------------------------------------
@router.get("/{constructor_id}/seasons")
def constructor_seasons(constructor_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all seasons in which a constructor competed.
    """

    ensure_constructor_exists(constructor_id, db)

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
        "constructor_id": constructor_id,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 8️⃣ GET /constructors/{constructor_id}
# Returns a single constructor by ID
# ---------------------------------------------------------
@router.get("/{constructor_id}")
def get_constructor(constructor_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single constructor by ID.
    """

    sql = """
    SELECT constructor_id, name, nationality
    FROM constructors
    WHERE constructor_id = :constructor_id;
    """

    row = db.execute(
        text(sql),
        {"constructor_id": constructor_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Constructor not found")

    return dict(row._mapping)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
router = APIRouter(prefix="/races", tags=["Races"])


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def ensure_race_exists(race_id: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE race_id = :race_id LIMIT 1"),
        {"race_id": race_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Race not found")


def ensure_season_exists(year: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE year = :year LIMIT 1"),
        {"year": year},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")


# ---------------------------------------------------------
# 1️⃣ GET /races
# Returns all races with optional filtering
# ---------------------------------------------------------
@router.get("/")
def list_races(
    year: int | None = Query(None, ge=1950),
    circuit_id: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retrieve all races.

    Optional:
    - year
    - circuit_id
    - limit / offset
    """

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        r.race_id,
        r.year,
        r.round,
        r.name,
        r.date,
        r.time,
        c.circuit_id,
        c.name AS circuit_name,
        c.location,
        c.country
    FROM races r
    JOIN circuits c ON c.circuit_id = r.circuit_id
    WHERE (:year IS NULL OR r.year = :year)
      AND (:circuit_id IS NULL OR r.circuit_id = :circuit_id)
    ORDER BY r.year DESC, r.round ASC
    LIMIT :limit OFFSET :offset;
    """

    rows = db.execute(
        text(sql),
        {
            "year": year,
            "circuit_id": circuit_id,
            "limit": limit,
            "offset": offset,
        },
    ).fetchall()

    return {
        "year": year,
        "circuit_id": circuit_id,
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 2️⃣ GET /races/current
# Returns races from the latest season
# ---------------------------------------------------------
@router.get("/current")
def current_races(db: Session = Depends(get_db)):
    """
    Retrieve races from the most recent season.
    """

    latest_year = db.execute(text("SELECT MAX(year) FROM races")).scalar()

    if latest_year is None:
        raise HTTPException(status_code=404, detail="No seasons found")

    sql = """
    SELECT
        r.race_id,
        r.year,
        r.round,
        r.name,
        r.date,
        r.time,
        c.circuit_id,
        c.name AS circuit_name,
        c.location,
        c.country
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
# 3️⃣ GET /races/season/{year}
# Returns races from a specific season
# ---------------------------------------------------------
@router.get("/season/{year}")
def races_by_season(year: int, db: Session = Depends(get_db)):
    """
    Retrieve races from a specific season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT
        r.race_id,
        r.year,
        r.round,
        r.name,
        r.date,
        r.time,
        c.circuit_id,
        c.name AS circuit_name,
        c.location,
        c.country
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
# 4️⃣ GET /races/season/{year}/calendar
# Returns a season calendar ordered by round
# ---------------------------------------------------------
@router.get("/season/{year}/calendar")
def season_calendar(year: int, db: Session = Depends(get_db)):
    """
    Retrieve the race calendar for a season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT
        r.race_id,
        r.round,
        r.name AS race_name,
        r.date,
        r.time,
        c.circuit_id,
        c.name AS circuit_name,
        c.location,
        c.country
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
# 5️⃣ GET /races/season/{year}/winners
# Returns winners for each race in a season
# ---------------------------------------------------------
@router.get("/season/{year}/winners")
def season_winners(year: int, db: Session = Depends(get_db)):
    """
    Retrieve race winners for a given season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT
        ra.race_id,
        ra.round,
        ra.name AS race_name,
        ra.date,
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
    WHERE ra.year = :year
      AND res.position_order = 1
    ORDER BY ra.round;
    """

    rows = db.execute(text(sql), {"year": year}).fetchall()

    return {
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 6️⃣ GET /races/{race_id}/results
# Full classified race results
# ---------------------------------------------------------
@router.get("/{race_id}/results")
def race_results(race_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full race results for a race.
    """

    ensure_race_exists(race_id, db)

    sql = """
    SELECT
        res.result_id,
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        c.constructor_id,
        c.name AS constructor_name,
        res.grid,
        res.position_order,
        res.points,
        res.laps,
        res.milliseconds,
        s.status
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    JOIN status s ON s.status_id = res.status_id
    WHERE res.race_id = :race_id
    ORDER BY
        CASE WHEN res.position_order IS NULL OR res.position_order = 0 THEN 9999 ELSE res.position_order END,
        d.surname,
        d.forename;
    """

    rows = db.execute(text(sql), {"race_id": race_id}).fetchall()

    return {
        "race_id": race_id,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 7️⃣ GET /races/{race_id}/podium
# Top 3 finishers
# ---------------------------------------------------------
@router.get("/{race_id}/podium")
def race_podium(race_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the podium finishers for a race.
    """

    ensure_race_exists(race_id, db)

    sql = """
    SELECT
        res.position_order,
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        c.constructor_id,
        c.name AS constructor_name,
        res.points,
        res.grid,
        s.status
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    JOIN status s ON s.status_id = res.status_id
    WHERE res.race_id = :race_id
      AND res.position_order IN (1, 2, 3)
    ORDER BY res.position_order;
    """

    rows = db.execute(text(sql), {"race_id": race_id}).fetchall()

    return {
        "race_id": race_id,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 8️⃣ GET /races/{race_id}/fast-summary
# Compact summary of a race
# ---------------------------------------------------------
@router.get("/{race_id}/fast-summary")
def race_fast_summary(race_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a compact summary of a race including winner,
    podium count, finishers, and non-finishers.
    """

    ensure_race_exists(race_id, db)

    race_sql = """
    SELECT
        r.race_id,
        r.year,
        r.round,
        r.name AS race_name,
        r.date,
        r.time,
        c.circuit_id,
        c.name AS circuit_name,
        c.location,
        c.country
    FROM races r
    JOIN circuits c ON c.circuit_id = r.circuit_id
    WHERE r.race_id = :race_id;
    """

    winner_sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        con.constructor_id,
        con.name AS constructor_name
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN constructors con ON con.constructor_id = res.constructor_id
    WHERE res.race_id = :race_id
      AND res.position_order = 1
    LIMIT 1;
    """

    counts_sql = """
    SELECT
        COUNT(*) AS total_classified_rows,
        SUM(CASE WHEN s.status ILIKE 'Finished' OR s.status LIKE '+%' THEN 1 ELSE 0 END) AS finishers_like,
        SUM(CASE WHEN NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%') THEN 1 ELSE 0 END) AS non_finishers
    FROM results res
    JOIN status s ON s.status_id = res.status_id
    WHERE res.race_id = :race_id;
    """

    race_row = db.execute(text(race_sql), {"race_id": race_id}).fetchone()
    winner_row = db.execute(text(winner_sql), {"race_id": race_id}).fetchone()
    counts_row = db.execute(text(counts_sql), {"race_id": race_id}).fetchone()

    return {
        "race": dict(race_row._mapping) if race_row else None,
        "winner": dict(winner_row._mapping) if winner_row else None,
        "summary": dict(counts_row._mapping) if counts_row else None,
    }


# ---------------------------------------------------------
# 9️⃣ GET /races/{race_id}/dnfs
# DNF / non-finish analysis for a race
# ---------------------------------------------------------
@router.get("/{race_id}/dnfs")
def race_dnfs(race_id: int, db: Session = Depends(get_db)):
    """
    Retrieve non-finishers and status breakdown for a race.
    """

    ensure_race_exists(race_id, db)

    details_sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        c.constructor_id,
        c.name AS constructor_name,
        s.status
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    JOIN status s ON s.status_id = res.status_id
    WHERE res.race_id = :race_id
      AND NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%')
    ORDER BY d.surname, d.forename;
    """

    breakdown_sql = """
    SELECT
        s.status,
        COUNT(*) AS count
    FROM results res
    JOIN status s ON s.status_id = res.status_id
    WHERE res.race_id = :race_id
      AND NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%')
    GROUP BY s.status
    ORDER BY count DESC, s.status;
    """

    detail_rows = db.execute(text(details_sql), {"race_id": race_id}).fetchall()
    breakdown_rows = db.execute(text(breakdown_sql), {"race_id": race_id}).fetchall()

    return {
        "race_id": race_id,
        "non_finishers_count": len(detail_rows),
        "non_finishers": [dict(row._mapping) for row in detail_rows],
        "breakdown_by_status": [dict(row._mapping) for row in breakdown_rows],
    }


# ---------------------------------------------------------
# 🔟 GET /races/{race_id}
# Returns a single race by ID
# ---------------------------------------------------------
@router.get("/{race_id}")
def get_race(race_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single race by ID.
    """

    sql = """
    SELECT
        r.race_id,
        r.year,
        r.round,
        r.name,
        r.date,
        r.time,
        c.circuit_id,
        c.name AS circuit_name,
        c.location,
        c.country
    FROM races r
    JOIN circuits c ON c.circuit_id = r.circuit_id
    WHERE r.race_id = :race_id;
    """

    row = db.execute(text(sql), {"race_id": race_id}).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Race not found")

    return dict(row._mapping)
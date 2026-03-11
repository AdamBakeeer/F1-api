from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
router = APIRouter(prefix="/drivers", tags=["Drivers"])


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def ensure_driver_exists(driver_id: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM drivers WHERE driver_id = :driver_id LIMIT 1"),
        {"driver_id": driver_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Driver not found")


def ensure_season_exists(year: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE year = :year LIMIT 1"),
        {"year": year},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")


def ensure_constructor_exists(constructor_id: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM constructors WHERE constructor_id = :constructor_id LIMIT 1"),
        {"constructor_id": constructor_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Constructor not found")


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

    latest_year = db.execute(text("SELECT MAX(year) FROM races")).scalar()

    if latest_year is None:
        raise HTTPException(status_code=404, detail="No seasons found")

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

    ensure_season_exists(year, db)

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
# 4️⃣ GET /drivers/standings/{year}
# Returns driver standings for a given season
# Optional: round, pagination
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
    - limit / offset: pagination
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
    ORDER BY points DESC, wins DESC, podiums DESC, surname ASC, forename ASC
    LIMIT :limit OFFSET :offset;
    """

    rows = db.execute(
        text(sql),
        {
            "year": year,
            "round": round,
            "limit": limit,
            "offset": offset,
        },
    ).fetchall()

    data = []
    for idx, row in enumerate(rows, start=offset + 1):
        item = dict(row._mapping)
        item["position"] = idx
        data.append(item)

    return {
        "season": year,
        "round": round,
        "limit": limit,
        "offset": offset,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 5️⃣ GET /drivers/{driver_id}/stats
# Career or season-specific summary
# ---------------------------------------------------------
@router.get("/{driver_id}/stats")
def driver_stats(
    driver_id: int,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve career statistics for a driver.

    Optional:
    - year: restrict stats to a single season
    """

    ensure_driver_exists(driver_id, db)

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

    return {
        "season": year,
        "data": data,
    }


# ---------------------------------------------------------
# 6️⃣ GET /drivers/{driver_id}/results
# Full race-by-race results for a driver
# ---------------------------------------------------------
@router.get("/{driver_id}/results")
def driver_results(
    driver_id: int,
    year: int | None = Query(None, ge=1950),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retrieve race-by-race results for a driver.

    Optional:
    - year
    - limit / offset
    """

    ensure_driver_exists(driver_id, db)

    if year is not None:
        ensure_season_exists(year, db)

    sql = """
    SELECT
        r.result_id,
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
    JOIN drivers r ON r.driver_id = res.driver_id
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
        "driver_id": driver_id,
        "season": year,
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 7️⃣ GET /drivers/{driver_id}/seasons
# Season-by-season performance progression
# ---------------------------------------------------------
@router.get("/{driver_id}/seasons")
def driver_seasons(driver_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all seasons in which a driver competed.
    """

    ensure_driver_exists(driver_id, db)

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
        "driver_id": driver_id,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 8️⃣ GET /drivers/{driver_id}/teams
# Constructors raced for by the driver
# Optional filter by year
# ---------------------------------------------------------
@router.get("/{driver_id}/teams")
def driver_teams(
    driver_id: int,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve constructors a driver raced for.

    Optional:
    - year: restrict to a single season
    """

    ensure_driver_exists(driver_id, db)

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
        "driver_id": driver_id,
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 9️⃣ GET /drivers/{driver_id}/teammates
# Drivers who shared the same constructor in the same race
# Optional filter by year
# ---------------------------------------------------------
@router.get("/{driver_id}/teammates")
def driver_teammates(
    driver_id: int,
    year: int | None = Query(None, ge=1950),
    db: Session = Depends(get_db),
):
    """
    Retrieve teammates of a driver.

    Optional:
    - year: restrict to a single season
    """

    ensure_driver_exists(driver_id, db)

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
        "driver_id": driver_id,
        "season": year,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 🔟 GET /drivers/{driver_id}/constructors/{constructor_id}/stats
# Driver performance for one constructor
# ---------------------------------------------------------
@router.get("/{driver_id}/constructors/{constructor_id}/stats")
def driver_constructor_stats(
    driver_id: int,
    constructor_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a driver's performance statistics for a specific constructor.
    """

    ensure_driver_exists(driver_id, db)
    ensure_constructor_exists(constructor_id, db)

    sql = """
    SELECT
        d.driver_id,
        d.forename,
        d.surname,
        c.constructor_id,
        c.name AS constructor_name,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_season,
        MAX(ra.year) AS last_season
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    JOIN races ra ON ra.race_id = res.race_id
    WHERE res.driver_id = :driver_id
      AND res.constructor_id = :constructor_id
    GROUP BY d.driver_id, d.forename, d.surname, c.constructor_id, c.name;
    """

    row = db.execute(
        text(sql),
        {"driver_id": driver_id, "constructor_id": constructor_id},
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No stats found for this driver-constructor combination",
        )

    return dict(row._mapping)


# ---------------------------------------------------------
# 1️⃣1️⃣ GET /drivers/{driver_id}/circuits
# Driver performance by circuit
# ---------------------------------------------------------
@router.get("/{driver_id}/circuits")
def driver_circuits(
    driver_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve driver performance statistics by circuit.
    """

    ensure_driver_exists(driver_id, db)

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
    ORDER BY wins DESC, podiums DESC, total_points DESC, circuit_name;
    """

    rows = db.execute(text(sql), {"driver_id": driver_id}).fetchall()

    return {
        "driver_id": driver_id,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 1️⃣2️⃣ GET /drivers/{driver_id}/dnfs
# DNF / non-finish analysis using status
# ---------------------------------------------------------
@router.get("/{driver_id}/dnfs")
def driver_dnfs(
    driver_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve DNF / non-finish analysis for a driver.
    """

    ensure_driver_exists(driver_id, db)

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
        "driver_id": driver_id,
        "total_non_finishes": summary._mapping["total_non_finishes"] if summary else 0,
        "breakdown_by_status": [dict(row._mapping) for row in breakdown],
        "dnf_rate_by_season": [dict(row._mapping) for row in seasonal],
    }


# ---------------------------------------------------------
# 1️⃣3️⃣ GET /drivers/{driver_id}/rivals
# Compare a driver with others they raced against often
# ---------------------------------------------------------
@router.get("/{driver_id}/rivals")
def driver_rivals(
    driver_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Retrieve common rivals for a driver based on shared races.
    """

    ensure_driver_exists(driver_id, db)

    sql = """
    WITH target AS (
        SELECT
            res.race_id,
            res.driver_id,
            res.position_order,
            res.points
        FROM results res
        WHERE res.driver_id = :driver_id
    ),
    rivals AS (
        SELECT
            d2.driver_id AS rival_id,
            d2.code AS rival_code,
            d2.forename AS rival_forename,
            d2.surname AS rival_surname,
            COUNT(*) AS shared_races,
            SUM(CASE WHEN t.position_order > 0 AND r2.position_order > 0 AND t.position_order < r2.position_order THEN 1 ELSE 0 END) AS target_ahead_finishes,
            SUM(CASE WHEN t.position_order > 0 AND r2.position_order > 0 AND t.position_order > r2.position_order THEN 1 ELSE 0 END) AS rival_ahead_finishes,
            SUM(t.points) AS target_points_in_shared_races,
            SUM(r2.points) AS rival_points_in_shared_races,
            SUM(CASE WHEN r2.position_order = 1 THEN 1 ELSE 0 END) AS rival_wins_in_shared_races,
            SUM(CASE WHEN r2.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS rival_podiums_in_shared_races
        FROM target t
        JOIN results r2
            ON t.race_id = r2.race_id
           AND r2.driver_id <> :driver_id
        JOIN drivers d2 ON d2.driver_id = r2.driver_id
        GROUP BY d2.driver_id, d2.code, d2.forename, d2.surname
    )
    SELECT
        rival_id,
        rival_code,
        rival_forename,
        rival_surname,
        shared_races,
        target_ahead_finishes,
        rival_ahead_finishes,
        target_points_in_shared_races,
        rival_points_in_shared_races,
        rival_wins_in_shared_races,
        rival_podiums_in_shared_races
    FROM rivals
    ORDER BY shared_races DESC, rival_points_in_shared_races DESC, rival_surname, rival_forename
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"driver_id": driver_id, "limit": limit},
    ).fetchall()

    return {
        "driver_id": driver_id,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 1️⃣4️⃣ GET /drivers/{driver_id}
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
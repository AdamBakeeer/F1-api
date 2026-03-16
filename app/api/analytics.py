from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

# ---------------------------------------------------------
# Router configuration
# ---------------------------------------------------------
router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def ensure_season_exists(year: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM races WHERE year = :year LIMIT 1"),
        {"year": year},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Season not found")


# ---------------------------------------------------------
# 1️⃣ GET /analytics/dnfs/by-season
# Non-finish trends by season
# ---------------------------------------------------------
@router.get("/dnfs/by-season")
def dnfs_by_season(db: Session = Depends(get_db)):
    """
    Retrieve DNF / non-finish trends by season.
    """

    sql = """
    SELECT
        ra.year,
        COUNT(res.result_id) AS total_results,
        SUM(
            CASE
                WHEN NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%')
                THEN 1 ELSE 0
            END
        ) AS non_finishes,
        ROUND(
            100.0 * SUM(
                CASE
                    WHEN NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%')
                    THEN 1 ELSE 0
                END
            ) / NULLIF(COUNT(res.result_id), 0),
            2
        ) AS dnf_rate_percent
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    JOIN status s ON s.status_id = res.status_id
    GROUP BY ra.year
    ORDER BY ra.year;
    """

    rows = db.execute(text(sql)).fetchall()

    return {
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 2️⃣ GET /analytics/most-successful-drivers
# All-time driver leaderboard
# ---------------------------------------------------------
@router.get("/most-successful-drivers")
def most_successful_drivers(
    metric: str = Query("wins", pattern="^(wins|podiums|points)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Retrieve the most successful drivers of all time.

    Sort options:
    - wins
    - podiums
    - points
    """

    order_map = {
        "wins": "wins DESC, podiums DESC, total_points DESC",
        "podiums": "podiums DESC, wins DESC, total_points DESC",
        "points": "total_points DESC, wins DESC, podiums DESC",
    }

    sql = f"""
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
        MIN(ra.year) AS first_season,
        MAX(ra.year) AS last_season
    FROM drivers d
    JOIN results res ON res.driver_id = d.driver_id
    JOIN races ra ON ra.race_id = res.race_id
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality
    ORDER BY {order_map[metric]}, d.surname, d.forename
    LIMIT :limit;
    """

    rows = db.execute(text(sql), {"limit": limit}).fetchall()

    return {
        "metric": metric,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 3️⃣ GET /analytics/most-successful-constructors
# All-time constructor leaderboard
# ---------------------------------------------------------
@router.get("/most-successful-constructors")
def most_successful_constructors(
    metric: str = Query("wins", pattern="^(wins|podiums|points)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Retrieve the most successful constructors of all time.

    Sort options:
    - wins
    - podiums
    - points
    """

    order_map = {
        "wins": "wins DESC, podiums DESC, total_points DESC",
        "podiums": "podiums DESC, wins DESC, total_points DESC",
        "points": "total_points DESC, wins DESC, podiums DESC",
    }

    sql = f"""
    SELECT
        c.constructor_id,
        c.name AS constructor_name,
        c.nationality,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_season,
        MAX(ra.year) AS last_season
    FROM constructors c
    JOIN results res ON res.constructor_id = c.constructor_id
    JOIN races ra ON ra.race_id = res.race_id
    GROUP BY c.constructor_id, c.name, c.nationality
    ORDER BY {order_map[metric]}, constructor_name
    LIMIT :limit;
    """

    rows = db.execute(text(sql), {"limit": limit}).fetchall()

    return {
        "metric": metric,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 4️⃣ GET /analytics/circuit-specialists
# Best driver-circuit combinations
# ---------------------------------------------------------
@router.get("/circuit-specialists")
def circuit_specialists(
    metric: str = Query("wins", pattern="^(wins|podiums|points)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Retrieve top driver-circuit combinations.

    Sort options:
    - wins
    - podiums
    - points
    """

    order_map = {
        "wins": "wins DESC, podiums DESC, total_points DESC",
        "podiums": "podiums DESC, wins DESC, total_points DESC",
        "points": "total_points DESC, wins DESC, podiums DESC",
    }

    sql = f"""
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        ci.circuit_id,
        ci.name AS circuit_name,
        ci.country,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_year,
        MAX(ra.year) AS last_year
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN races ra ON ra.race_id = res.race_id
    JOIN circuits ci ON ci.circuit_id = ra.circuit_id
    GROUP BY
        d.driver_id, d.code, d.forename, d.surname,
        ci.circuit_id, ci.name, ci.country
    HAVING COUNT(res.result_id) >= 2
    ORDER BY {order_map[metric]}, d.surname, d.forename, circuit_name
    LIMIT :limit;
    """

    rows = db.execute(text(sql), {"limit": limit}).fetchall()

    return {
        "metric": metric,
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 5️⃣ GET /analytics/championship-battles/{year}
# Top title contenders in a given season
# ---------------------------------------------------------
@router.get("/championship-battles/{year}")
def championship_battles(
    year: int,
    top_n: int = Query(2, ge=2, le=5),
    db: Session = Depends(get_db),
):
    """
    Retrieve the top championship contenders for a season.
    """

    ensure_season_exists(year, db)

    sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        COUNT(res.result_id) AS race_entries
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    JOIN drivers d ON d.driver_id = res.driver_id
    WHERE ra.year = :year
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality
    ORDER BY total_points DESC, wins DESC, podiums DESC, d.surname, d.forename
    LIMIT :top_n;
    """

    rows = db.execute(text(sql), {"year": year, "top_n": top_n}).fetchall()
    data = [dict(row._mapping) for row in rows]

    if len(data) >= 2:
        leader_points = data[0]["total_points"]
        for item in data:
            item["points_gap_to_leader"] = leader_points - item["total_points"]

    return {
        "season": year,
        "top_n": top_n,
        "count": len(data),
        "data": data,
    }


# ---------------------------------------------------------
# 6️⃣ GET /analytics/closest-title-fights
# Seasons with the smallest final title gap
# ---------------------------------------------------------
@router.get("/closest-title-fights")
def closest_title_fights(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """
    Retrieve seasons with the closest final title fights.
    """

    sql = """
    WITH yearly_standings AS (
        SELECT
            ra.year,
            d.driver_id,
            d.forename,
            d.surname,
            COALESCE(SUM(res.points), 0) AS total_points,
            ROW_NUMBER() OVER (
                PARTITION BY ra.year
                ORDER BY COALESCE(SUM(res.points), 0) DESC,
                         SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) DESC,
                         SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) DESC,
                         d.surname,
                         d.forename
            ) AS season_rank
        FROM results res
        JOIN races ra ON ra.race_id = res.race_id
        JOIN drivers d ON d.driver_id = res.driver_id
        GROUP BY ra.year, d.driver_id, d.forename, d.surname
    )
    SELECT
        y1.year,
        y1.driver_id AS champion_id,
        y1.forename AS champion_forename,
        y1.surname AS champion_surname,
        y1.total_points AS champion_points,
        y2.driver_id AS runner_up_id,
        y2.forename AS runner_up_forename,
        y2.surname AS runner_up_surname,
        y2.total_points AS runner_up_points,
        (y1.total_points - y2.total_points) AS points_gap
    FROM yearly_standings y1
    JOIN yearly_standings y2
      ON y1.year = y2.year
    WHERE y1.season_rank = 1
      AND y2.season_rank = 2
    ORDER BY points_gap ASC, y1.year DESC
    LIMIT :limit;
    """

    rows = db.execute(text(sql), {"limit": limit}).fetchall()

    return {
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 7️⃣ GET /analytics/driver-consistency
# Consistency-based driver ranking
# ---------------------------------------------------------
@router.get("/driver-consistency")
def driver_consistency(
    limit: int = Query(10, ge=1, le=50),
    min_races: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Retrieve the most consistent drivers based on
    average finish, finish rate, podium rate, and points per race.
    """

    sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        COUNT(res.result_id) AS race_entries,
        ROUND(AVG(CASE WHEN res.position_order > 0 THEN res.position_order END), 2) AS average_finish_position,
        ROUND(
            100.0 * SUM(
                CASE
                    WHEN s.status ILIKE 'Finished' OR s.status LIKE '+%'
                    THEN 1 ELSE 0
                END
            ) / NULLIF(COUNT(res.result_id), 0),
            2
        ) AS finish_rate_percent,
        ROUND(
            100.0 * SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END)
            / NULLIF(COUNT(res.result_id), 0),
            2
        ) AS podium_rate_percent,
        ROUND(COALESCE(SUM(res.points), 0) / NULLIF(COUNT(res.result_id), 0), 2) AS points_per_race
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    JOIN status s ON s.status_id = res.status_id
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality
    HAVING COUNT(res.result_id) >= :min_races
    ORDER BY average_finish_position ASC NULLS LAST,
             finish_rate_percent DESC,
             podium_rate_percent DESC,
             points_per_race DESC,
             d.surname,
             d.forename
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"limit": limit, "min_races": min_races},
    ).fetchall()

    return {
        "limit": limit,
        "min_races": min_races,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 8️⃣ GET /analytics/comeback-drivers
# Drivers who gain the most places on average
# ---------------------------------------------------------
@router.get("/comeback-drivers")
def comeback_drivers(
    limit: int = Query(10, ge=1, le=50),
    min_races: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Retrieve drivers with the best average comeback performance
    based on grid position minus finishing position.
    """

    sql = """
    SELECT
        d.driver_id,
        d.code,
        d.forename,
        d.surname,
        d.nationality,
        COUNT(res.result_id) AS race_entries,
        ROUND(AVG(
            CASE
                WHEN res.grid IS NOT NULL
                 AND res.grid > 0
                 AND res.position_order IS NOT NULL
                 AND res.position_order > 0
                THEN (res.grid - res.position_order)
            END
        ), 2) AS average_positions_gained,
        MAX(
            CASE
                WHEN res.grid IS NOT NULL
                 AND res.grid > 0
                 AND res.position_order IS NOT NULL
                 AND res.position_order > 0
                THEN (res.grid - res.position_order)
            END
        ) AS best_single_race_comeback
    FROM results res
    JOIN drivers d ON d.driver_id = res.driver_id
    GROUP BY d.driver_id, d.code, d.forename, d.surname, d.nationality
    HAVING COUNT(res.result_id) >= :min_races
    ORDER BY average_positions_gained DESC NULLS LAST,
             best_single_race_comeback DESC NULLS LAST,
             d.surname,
             d.forename
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"limit": limit, "min_races": min_races},
    ).fetchall()

    return {
        "limit": limit,
        "min_races": min_races,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 9️⃣ GET /analytics/constructors-by-era
# Constructor performance grouped by era
# ---------------------------------------------------------
@router.get("/constructors-by-era")
def constructors_by_era(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve constructor performance grouped by decade/era.
    """

    sql = """
    SELECT
        CONCAT((ra.year / 10) * 10, 's') AS era,
        c.constructor_id,
        c.name AS constructor_name,
        c.nationality,
        COUNT(res.result_id) AS race_entries,
        COALESCE(SUM(res.points), 0) AS total_points,
        SUM(CASE WHEN res.position_order = 1 THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN res.position_order IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
        MIN(ra.year) AS first_year_in_era,
        MAX(ra.year) AS last_year_in_era
    FROM results res
    JOIN races ra ON ra.race_id = res.race_id
    JOIN constructors c ON c.constructor_id = res.constructor_id
    GROUP BY CONCAT((ra.year / 10) * 10, 's'), c.constructor_id, c.name, c.nationality
    ORDER BY era, total_points DESC, wins DESC, podiums DESC, constructor_name
    LIMIT :limit;
    """

    rows = db.execute(text(sql), {"limit": limit}).fetchall()

    return {
        "limit": limit,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 🔟 GET /analytics/circuit-difficulty
# Hardest circuits based on DNF rate
# ---------------------------------------------------------
@router.get("/circuit-difficulty")
def circuit_difficulty(
    limit: int = Query(10, ge=1, le=50),
    min_races: int = Query(3, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Retrieve circuits ranked by non-finish rate.
    """

    sql = """
    SELECT
        ci.circuit_id,
        ci.name AS circuit_name,
        ci.location,
        ci.country,
        COUNT(DISTINCT ra.race_id) AS races_hosted,
        COUNT(res.result_id) AS total_results,
        SUM(
            CASE
                WHEN NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%')
                THEN 1 ELSE 0
            END
        ) AS non_finishes,
        ROUND(
            100.0 * SUM(
                CASE
                    WHEN NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%')
                    THEN 1 ELSE 0
                END
            ) / NULLIF(COUNT(res.result_id), 0),
            2
        ) AS dnf_rate_percent,
        ROUND(
            AVG(
                CASE
                    WHEN s.status ILIKE 'Finished' OR s.status LIKE '+%'
                    THEN 1 ELSE 0
                END
            ) * 100,
            2
        ) AS finisher_like_rate_percent
    FROM races ra
    JOIN circuits ci ON ci.circuit_id = ra.circuit_id
    JOIN results res ON res.race_id = ra.race_id
    JOIN status s ON s.status_id = res.status_id
    GROUP BY ci.circuit_id, ci.name, ci.location, ci.country
    HAVING COUNT(DISTINCT ra.race_id) >= :min_races
    ORDER BY dnf_rate_percent DESC, non_finishes DESC, circuit_name
    LIMIT :limit;
    """

    rows = db.execute(
        text(sql),
        {"limit": limit, "min_races": min_races},
    ).fetchall()

    return {
        "limit": limit,
        "min_races": min_races,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }
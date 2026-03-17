from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.core.deps import require_admin

router = APIRouter(prefix="/races", tags=["Races"])


# ---------------------------------------------------------
# Schemas for admin CRUD
# ---------------------------------------------------------
class RaceCreate(BaseModel):
    year: int = Field(..., ge=1950)
    round: int = Field(..., ge=1)
    circuit_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=150)
    date: str
    time: str | None = None


class RaceUpdate(BaseModel):
    year: int | None = Field(default=None, ge=1950)
    round: int | None = Field(default=None, ge=1)
    circuit_id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    date: str | None = None
    time: str | None = None


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


def ensure_circuit_exists(circuit_id: int, db: Session) -> None:
    row = db.execute(
        text("SELECT 1 FROM circuits WHERE circuit_id = :circuit_id LIMIT 1"),
        {"circuit_id": circuit_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Circuit not found")


def get_race_row_by_year_round_or_404(year: int, round_num: int, db: Session):
    row = db.execute(
        text("""
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
              AND r.round = :round
            LIMIT 1
        """),
        {"year": year, "round": round_num},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Race not found")

    return row


def get_race_id_by_year_round(year: int, round_num: int, db: Session) -> int:
    row = get_race_row_by_year_round_or_404(year, round_num, db)
    return row._mapping["race_id"]


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
    if year is not None:
        ensure_season_exists(year, db)

    if circuit_id is not None:
        ensure_circuit_exists(circuit_id, db)

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
# 2️⃣ POST /races
# Create a new race (admin only)
# ---------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_race(
    payload: RaceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    ensure_circuit_exists(payload.circuit_id, db)

    new_race_id = db.execute(
        text("SELECT COALESCE(MAX(race_id), 0) + 1 AS next_id FROM races")
    ).scalar()

    row = db.execute(
        text("""
            INSERT INTO races (race_id, year, round, circuit_id, name, date, time)
            VALUES (:race_id, :year, :round, :circuit_id, :name, :date, :time)
            RETURNING race_id, year, round, circuit_id, name, date, time
        """),
        {
            "race_id": new_race_id,
            "year": payload.year,
            "round": payload.round,
            "circuit_id": payload.circuit_id,
            "name": payload.name,
            "date": payload.date,
            "time": payload.time,
        },
    ).fetchone()

    db.commit()

    return {
        "message": "Race created successfully",
        "data": dict(row._mapping),
    }


# ---------------------------------------------------------
# 3️⃣ GET /races/current
# Returns races from the latest season
# ---------------------------------------------------------
@router.get("/current")
def current_races(db: Session = Depends(get_db)):
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
# 4️⃣ GET /races/season/{year}
# Returns races from a specific season
# ---------------------------------------------------------
@router.get("/season/{year}")
def races_by_season(year: int, db: Session = Depends(get_db)):
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
# 5️⃣ GET /races/season/{year}/calendar
# Returns a season calendar ordered by round
# ---------------------------------------------------------
@router.get("/season/{year}/calendar")
def season_calendar(year: int, db: Session = Depends(get_db)):
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
# 6️⃣ GET /races/season/{year}/winners
# Returns winners for each race in a season
# ---------------------------------------------------------
@router.get("/season/{year}/winners")
def season_winners(year: int, db: Session = Depends(get_db)):
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
# 7️⃣ GET /races/{year}/{round}
# Returns a single race by year + round
# ---------------------------------------------------------
@router.get("/{year}/{round}")
def get_race(year: int, round: int, db: Session = Depends(get_db)):
    row = get_race_row_by_year_round_or_404(year, round, db)
    return dict(row._mapping)


# ---------------------------------------------------------
# 8️⃣ GET /races/{year}/{round}/results
# Full classified race results
# ---------------------------------------------------------
@router.get("/{year}/{round}/results")
def race_results(year: int, round: int, db: Session = Depends(get_db)):
    race_id = get_race_id_by_year_round(year, round, db)

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
        "year": year,
        "round": round,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 9️⃣ GET /races/{year}/{round}/podium
# Top 3 finishers
# ---------------------------------------------------------
@router.get("/{year}/{round}/podium")
def race_podium(year: int, round: int, db: Session = Depends(get_db)):
    race_id = get_race_id_by_year_round(year, round, db)

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
        "year": year,
        "round": round,
        "count": len(rows),
        "data": [dict(row._mapping) for row in rows],
    }


# ---------------------------------------------------------
# 🔟 GET /races/{year}/{round}/summary
# Compact summary of a race
# ---------------------------------------------------------
@router.get("/{year}/{round}/summary")
def race_summary(year: int, round: int, db: Session = Depends(get_db)):
    race_row = get_race_row_by_year_round_or_404(year, round, db)
    race_id = race_row._mapping["race_id"]

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
        SUM(CASE WHEN s.status ILIKE 'Finished' OR s.status LIKE '+%%' THEN 1 ELSE 0 END) AS finishers_like,
        SUM(CASE WHEN NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%%') THEN 1 ELSE 0 END) AS non_finishers
    FROM results res
    JOIN status s ON s.status_id = res.status_id
    WHERE res.race_id = :race_id;
    """

    winner_row = db.execute(text(winner_sql), {"race_id": race_id}).fetchone()
    counts_row = db.execute(text(counts_sql), {"race_id": race_id}).fetchone()

    return {
        "race": dict(race_row._mapping),
        "winner": dict(winner_row._mapping) if winner_row else None,
        "summary": dict(counts_row._mapping) if counts_row else None,
    }


# ---------------------------------------------------------
# 1️⃣1️⃣ GET /races/{year}/{round}/dnfs
# DNF / non-finish analysis for a race
# ---------------------------------------------------------
@router.get("/{year}/{round}/dnfs")
def race_dnfs(year: int, round: int, db: Session = Depends(get_db)):
    race_id = get_race_id_by_year_round(year, round, db)

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
      AND NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%%')
    ORDER BY d.surname, d.forename;
    """

    breakdown_sql = """
    SELECT
        s.status,
        COUNT(*) AS count
    FROM results res
    JOIN status s ON s.status_id = res.status_id
    WHERE res.race_id = :race_id
      AND NOT (s.status ILIKE 'Finished' OR s.status LIKE '+%%')
    GROUP BY s.status
    ORDER BY count DESC, s.status;
    """

    detail_rows = db.execute(text(details_sql), {"race_id": race_id}).fetchall()
    breakdown_rows = db.execute(text(breakdown_sql), {"race_id": race_id}).fetchall()

    return {
        "year": year,
        "round": round,
        "non_finishers_count": len(detail_rows),
        "non_finishers": [dict(row._mapping) for row in detail_rows],
        "breakdown_by_status": [dict(row._mapping) for row in breakdown_rows],
    }


# ---------------------------------------------------------
# 1️⃣2️⃣ PATCH /races/{race_id}
# Update an existing race (admin only)
# ---------------------------------------------------------
@router.patch("/{race_id}")
def update_race(
    race_id: int,
    payload: RaceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    ensure_race_exists(race_id, db)

    if payload.circuit_id is not None:
        ensure_circuit_exists(payload.circuit_id, db)

    existing = db.execute(
        text("""
            SELECT race_id, year, round, circuit_id, name, date, time
            FROM races
            WHERE race_id = :race_id
        """),
        {"race_id": race_id},
    ).fetchone()

    existing_data = dict(existing._mapping)

    updated_data = {
        "race_id": race_id,
        "year": payload.year if payload.year is not None else existing_data["year"],
        "round": payload.round if payload.round is not None else existing_data["round"],
        "circuit_id": payload.circuit_id if payload.circuit_id is not None else existing_data["circuit_id"],
        "name": payload.name if payload.name is not None else existing_data["name"],
        "date": payload.date if payload.date is not None else existing_data["date"],
        "time": payload.time if payload.time is not None else existing_data["time"],
    }

    row = db.execute(
        text("""
            UPDATE races
            SET year = :year,
                round = :round,
                circuit_id = :circuit_id,
                name = :name,
                date = :date,
                time = :time
            WHERE race_id = :race_id
            RETURNING race_id, year, round, circuit_id, name, date, time
        """),
        updated_data,
    ).fetchone()

    db.commit()

    return {
        "message": "Race updated successfully",
        "data": dict(row._mapping),
    }


# ---------------------------------------------------------
# 1️⃣3️⃣ DELETE /races/{race_id}
# Delete a race (admin only)
# ---------------------------------------------------------
@router.delete("/{race_id}")
def delete_race(
    race_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    ensure_race_exists(race_id, db)

    dependency_count = db.execute(
        text("SELECT COUNT(*) FROM results WHERE race_id = :race_id"),
        {"race_id": race_id},
    ).scalar()

    if dependency_count and dependency_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete race because related results exist",
        )

    db.execute(
        text("DELETE FROM races WHERE race_id = :race_id"),
        {"race_id": race_id},
    )
    db.commit()

    return {
        "message": "Race deleted successfully",
        "race_id": race_id,
    }
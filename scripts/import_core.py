import os
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text, inspect
from app.db.database import Base


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.where(pd.notnull(df), None)


def ensure_tables_exist(engine):
    Base.metadata.create_all(bind=engine)
    print("✓ tables created / verified")


def truncate_if_tables_exist(engine):
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {"results", "races", "status", "circuits", "constructors", "drivers"}

    if required_tables.issubset(existing_tables):
        with engine.begin() as conn:
            conn.execute(text("""
                TRUNCATE TABLE results,
                               races,
                               status,
                               circuits,
                               constructors,
                               drivers
                RESTART IDENTITY CASCADE;
            """))
        print("✓ tables cleared")
    else:
        print("⚠️ Some tables did not exist yet, skipping truncate on first run")


def get_engine():
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://adambakeer@localhost/f1db"
    )

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    if "render.com" in database_url and "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    print("Using database URL:", database_url.split("@")[0] + "@*****")
    return create_engine(database_url, pool_pre_ping=True)


def main(engine=None, data_dir="data"):
    """
    Import F1 data from CSV files into the database.

    Args:
        engine: SQLAlchemy engine (optional)
        data_dir: Directory containing CSV files
    """
    if engine is None:
        engine = get_engine()

    data_path = data_dir

    # 1) Ensure tables exist first
    ensure_tables_exist(engine)

    # 2) Clear tables if they already exist
    truncate_if_tables_exist(engine)

    # -------------------------
    # 1) CONSTRUCTORS
    # -------------------------
    constructors = pd.read_csv(f"{data_path}/constructors.csv")
    constructors = constructors[["constructorId", "name", "nationality"]].rename(columns={
        "constructorId": "constructor_id"
    })
    constructors = clean_df(constructors)
    constructors.to_sql("constructors", engine, if_exists="append", index=False)
    print("✓ constructors imported")

    # -------------------------
    # 2) CIRCUITS
    # -------------------------
    circuits = pd.read_csv(f"{data_path}/circuits.csv")
    circuits = circuits[["circuitId", "name", "location", "country", "lat", "lng", "alt"]].rename(columns={
        "circuitId": "circuit_id"
    })
    circuits = clean_df(circuits)
    circuits.to_sql("circuits", engine, if_exists="append", index=False)
    print("✓ circuits imported")

    # -------------------------
    # 3) DRIVERS
    # -------------------------
    drivers = pd.read_csv(f"{data_path}/drivers.csv")
    drivers = drivers[["driverId", "code", "forename", "surname", "dob", "nationality"]].rename(columns={
        "driverId": "driver_id"
    })
    drivers["dob"] = pd.to_datetime(drivers["dob"], errors="coerce").dt.date
    drivers = clean_df(drivers)
    drivers.to_sql("drivers", engine, if_exists="append", index=False)
    print("✓ drivers imported")

    # -------------------------
    # 4) STATUS
    # -------------------------
    status_df = pd.read_csv(f"{data_path}/status.csv")
    status_df = status_df.rename(columns={"statusId": "status_id"})
    status_df = clean_df(status_df)
    status_df.to_sql("status", engine, if_exists="append", index=False)
    print("✓ status imported")

    # -------------------------
    # 5) RACES
    # -------------------------
    races = pd.read_csv(f"{data_path}/races.csv")
    races = races[["raceId", "year", "round", "circuitId", "name", "date", "time"]].rename(columns={
        "raceId": "race_id",
        "circuitId": "circuit_id"
    })

    races["date"] = pd.to_datetime(races["date"], errors="coerce").dt.date
    races["time"] = races["time"].replace({r"\\N": None, "": None})
    races["time"] = pd.to_datetime(races["time"], format="%H:%M:%S", errors="coerce").dt.time
    races = clean_df(races)
    races.to_sql("races", engine, if_exists="append", index=False)
    print("✓ races imported")

    # -------------------------
    # 6) RESULTS
    # -------------------------
    results = pd.read_csv(f"{data_path}/results.csv", na_values=[r"\N"])
    results = results[[
        "resultId", "raceId", "driverId", "constructorId", "statusId",
        "grid", "positionOrder", "points", "laps", "milliseconds"
    ]].rename(columns={
        "resultId": "result_id",
        "raceId": "race_id",
        "driverId": "driver_id",
        "constructorId": "constructor_id",
        "statusId": "status_id",
        "positionOrder": "position_order"
    })

    int_cols = [
        "result_id", "race_id", "driver_id", "constructor_id",
        "status_id", "grid", "position_order", "laps", "milliseconds"
    ]
    for col in int_cols:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    results["points"] = pd.to_numeric(results["points"], errors="coerce")
    results = results.where(pd.notnull(results), None)

    results.to_sql("results", engine, if_exists="append", index=False)
    print("✓ results imported")

    print("\n✨ All core tables imported successfully!")


if __name__ == "__main__":
    main()
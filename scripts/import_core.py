import pandas as pd
from sqlalchemy import create_engine, text

# -------------------------
# Database connection
# -------------------------
engine = create_engine("postgresql+psycopg2://localhost/f1db")
DATA = "data"

# -------------------------
# Helper: replace NaN with None
# -------------------------
def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.where(pd.notnull(df), None)

# -------------------------
# STEP 0: Clear tables (idempotent behaviour)
# -------------------------
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

print(" Tables cleared")

# -------------------------
# 1) CONSTRUCTORS
# -------------------------
constructors = pd.read_csv(f"{DATA}/constructors.csv")
constructors = constructors[["constructorId", "name", "nationality"]].rename(columns={
    "constructorId": "constructor_id"
})
constructors = clean_df(constructors)
constructors.to_sql("constructors", engine, if_exists="append", index=False)
print(" constructors imported")

# -------------------------
# 2) CIRCUITS
# -------------------------
circuits = pd.read_csv(f"{DATA}/circuits.csv")
circuits = circuits[["circuitId", "name", "location", "country", "lat", "lng", "alt"]].rename(columns={
    "circuitId": "circuit_id"
})
circuits = clean_df(circuits)
circuits.to_sql("circuits", engine, if_exists="append", index=False)
print(" circuits imported")

# -------------------------
# 3) DRIVERS
# -------------------------
drivers = pd.read_csv(f"{DATA}/drivers.csv")
drivers = drivers[["driverId", "code", "forename", "surname", "dob", "nationality"]].rename(columns={
    "driverId": "driver_id"
})
drivers["dob"] = pd.to_datetime(drivers["dob"], errors="coerce").dt.date
drivers = clean_df(drivers)
drivers.to_sql("drivers", engine, if_exists="append", index=False)
print(" drivers imported")

# -------------------------
# 4) STATUS
# -------------------------
status = pd.read_csv(f"{DATA}/status.csv")
status = status.rename(columns={"statusId": "status_id"})
status = clean_df(status)
status.to_sql("status", engine, if_exists="append", index=False)
print(" status imported")

# -------------------------
# 5) RACES
# -------------------------
races = pd.read_csv(f"{DATA}/races.csv")
races = races[["raceId", "year", "round", "circuitId", "name", "date", "time"]].rename(columns={
    "raceId": "race_id",
    "circuitId": "circuit_id"
})

races["date"] = pd.to_datetime(races["date"], errors="coerce").dt.date

# Handle time safely
races["time"] = races["time"].replace({r"\\N": None, "": None})
races["time"] = pd.to_datetime(races["time"], format="%H:%M:%S", errors="coerce").dt.time

races = clean_df(races)
races.to_sql("races", engine, if_exists="append", index=False)
print("races imported")

# -------------------------
# 6) RESULTS  (FIXED \N handling)
# -------------------------
results = pd.read_csv(f"{DATA}/results.csv", na_values=[r"\N"])

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

# Convert numeric columns safely (invalid -> NaN -> None)
int_cols = ["result_id", "race_id", "driver_id", "constructor_id", "status_id", "grid", "position_order", "laps", "milliseconds"]
for c in int_cols:
    results[c] = pd.to_numeric(results[c], errors="coerce")

results["points"] = pd.to_numeric(results["points"], errors="coerce")

# NaN -> None for SQL insertion
results = results.where(pd.notnull(results), None)

results.to_sql("results", engine, if_exists="append", index=False)
print("results imported")

print(" All core tables imported successfully.")
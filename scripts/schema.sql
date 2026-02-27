CREATE TABLE IF NOT EXISTS drivers (
  driver_id INTEGER PRIMARY KEY,
  code TEXT,
  forename TEXT NOT NULL,
  surname TEXT NOT NULL,
  dob DATE,
  nationality TEXT
);

CREATE TABLE IF NOT EXISTS constructors (
  constructor_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  nationality TEXT
);

CREATE TABLE IF NOT EXISTS circuits (
  circuit_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  location TEXT,
  country TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  alt INTEGER
);

CREATE TABLE IF NOT EXISTS races (
  race_id INTEGER PRIMARY KEY,
  year INTEGER NOT NULL,
  round INTEGER NOT NULL,
  circuit_id INTEGER NOT NULL REFERENCES circuits(circuit_id),
  name TEXT NOT NULL,
  date DATE NOT NULL,
  time TIME
);

CREATE TABLE IF NOT EXISTS status (
  status_id INTEGER PRIMARY KEY,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
  result_id INTEGER PRIMARY KEY,
  race_id INTEGER NOT NULL REFERENCES races(race_id),
  driver_id INTEGER NOT NULL REFERENCES drivers(driver_id),
  constructor_id INTEGER NOT NULL REFERENCES constructors(constructor_id),
  status_id INTEGER NOT NULL REFERENCES status(status_id),
  grid INTEGER,
  position_order INTEGER,
  points DOUBLE PRECISION,
  laps INTEGER,
  milliseconds INTEGER
);

CREATE INDEX IF NOT EXISTS idx_results_race ON results(race_id);
CREATE INDEX IF NOT EXISTS idx_results_driver ON results(driver_id);
CREATE INDEX IF NOT EXISTS idx_results_constructor ON results(constructor_id);
CREATE INDEX IF NOT EXISTS idx_races_year ON races(year);
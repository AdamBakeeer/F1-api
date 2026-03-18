import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Local development fallback (your existing setup)
    DATABASE_URL = "postgresql+psycopg2://adambakeer@localhost/f1db"
    print("⚠️ Using LOCAL PostgreSQL database")
    use_null_pool = False
else:
    print("✓ Using RAILWAY PostgreSQL database")
    # Fix SSL/connection issues with Railway PostgreSQL
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL + "?sslmode=require"
    use_null_pool = True  # important for cloud

# Engine configuration
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

# On Render → disable pooling (VERY IMPORTANT)
if use_null_pool:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
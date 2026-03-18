import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Development fallback
    DATABASE_URL = "postgresql+psycopg2://adambakeer@localhost/f1db"
    print("⚠️  DATABASE_URL not set - using local PostgreSQL")
else:
    print(f"✓ Using Railway PostgreSQL database")

# Railway-optimized connection settings
engine_kwargs = {
    "pool_pre_ping": True,  # Verify connection before using
    "pool_recycle": 3600,  # Recycle connections every hour
}

# Use NullPool on Railway (connection pooling handled by environment)
if os.getenv("RAILWAY_ENVIRONMENT_NAME"):
    engine_kwargs["poolclass"] = NullPool
else:
    # Local development: use normal pool
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
    """
    Dependency that provides a DB session per request.
    FastAPI will call this automatically when used with Depends(get_db).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
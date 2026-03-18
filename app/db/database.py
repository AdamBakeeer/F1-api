import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment variable or use default for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://adambakeer@localhost/f1db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

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
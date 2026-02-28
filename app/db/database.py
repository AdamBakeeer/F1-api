from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# NOTE: using local Postgres without password
DATABASE_URL = "postgresql+psycopg2://adambakeer@localhost/f1db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

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
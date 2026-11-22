from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.models import Base

# SQLite engine with check_same_thread=False for FastAPI concurrency
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables in SQLite database if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI Dependency for database session injection."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

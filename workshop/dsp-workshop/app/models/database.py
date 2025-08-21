from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config.settings import psql_config

# Create database URL
DATABASE_URL = (
    f"postgresql://{psql_config['postgres.user']}:{psql_config['postgres.password']}"
    f"@{psql_config['postgres.host']}/{psql_config['postgres.db']}"
)

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
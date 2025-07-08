from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from app.core.config import settings

# PostgreSQL database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# Redis connection
redis_client = redis.from_url(settings.redis_url)


def get_db():
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """
    Dependency function to get Redis client.
    
    Returns:
        Redis: Redis client instance
    """
    return redis_client

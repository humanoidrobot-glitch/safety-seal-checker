"""
SQLAlchemy engine, session factory, and declarative Base for the SealCheck application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://sealcheck:sealcheck@localhost:5432/sealcheck"

    class Config:
        env_file = ".env"

    @property
    def effective_database_url(self) -> str:
        """Return the database URL with the scheme fixed for SQLAlchemy 2.0+.

        Render provides ``postgres://`` URLs, but SQLAlchemy 2.0 only accepts
        ``postgresql://``.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()

engine = create_engine(settings.effective_database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""SQLite database setup and session management."""

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import config


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},
    echo=config.DEBUG,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign keys and WAL mode for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create all tables defined by ORM models."""
    import models.schemas  # noqa: F401 -- registers models with Base
    Base.metadata.create_all(bind=engine)


def get_session():
    """Yield a database session, closing it when done."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

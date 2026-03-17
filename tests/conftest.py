"""Pytest fixtures for AgriWatch tests."""

import os
import sys
import datetime
import tempfile

import pytest

# Ensure the project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
config.TESTING = True


@pytest.fixture(scope="session")
def _tmp_db():
    """Create a temporary database path for the entire test session."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    config.DATABASE_PATH = tmp.name
    config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
    yield tmp.name
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


@pytest.fixture(scope="session")
def app(_tmp_db):
    """Create a Flask test application."""
    # Re-import after patching config
    from models.database import Base, engine, SessionLocal
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    yield application

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    """Flask test client."""
    with app.test_client() as c:
        yield c


@pytest.fixture
def db_session(_tmp_db):
    """Database session for direct ORM testing."""
    from models.database import SessionLocal, Base, engine
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_field(db_session):
    """Create a sample field for testing."""
    from models.schemas import Field
    field = Field(
        name="Test Field Alpha",
        crop_type="corn",
        size_hectares=5.0,
        grid_rows=3,
        grid_cols=3,
        planting_date=datetime.datetime.utcnow() - datetime.timedelta(days=60),
    )
    db_session.add(field)
    db_session.commit()
    db_session.refresh(field)
    return field


@pytest.fixture
def sample_sensor(db_session, sample_field):
    """Create a sample sensor for testing."""
    from models.schemas import Sensor
    sensor = Sensor(
        name="Temp Sensor 1",
        sensor_type="temperature",
        field_id=sample_field.id,
        grid_row=1,
        grid_col=1,
    )
    db_session.add(sensor)
    db_session.commit()
    db_session.refresh(sensor)
    return sensor

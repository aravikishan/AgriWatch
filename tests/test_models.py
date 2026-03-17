"""Model and schema tests for AgriWatch."""

import datetime


def test_field_creation(db_session, sample_field):
    """Field model creates and serializes correctly."""
    assert sample_field.id is not None
    d = sample_field.to_dict()
    assert d["name"] == "Test Field Alpha"
    assert d["crop_type"] == "corn"
    assert d["size_hectares"] == 5.0


def test_sensor_creation(db_session, sample_sensor):
    """Sensor model creates and links to field."""
    assert sample_sensor.id is not None
    assert sample_sensor.field_id is not None
    d = sample_sensor.to_dict()
    assert d["sensor_type"] == "temperature"
    assert d["is_active"] is True


def test_reading_creation(db_session, sample_sensor):
    """Reading model stores sensor data."""
    from models.schemas import Reading
    reading = Reading(
        sensor_id=sample_sensor.id,
        value=25.5,
        unit="°C",
        recorded_at=datetime.datetime.utcnow(),
        is_alert=False,
    )
    db_session.add(reading)
    db_session.commit()
    db_session.refresh(reading)
    assert reading.id is not None
    d = reading.to_dict()
    assert d["value"] == 25.5
    assert d["unit"] == "°C"


def test_prediction_creation(db_session, sample_field):
    """CropPrediction model stores prediction data."""
    from models.schemas import CropPrediction
    pred = CropPrediction(
        field_id=sample_field.id,
        predicted_yield=8.5,
        growth_stage="Vegetative",
        growth_stage_index=2,
        accumulated_gdd=450.0,
        confidence=0.72,
        health_score=85.0,
    )
    db_session.add(pred)
    db_session.commit()
    db_session.refresh(pred)
    d = pred.to_dict()
    assert d["predicted_yield"] == 8.5
    assert d["growth_stage"] == "Vegetative"
    assert d["confidence"] == 0.72

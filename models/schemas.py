"""SQLAlchemy ORM models for AgriWatch."""

import datetime

from sqlalchemy import (
    Column, Integer, Float, String, DateTime, Text, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship

from models.database import Base


class Field(Base):
    """Agricultural field / plot."""

    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    crop_type = Column(String(60), nullable=False, default="corn")
    size_hectares = Column(Float, nullable=False, default=1.0)
    grid_rows = Column(Integer, nullable=False, default=4)
    grid_cols = Column(Integer, nullable=False, default=4)
    planting_date = Column(DateTime, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sensors = relationship("Sensor", back_populates="field", cascade="all, delete-orphan")
    predictions = relationship("CropPrediction", back_populates="field", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "crop_type": self.crop_type,
            "size_hectares": self.size_hectares,
            "grid_rows": self.grid_rows,
            "grid_cols": self.grid_cols,
            "planting_date": self.planting_date.isoformat() if self.planting_date else None,
            "location_lat": self.location_lat,
            "location_lon": self.location_lon,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sensor_count": len(self.sensors) if self.sensors else 0,
        }


class Sensor(Base):
    """IoT sensor device deployed in a field."""

    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    sensor_type = Column(String(60), nullable=False)  # temperature, humidity, soil_moisture, ph, light
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    grid_row = Column(Integer, nullable=False, default=0)
    grid_col = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    installed_at = Column(DateTime, default=datetime.datetime.utcnow)

    field = relationship("Field", back_populates="sensors")
    readings = relationship("Reading", back_populates="sensor", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "sensor_type": self.sensor_type,
            "field_id": self.field_id,
            "grid_row": self.grid_row,
            "grid_col": self.grid_col,
            "is_active": self.is_active,
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "field_name": self.field.name if self.field else None,
        }


class Reading(Base):
    """Single sensor reading / data point."""

    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_alert = Column(Boolean, default=False)
    alert_message = Column(String(255), nullable=True)

    sensor = relationship("Sensor", back_populates="readings")

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "value": round(self.value, 2),
            "unit": self.unit,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "is_alert": self.is_alert,
            "alert_message": self.alert_message,
            "sensor_name": self.sensor.name if self.sensor else None,
            "sensor_type": self.sensor.sensor_type if self.sensor else None,
        }


class CropPrediction(Base):
    """Crop yield and growth prediction for a field."""

    __tablename__ = "crop_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    predicted_yield = Column(Float, nullable=True)
    yield_unit = Column(String(30), default="tonnes/ha")
    growth_stage = Column(String(60), nullable=True)
    growth_stage_index = Column(Integer, default=0)
    accumulated_gdd = Column(Float, default=0.0)
    estimated_harvest_date = Column(DateTime, nullable=True)
    confidence = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)  # 0-100
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    field = relationship("Field", back_populates="predictions")

    def to_dict(self):
        return {
            "id": self.id,
            "field_id": self.field_id,
            "predicted_yield": round(self.predicted_yield, 2) if self.predicted_yield else None,
            "yield_unit": self.yield_unit,
            "growth_stage": self.growth_stage,
            "growth_stage_index": self.growth_stage_index,
            "accumulated_gdd": round(self.accumulated_gdd, 1),
            "estimated_harvest_date": (
                self.estimated_harvest_date.isoformat()
                if self.estimated_harvest_date else None
            ),
            "confidence": round(self.confidence, 2),
            "health_score": round(self.health_score, 1),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "field_name": self.field.name if self.field else None,
        }

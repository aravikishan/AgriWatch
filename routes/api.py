"""REST API endpoints for AgriWatch."""

import datetime

from flask import Blueprint, jsonify, request

from models.database import SessionLocal
from models.schemas import Field, Sensor, Reading, CropPrediction
from services import sensors as sensor_service
from services import prediction as prediction_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _get_db():
    return SessionLocal()


# ---- Fields ----

@api_bp.route("/fields", methods=["GET"])
def list_fields():
    """List all fields."""
    db = _get_db()
    try:
        fields = db.query(Field).all()
        return jsonify([f.to_dict() for f in fields])
    finally:
        db.close()


@api_bp.route("/fields/<int:field_id>", methods=["GET"])
def get_field(field_id):
    """Get a single field by ID."""
    db = _get_db()
    try:
        field = db.query(Field).get(field_id)
        if not field:
            return jsonify({"error": "Field not found"}), 404
        return jsonify(field.to_dict())
    finally:
        db.close()


@api_bp.route("/fields", methods=["POST"])
def create_field():
    """Create a new field."""
    db = _get_db()
    try:
        data = request.get_json(force=True)
        planting_date = None
        if data.get("planting_date"):
            planting_date = datetime.datetime.fromisoformat(data["planting_date"])

        field = Field(
            name=data.get("name", "New Field"),
            crop_type=data.get("crop_type", "corn"),
            size_hectares=float(data.get("size_hectares", 1.0)),
            grid_rows=int(data.get("grid_rows", 4)),
            grid_cols=int(data.get("grid_cols", 4)),
            planting_date=planting_date,
            location_lat=data.get("location_lat"),
            location_lon=data.get("location_lon"),
            notes=data.get("notes"),
        )
        db.add(field)
        db.commit()
        db.refresh(field)
        return jsonify(field.to_dict()), 201
    finally:
        db.close()


@api_bp.route("/fields/<int:field_id>", methods=["PUT"])
def update_field(field_id):
    """Update an existing field."""
    db = _get_db()
    try:
        field = db.query(Field).get(field_id)
        if not field:
            return jsonify({"error": "Field not found"}), 404
        data = request.get_json(force=True)
        for attr in ["name", "crop_type", "notes"]:
            if attr in data:
                setattr(field, attr, data[attr])
        if "size_hectares" in data:
            field.size_hectares = float(data["size_hectares"])
        if "grid_rows" in data:
            field.grid_rows = int(data["grid_rows"])
        if "grid_cols" in data:
            field.grid_cols = int(data["grid_cols"])
        if "planting_date" in data and data["planting_date"]:
            field.planting_date = datetime.datetime.fromisoformat(data["planting_date"])
        if "location_lat" in data:
            field.location_lat = data["location_lat"]
        if "location_lon" in data:
            field.location_lon = data["location_lon"]
        db.commit()
        db.refresh(field)
        return jsonify(field.to_dict())
    finally:
        db.close()


@api_bp.route("/fields/<int:field_id>", methods=["DELETE"])
def delete_field(field_id):
    """Delete a field and its associated data."""
    db = _get_db()
    try:
        field = db.query(Field).get(field_id)
        if not field:
            return jsonify({"error": "Field not found"}), 404
        db.delete(field)
        db.commit()
        return jsonify({"message": "Field deleted"})
    finally:
        db.close()


# ---- Sensors ----

@api_bp.route("/sensors", methods=["GET"])
def list_sensors():
    """List all sensors, optionally filtered by field."""
    db = _get_db()
    try:
        query = db.query(Sensor)
        field_id = request.args.get("field_id", type=int)
        if field_id:
            query = query.filter(Sensor.field_id == field_id)
        sensors = query.all()
        return jsonify([s.to_dict() for s in sensors])
    finally:
        db.close()


@api_bp.route("/sensors/<int:sensor_id>", methods=["GET"])
def get_sensor(sensor_id):
    """Get a single sensor by ID."""
    db = _get_db()
    try:
        sensor = db.query(Sensor).get(sensor_id)
        if not sensor:
            return jsonify({"error": "Sensor not found"}), 404
        return jsonify(sensor.to_dict())
    finally:
        db.close()


@api_bp.route("/sensors", methods=["POST"])
def create_sensor():
    """Create a new sensor."""
    db = _get_db()
    try:
        data = request.get_json(force=True)
        sensor = Sensor(
            name=data.get("name", "New Sensor"),
            sensor_type=data.get("sensor_type", "temperature"),
            field_id=int(data["field_id"]),
            grid_row=int(data.get("grid_row", 0)),
            grid_col=int(data.get("grid_col", 0)),
            is_active=data.get("is_active", True),
        )
        db.add(sensor)
        db.commit()
        db.refresh(sensor)
        return jsonify(sensor.to_dict()), 201
    finally:
        db.close()


# ---- Readings ----

@api_bp.route("/readings", methods=["GET"])
def list_readings():
    """List recent readings, optionally filtered by sensor or field."""
    db = _get_db()
    try:
        sensor_id = request.args.get("sensor_id", type=int)
        field_id = request.args.get("field_id", type=int)
        limit = request.args.get("limit", 50, type=int)

        if sensor_id:
            readings = (
                db.query(Reading)
                .filter(Reading.sensor_id == sensor_id)
                .order_by(Reading.recorded_at.desc())
                .limit(limit)
                .all()
            )
        elif field_id:
            readings = sensor_service.get_latest_readings(db, field_id, limit)
        else:
            readings = sensor_service.get_latest_readings(db, limit=limit)

        return jsonify([r.to_dict() for r in readings])
    finally:
        db.close()


@api_bp.route("/readings/ingest", methods=["POST"])
def ingest_reading():
    """Ingest a new sensor reading (or simulate one)."""
    db = _get_db()
    try:
        data = request.get_json(force=True)
        sensor_id = int(data["sensor_id"])
        sensor = db.query(Sensor).get(sensor_id)
        if not sensor:
            return jsonify({"error": "Sensor not found"}), 404

        value = data.get("value")  # None means simulate
        reading = sensor_service.ingest_reading(db, sensor, value=value)
        if reading is None:
            return jsonify({"error": "Could not generate reading"}), 400
        return jsonify(reading.to_dict()), 201
    finally:
        db.close()


@api_bp.route("/readings/simulate/<int:field_id>", methods=["POST"])
def simulate_field_readings(field_id):
    """Simulate readings for all sensors in a field."""
    db = _get_db()
    try:
        field = db.query(Field).get(field_id)
        if not field:
            return jsonify({"error": "Field not found"}), 404
        sensors = db.query(Sensor).filter(
            Sensor.field_id == field_id, Sensor.is_active.is_(True)
        ).all()
        results = []
        for sensor in sensors:
            reading = sensor_service.ingest_reading(db, sensor)
            if reading:
                results.append(reading.to_dict())
        return jsonify(results), 201
    finally:
        db.close()


@api_bp.route("/readings/history/<int:sensor_id>", methods=["GET"])
def sensor_history(sensor_id):
    """Get time-series data for a specific sensor."""
    db = _get_db()
    try:
        hours = request.args.get("hours", 24, type=int)
        readings = sensor_service.get_sensor_history(db, sensor_id, hours)
        return jsonify([r.to_dict() for r in readings])
    finally:
        db.close()


# ---- Alerts ----

@api_bp.route("/alerts", methods=["GET"])
def list_alerts():
    """List recent alert readings."""
    db = _get_db()
    try:
        field_id = request.args.get("field_id", type=int)
        limit = request.args.get("limit", 20, type=int)
        alerts = sensor_service.get_alerts(db, field_id, limit)
        return jsonify([a.to_dict() for a in alerts])
    finally:
        db.close()


# ---- Predictions ----

@api_bp.route("/predictions/<int:field_id>", methods=["GET"])
def get_prediction(field_id):
    """Get the latest prediction for a field."""
    db = _get_db()
    try:
        pred = prediction_service.get_latest_prediction(db, field_id)
        if not pred:
            return jsonify({"error": "No prediction available"}), 404
        return jsonify(pred.to_dict())
    finally:
        db.close()


@api_bp.route("/predictions/<int:field_id>/generate", methods=["POST"])
def generate_prediction(field_id):
    """Generate a new crop prediction for a field."""
    db = _get_db()
    try:
        field = db.query(Field).get(field_id)
        if not field:
            return jsonify({"error": "Field not found"}), 404
        pred = prediction_service.create_prediction(db, field)
        return jsonify(pred.to_dict()), 201
    finally:
        db.close()


@api_bp.route("/predictions/<int:field_id>/zones", methods=["GET"])
def get_field_zones(field_id):
    """Get zone health grid for a field."""
    db = _get_db()
    try:
        field = db.query(Field).get(field_id)
        if not field:
            return jsonify({"error": "Field not found"}), 404
        grid = prediction_service.get_field_zone_health(db, field)
        return jsonify({
            "field_id": field_id,
            "grid_rows": field.grid_rows,
            "grid_cols": field.grid_cols,
            "zones": grid,
        })
    finally:
        db.close()


# ---- Dashboard summary ----

@api_bp.route("/dashboard/summary", methods=["GET"])
def dashboard_summary():
    """Get aggregated dashboard data."""
    db = _get_db()
    try:
        fields = db.query(Field).all()
        total_sensors = db.query(Sensor).count()
        active_sensors = db.query(Sensor).filter(Sensor.is_active.is_(True)).count()
        recent_alerts = sensor_service.get_alerts(db, limit=5)

        field_summaries = []
        for f in fields:
            pred = prediction_service.get_latest_prediction(db, f.id)
            health = prediction_service.compute_health_score(db, f)
            field_summaries.append({
                "id": f.id,
                "name": f.name,
                "crop_type": f.crop_type,
                "size_hectares": f.size_hectares,
                "health_score": health,
                "growth_stage": pred.growth_stage if pred else "Unknown",
                "predicted_yield": pred.predicted_yield if pred else None,
            })

        return jsonify({
            "total_fields": len(fields),
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "alert_count": len(recent_alerts),
            "recent_alerts": [a.to_dict() for a in recent_alerts],
            "fields": field_summaries,
        })
    finally:
        db.close()

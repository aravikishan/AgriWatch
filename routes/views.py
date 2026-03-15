"""HTML-serving view routes for AgriWatch."""

from flask import Blueprint, render_template

from models.database import SessionLocal
from models.schemas import Field, Sensor
from services import prediction as prediction_service

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Farm dashboard overview."""
    db = SessionLocal()
    try:
        fields = db.query(Field).all()
        field_data = []
        for f in fields:
            pred = prediction_service.get_latest_prediction(db, f.id)
            health = prediction_service.compute_health_score(db, f)
            field_data.append({
                "field": f,
                "prediction": pred,
                "health": health,
            })
        sensor_count = db.query(Sensor).filter(Sensor.is_active.is_(True)).count()
        return render_template(
            "index.html",
            fields=field_data,
            sensor_count=sensor_count,
            total_fields=len(fields),
        )
    finally:
        db.close()


@views_bp.route("/fields")
def fields_page():
    """Field management page."""
    db = SessionLocal()
    try:
        fields = db.query(Field).all()
        return render_template("fields.html", fields=fields)
    finally:
        db.close()


@views_bp.route("/sensors")
def sensors_page():
    """Sensor data and charts page."""
    db = SessionLocal()
    try:
        sensors = db.query(Sensor).all()
        fields = db.query(Field).all()
        return render_template("sensors.html", sensors=sensors, fields=fields)
    finally:
        db.close()


@views_bp.route("/predictions")
def predictions_page():
    """Crop predictions page."""
    db = SessionLocal()
    try:
        fields = db.query(Field).all()
        predictions = []
        for f in fields:
            pred = prediction_service.get_latest_prediction(db, f.id)
            health = prediction_service.compute_health_score(db, f)
            zones = prediction_service.get_field_zone_health(db, f)
            predictions.append({
                "field": f,
                "prediction": pred,
                "health": health,
                "zones": zones,
            })
        return render_template("predictions.html", predictions=predictions)
    finally:
        db.close()


@views_bp.route("/about")
def about():
    """About page."""
    return render_template("about.html")

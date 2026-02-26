"""AgriWatch -- IoT Agricultural Monitoring Platform.

Flask entry point that wires up blueprints, initializes the database,
and loads seed data on first run.
"""

import json
import os
import datetime

from flask import Flask

import config
from models.database import init_db, SessionLocal
from models.schemas import Field, Sensor, Reading, CropPrediction
from routes.api import api_bp
from routes.views import views_bp
from services import sensors as sensor_service
from services import prediction as prediction_service


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "agriwatch-dev-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Initialize components database
    with app.app_context():
        init_db()
        _seed_if_empty()

    return app


def _seed_if_empty():
    """Load seed data if the database is empty."""
    db = SessionLocal()
    try:
        if db.query(Field).count() > 0:
            return

        seed_path = config.SEED_DATA_PATH
        if not os.path.exists(seed_path):
            return

        with open(seed_path, "r") as f:
            data = json.load(f)

        # Create fields
        field_map = {}
        for fd in data.get("fields", []):
            planting_date = None
            if fd.get("planting_date"):
                planting_date = datetime.datetime.fromisoformat(fd["planting_date"])
            field = Field(
                name=fd["name"],
                crop_type=fd.get("crop_type", "corn"),
                size_hectares=fd.get("size_hectares", 1.0),
                grid_rows=fd.get("grid_rows", 4),
                grid_cols=fd.get("grid_cols", 4),
                planting_date=planting_date,
                location_lat=fd.get("location_lat"),
                location_lon=fd.get("location_lon"),
                notes=fd.get("notes"),
            )
            db.add(field)
            db.flush()
            field_map[fd["name"]] = field

        # Create sensors
        sensor_map = {}
        for sd in data.get("sensors", []):
            field = field_map.get(sd.get("field_name"))
            if not field:
                continue
            sensor = Sensor(
                name=sd["name"],
                sensor_type=sd["sensor_type"],
                field_id=field.id,
                grid_row=sd.get("grid_row", 0),
                grid_col=sd.get("grid_col", 0),
                is_active=sd.get("is_active", True),
            )
            db.add(sensor)
            db.flush()
            sensor_map[sd["name"]] = sensor

        # Generate simulated historical readings
        now = datetime.datetime.utcnow()
        for sensor_name, sensor in sensor_map.items():
            start = now - datetime.timedelta(days=7)
            series = sensor_service.generate_time_series(
                sensor.sensor_type, start, now, interval_minutes=60
            )
            for point in series:
                is_alert, alert_msg = sensor_service.check_alert(
                    sensor.sensor_type, point["value"]
                )
                reading = Reading(
                    sensor_id=sensor.id,
                    value=point["value"],
                    unit=point["unit"],
                    recorded_at=point["recorded_at"],
                    is_alert=is_alert,
                    alert_message=alert_msg,
                )
                db.add(reading)

        db.commit()

        # Generate initial predictions
        for field in field_map.values():
            prediction_service.create_prediction(db, field)

    finally:
        db.close()


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003, debug=config.DEBUG)

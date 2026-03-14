"""Sensor data simulation and time-series generation.

Simulates realistic IoT sensor readings with:
- Diurnal temperature patterns (warm day, cool night)
- Humidity inversely correlated with temperature
- Soil moisture that decreases between watering events
- pH with minor random fluctuation
- Light intensity following a bell curve during daylight hours
"""

import math
import random
import datetime

import config
from models.schemas import Reading


def _hour_fraction(dt):
    """Return hour as a float (0-24) from a datetime."""
    return dt.hour + dt.minute / 60.0 + dt.second / 3600.0


def simulate_temperature(dt, base_temp=22.0, amplitude=8.0, noise=1.5):
    """Simulate temperature with a sinusoidal diurnal pattern.

    Peak temperature at ~14:00, minimum at ~05:00.
    """
    hour = _hour_fraction(dt)
    # Shift sine so peak is at hour 14: sin(2*pi*(hour-14)/24 + pi/2)
    diurnal = amplitude * math.sin(2 * math.pi * (hour - 8) / 24)
    jitter = random.gauss(0, noise)
    return round(base_temp + diurnal + jitter, 2)


def simulate_humidity(dt, base_humidity=60.0, amplitude=15.0, noise=3.0):
    """Simulate humidity inversely correlated with temperature.

    Higher humidity at night, lower during warm daytime.
    """
    hour = _hour_fraction(dt)
    diurnal = -amplitude * math.sin(2 * math.pi * (hour - 8) / 24)
    jitter = random.gauss(0, noise)
    value = base_humidity + diurnal + jitter
    return round(max(10.0, min(100.0, value)), 2)


def simulate_soil_moisture(dt, base=55.0, days_since_water=0, noise=2.0):
    """Simulate soil moisture decreasing over days since last watering.

    Moisture drops ~5% per day without rain or irrigation.
    """
    decay = days_since_water * 5.0
    hour = _hour_fraction(dt)
    # Slight diurnal effect: evaporation increases midday
    evap = 2.0 * math.sin(max(0, math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
    jitter = random.gauss(0, noise)
    value = base - decay - evap + jitter
    return round(max(5.0, min(100.0, value)), 2)


def simulate_ph(dt, base_ph=6.5, noise=0.15):
    """Simulate soil pH with minor random fluctuation."""
    jitter = random.gauss(0, noise)
    value = base_ph + jitter
    return round(max(3.0, min(10.0, value)), 2)


def simulate_light(dt, peak_lux=80000.0, noise=2000.0):
    """Simulate light intensity with a bell curve during daylight.

    Zero at night, peaks at solar noon (~12:00).
    """
    hour = _hour_fraction(dt)
    if hour < 6 or hour > 20:
        return round(max(0, random.gauss(0, 5)), 2)
    # Bell curve centered on hour 13
    x = (hour - 13) / 3.5
    intensity = peak_lux * math.exp(-0.5 * x * x)
    jitter = random.gauss(0, noise)
    return round(max(0, intensity + jitter), 2)


SIMULATORS = {
    "temperature": {"fn": simulate_temperature, "unit": "°C"},
    "humidity": {"fn": simulate_humidity, "unit": "%"},
    "soil_moisture": {"fn": simulate_soil_moisture, "unit": "%"},
    "ph": {"fn": simulate_ph, "unit": "pH"},
    "light": {"fn": simulate_light, "unit": "lux"},
}


def generate_reading(sensor_type, dt=None):
    """Generate a single simulated reading for the given sensor type."""
    if dt is None:
        dt = datetime.datetime.utcnow()
    sim = SIMULATORS.get(sensor_type)
    if not sim:
        return None
    value = sim["fn"](dt)
    unit = sim["unit"]
    return {"value": value, "unit": unit, "recorded_at": dt}


def generate_time_series(sensor_type, start, end, interval_minutes=30):
    """Generate a series of readings between start and end datetimes."""
    readings = []
    current = start
    delta = datetime.timedelta(minutes=interval_minutes)
    while current <= end:
        reading = generate_reading(sensor_type, current)
        if reading:
            readings.append(reading)
        current += delta
    return readings


def check_alert(sensor_type, value):
    """Check whether a reading is outside acceptable thresholds.

    Returns (is_alert: bool, message: str or None).
    """
    thresholds = config.THRESHOLDS.get(sensor_type)
    if not thresholds:
        return False, None

    if value < thresholds["min"]:
        msg = (
            f"{sensor_type.replace('_', ' ').title()} too low: "
            f"{value} {thresholds['unit']} (min: {thresholds['min']})"
        )
        return True, msg
    if value > thresholds["max"]:
        msg = (
            f"{sensor_type.replace('_', ' ').title()} too high: "
            f"{value} {thresholds['unit']} (max: {thresholds['max']})"
        )
        return True, msg
    return False, None


def ingest_reading(session, sensor, value=None, dt=None):
    """Create a reading for a sensor, optionally simulating the value.

    Returns the created Reading ORM instance.
    """
    if dt is None:
        dt = datetime.datetime.utcnow()
    if value is None:
        sim_data = generate_reading(sensor.sensor_type, dt)
        if sim_data is None:
            return None
        value = sim_data["value"]

    unit = SIMULATORS.get(sensor.sensor_type, {}).get("unit", "")
    is_alert, alert_msg = check_alert(sensor.sensor_type, value)

    reading = Reading(
        sensor_id=sensor.id,
        value=value,
        unit=unit,
        recorded_at=dt,
        is_alert=is_alert,
        alert_message=alert_msg,
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)
    return reading


def get_latest_readings(session, field_id=None, limit=50):
    """Fetch the most recent readings, optionally filtered by field."""
    from models.schemas import Sensor

    query = session.query(Reading).join(Sensor)
    if field_id:
        query = query.filter(Sensor.field_id == field_id)
    return query.order_by(Reading.recorded_at.desc()).limit(limit).all()


def get_alerts(session, field_id=None, limit=20):
    """Fetch recent alert readings."""
    from models.schemas import Sensor

    query = session.query(Reading).join(Sensor).filter(Reading.is_alert.is_(True))
    if field_id:
        query = query.filter(Sensor.field_id == field_id)
    return query.order_by(Reading.recorded_at.desc()).limit(limit).all()


def get_sensor_history(session, sensor_id, hours=24):
    """Fetch readings for a specific sensor within the last N hours."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    return (
        session.query(Reading)
        .filter(Reading.sensor_id == sensor_id, Reading.recorded_at >= cutoff)
        .order_by(Reading.recorded_at.asc())
        .all()
    )

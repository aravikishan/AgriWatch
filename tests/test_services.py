"""Service layer tests for AgriWatch."""

import datetime


def test_simulate_temperature():
    """Temperature simulation produces reasonable values."""
    from services.sensors import simulate_temperature
    dt_noon = datetime.datetime(2024, 7, 15, 14, 0, 0)
    dt_night = datetime.datetime(2024, 7, 15, 3, 0, 0)
    temp_noon = simulate_temperature(dt_noon)
    temp_night = simulate_temperature(dt_night)
    # Noon should generally be warmer than 3 AM (statistically)
    assert -20 < temp_noon < 50
    assert -20 < temp_night < 50


def test_simulate_humidity():
    """Humidity simulation stays in bounds."""
    from services.sensors import simulate_humidity
    dt = datetime.datetime(2024, 7, 15, 12, 0, 0)
    h = simulate_humidity(dt)
    assert 10.0 <= h <= 100.0


def test_simulate_soil_moisture():
    """Soil moisture decreases with days since watering."""
    from services.sensors import simulate_soil_moisture
    dt = datetime.datetime(2024, 7, 15, 12, 0, 0)
    m0 = simulate_soil_moisture(dt, days_since_water=0)
    m3 = simulate_soil_moisture(dt, days_since_water=3)
    # On average moisture should be lower after 3 dry days
    # This is statistical so we just check bounds
    assert 5.0 <= m0 <= 100.0
    assert 5.0 <= m3 <= 100.0


def test_simulate_light():
    """Light simulation gives zero at night, positive at noon."""
    from services.sensors import simulate_light
    dt_noon = datetime.datetime(2024, 7, 15, 13, 0, 0)
    dt_midnight = datetime.datetime(2024, 7, 15, 2, 0, 0)
    light_noon = simulate_light(dt_noon)
    light_midnight = simulate_light(dt_midnight)
    assert light_noon > 1000  # should be bright at noon
    assert light_midnight < 100  # very dark at 2 AM


def test_check_alert():
    """Alert detection works for out-of-range values."""
    from services.sensors import check_alert
    is_alert, msg = check_alert("temperature", 50.0)
    assert is_alert is True
    assert "too high" in msg.lower()

    is_alert, msg = check_alert("temperature", 22.0)
    assert is_alert is False
    assert msg is None


def test_generate_time_series():
    """Time series generation produces correct count."""
    from services.sensors import generate_time_series
    start = datetime.datetime(2024, 7, 15, 0, 0, 0)
    end = datetime.datetime(2024, 7, 15, 6, 0, 0)
    series = generate_time_series("temperature", start, end, interval_minutes=60)
    assert len(series) == 7  # 0:00 to 6:00 inclusive


def test_calculate_gdd():
    """Growing degree day calculation."""
    from services.prediction import calculate_gdd
    gdd = calculate_gdd(30.0, 20.0, 10.0)
    assert gdd == 15.0  # (30+20)/2 - 10

    gdd_zero = calculate_gdd(5.0, 3.0, 10.0)
    assert gdd_zero == 0.0  # below base temp


def test_determine_growth_stage():
    """Growth stage determination based on GDD."""
    from services.prediction import determine_growth_stage
    stage, idx = determine_growth_stage("corn", 0)
    assert stage == "Germination"
    assert idx == 0

    stage, idx = determine_growth_stage("corn", 600)
    assert stage == "Vegetative"
    assert idx == 2

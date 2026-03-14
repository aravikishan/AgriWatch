"""Crop yield prediction and growth stage estimation.

Uses growing degree days (GDD) for growth stage tracking and
simple linear regression on sensor history for yield prediction.
"""

import datetime
import math

import config
from models.schemas import CropPrediction, Reading, Sensor


def calculate_gdd(daily_max_temp, daily_min_temp, base_temp):
    """Calculate Growing Degree Days for one day.

    GDD = max(0, (T_max + T_min) / 2 - T_base)
    """
    avg = (daily_max_temp + daily_min_temp) / 2.0
    return max(0.0, avg - base_temp)


def accumulate_gdd(session, field, days_back=None):
    """Calculate accumulated GDD for a field from planting date.

    Uses temperature sensor readings to compute daily max/min.
    """
    crop = field.crop_type.lower()
    base_temp = config.GDD_BASE_TEMPS.get(crop, 10.0)

    start_date = field.planting_date
    if not start_date:
        return 0.0

    if days_back:
        start_date = max(
            start_date,
            datetime.datetime.utcnow() - datetime.timedelta(days=days_back),
        )

    temp_sensors = (
        session.query(Sensor)
        .filter(Sensor.field_id == field.id, Sensor.sensor_type == "temperature")
        .all()
    )
    if not temp_sensors:
        return 0.0

    sensor_ids = [s.id for s in temp_sensors]
    readings = (
        session.query(Reading)
        .filter(
            Reading.sensor_id.in_(sensor_ids),
            Reading.recorded_at >= start_date,
        )
        .order_by(Reading.recorded_at.asc())
        .all()
    )

    if not readings:
        return 0.0

    # Group readings by date
    daily_temps = {}
    for r in readings:
        day_key = r.recorded_at.date()
        if day_key not in daily_temps:
            daily_temps[day_key] = []
        daily_temps[day_key].append(r.value)

    total_gdd = 0.0
    for day_key in sorted(daily_temps.keys()):
        temps = daily_temps[day_key]
        daily_max = max(temps)
        daily_min = min(temps)
        total_gdd += calculate_gdd(daily_max, daily_min, base_temp)

    return round(total_gdd, 1)


def determine_growth_stage(crop_type, accumulated_gdd):
    """Determine the current growth stage based on accumulated GDD."""
    crop = crop_type.lower()
    thresholds = config.GDD_STAGE_THRESHOLDS.get(crop)
    stages = config.GROWTH_STAGES

    if not thresholds:
        return stages[0], 0

    stage_index = 0
    for i, threshold in enumerate(thresholds):
        if accumulated_gdd >= threshold:
            stage_index = i
        else:
            break

    stage_index = min(stage_index, len(stages) - 1)
    return stages[stage_index], stage_index


def estimate_harvest_date(field, accumulated_gdd):
    """Estimate harvest date based on remaining GDD needed."""
    crop = field.crop_type.lower()
    thresholds = config.GDD_STAGE_THRESHOLDS.get(crop)
    if not thresholds or not field.planting_date:
        return None

    total_gdd_needed = thresholds[-1]
    remaining_gdd = max(0, total_gdd_needed - accumulated_gdd)

    # Assume average daily GDD accumulation based on typical conditions
    avg_daily_gdd = 12.0  # reasonable temperate estimate
    if remaining_gdd <= 0:
        return datetime.datetime.utcnow()

    days_remaining = int(remaining_gdd / avg_daily_gdd)
    return datetime.datetime.utcnow() + datetime.timedelta(days=days_remaining)


def compute_health_score(session, field):
    """Compute field health score (0-100) based on recent sensor readings.

    Score considers how close readings are to optimal ranges.
    """
    sensors = (
        session.query(Sensor)
        .filter(Sensor.field_id == field.id, Sensor.is_active.is_(True))
        .all()
    )
    if not sensors:
        return 50.0  # neutral when no data

    scores = []
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=6)

    for sensor in sensors:
        recent = (
            session.query(Reading)
            .filter(Reading.sensor_id == sensor.id, Reading.recorded_at >= cutoff)
            .order_by(Reading.recorded_at.desc())
            .first()
        )
        if not recent:
            continue

        thresholds = config.THRESHOLDS.get(sensor.sensor_type)
        if not thresholds:
            continue

        t_min = thresholds["min"]
        t_max = thresholds["max"]
        optimal = (t_min + t_max) / 2.0
        half_range = (t_max - t_min) / 2.0

        if half_range == 0:
            scores.append(100.0)
            continue

        deviation = abs(recent.value - optimal) / half_range
        score = max(0.0, 100.0 * (1.0 - deviation))
        scores.append(score)

    if not scores:
        return 50.0
    return round(sum(scores) / len(scores), 1)


def predict_yield(session, field):
    """Predict crop yield using sensor health and growth progress.

    Simple model:
        yield = baseline * health_factor * growth_factor
    where health_factor is normalized health score and growth_factor
    accounts for how far along the growth cycle we are.
    """
    crop = field.crop_type.lower()
    baseline = config.YIELD_BASELINES.get(crop, 5.0)

    health = compute_health_score(session, field)
    health_factor = health / 100.0

    acc_gdd = accumulate_gdd(session, field)
    thresholds = config.GDD_STAGE_THRESHOLDS.get(crop)
    if thresholds and thresholds[-1] > 0:
        growth_progress = min(1.0, acc_gdd / thresholds[-1])
    else:
        growth_progress = 0.5

    # Yield adjustments
    # Early growth: uncertain prediction (lower confidence)
    # Near maturity: prediction more reliable
    confidence = min(0.95, 0.3 + 0.65 * growth_progress)

    predicted = baseline * (0.6 + 0.4 * health_factor) * (0.7 + 0.3 * growth_progress)
    return round(predicted, 2), round(confidence, 2)


def create_prediction(session, field):
    """Generate and store a crop prediction for a field."""
    acc_gdd = accumulate_gdd(session, field)
    stage, stage_idx = determine_growth_stage(field.crop_type, acc_gdd)
    harvest_date = estimate_harvest_date(field, acc_gdd)
    health = compute_health_score(session, field)
    predicted_yield, confidence = predict_yield(session, field)

    prediction = CropPrediction(
        field_id=field.id,
        predicted_yield=predicted_yield,
        growth_stage=stage,
        growth_stage_index=stage_idx,
        accumulated_gdd=acc_gdd,
        estimated_harvest_date=harvest_date,
        confidence=confidence,
        health_score=health,
        notes=f"Auto-generated prediction. Growth stage: {stage}. "
              f"Accumulated GDD: {acc_gdd}.",
    )
    session.add(prediction)
    session.commit()
    session.refresh(prediction)
    return prediction


def get_latest_prediction(session, field_id):
    """Get the most recent prediction for a field."""
    return (
        session.query(CropPrediction)
        .filter(CropPrediction.field_id == field_id)
        .order_by(CropPrediction.created_at.desc())
        .first()
    )


def get_field_zone_health(session, field):
    """Compute health scores for each grid zone in a field.

    Returns a 2D list [row][col] of health scores (0-100).
    """
    grid = []
    for r in range(field.grid_rows):
        row = []
        for c in range(field.grid_cols):
            zone_sensors = (
                session.query(Sensor)
                .filter(
                    Sensor.field_id == field.id,
                    Sensor.grid_row == r,
                    Sensor.grid_col == c,
                    Sensor.is_active.is_(True),
                )
                .all()
            )
            if not zone_sensors:
                row.append(75.0)  # default for zones without sensors
                continue

            cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
            zone_scores = []
            for sensor in zone_sensors:
                reading = (
                    session.query(Reading)
                    .filter(
                        Reading.sensor_id == sensor.id,
                        Reading.recorded_at >= cutoff,
                    )
                    .order_by(Reading.recorded_at.desc())
                    .first()
                )
                if not reading:
                    continue
                thresholds = config.THRESHOLDS.get(sensor.sensor_type)
                if not thresholds:
                    continue
                t_min = thresholds["min"]
                t_max = thresholds["max"]
                optimal = (t_min + t_max) / 2.0
                half_range = (t_max - t_min) / 2.0
                if half_range == 0:
                    zone_scores.append(100.0)
                    continue
                deviation = abs(reading.value - optimal) / half_range
                score = max(0.0, 100.0 * (1.0 - deviation))
                zone_scores.append(score)

            if zone_scores:
                row.append(round(sum(zone_scores) / len(zone_scores), 1))
            else:
                row.append(75.0)
        grid.append(row)
    return grid

"""API endpoint tests for AgriWatch."""

import json


def test_list_fields(client):
    """GET /api/fields returns a JSON list."""
    resp = client.get("/api/fields")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_create_field(client):
    """POST /api/fields creates a new field."""
    payload = {
        "name": "API Test Field",
        "crop_type": "wheat",
        "size_hectares": 3.5,
        "grid_rows": 2,
        "grid_cols": 2,
    }
    resp = client.post("/api/fields", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "API Test Field"
    assert data["crop_type"] == "wheat"


def test_get_field(client):
    """GET /api/fields/:id returns the field."""
    # Create one first
    create = client.post("/api/fields", json={"name": "GetMe", "crop_type": "corn"})
    field_id = create.get_json()["id"]
    resp = client.get(f"/api/fields/{field_id}")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "GetMe"


def test_update_field(client):
    """PUT /api/fields/:id updates the field."""
    create = client.post("/api/fields", json={"name": "Before", "crop_type": "rice"})
    field_id = create.get_json()["id"]
    resp = client.put(f"/api/fields/{field_id}", json={"name": "After"})
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "After"


def test_delete_field(client):
    """DELETE /api/fields/:id removes the field."""
    create = client.post("/api/fields", json={"name": "DeleteMe", "crop_type": "corn"})
    field_id = create.get_json()["id"]
    resp = client.delete(f"/api/fields/{field_id}")
    assert resp.status_code == 200
    # Verify gone
    get_resp = client.get(f"/api/fields/{field_id}")
    assert get_resp.status_code == 404


def test_create_sensor(client):
    """POST /api/sensors creates a new sensor."""
    field_resp = client.post("/api/fields", json={"name": "SensorField", "crop_type": "corn"})
    field_id = field_resp.get_json()["id"]
    payload = {
        "name": "Temp Sensor",
        "sensor_type": "temperature",
        "field_id": field_id,
        "grid_row": 0,
        "grid_col": 0,
    }
    resp = client.post("/api/sensors", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["sensor_type"] == "temperature"


def test_list_readings(client):
    """GET /api/readings returns a list."""
    resp = client.get("/api/readings")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_dashboard_summary(client):
    """GET /api/dashboard/summary returns aggregated data."""
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_fields" in data
    assert "total_sensors" in data
    assert "active_sensors" in data

# AgriWatch

[![CI](https://github.com/username/agriwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/username/agriwatch/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

**IoT Agricultural Monitoring Platform** -- Sensor data collection, crop prediction, and field zone mapping for modern farming.

---

## Overview

AgriWatch is a comprehensive IoT agricultural monitoring platform built with Flask. It provides real-time sensor data visualization, crop yield predictions, and field health mapping to help farmers and agronomists make data-driven decisions.

### Key Features

- **Real-time Sensor Monitoring** -- Track temperature, humidity, soil moisture, pH, and light intensity from IoT sensors deployed across your fields
- **Diurnal Pattern Simulation** -- Realistic sensor data simulation following natural day/night cycles with appropriate noise and correlation
- **Crop Yield Prediction** -- Estimate expected yields using regression models based on sensor history and environmental conditions
- **Growth Stage Tracking** -- Monitor crop development using Growing Degree Days (GDD) to determine the current growth stage
- **Field Zone Mapping** -- Grid-based field visualization with color-coded health scores for each zone
- **Alert System** -- Automatic alerts when sensor readings fall outside optimal ranges (too dry, too hot, pH imbalance, etc.)
- **REST API** -- Full API access for all operations, enabling integration with other farm management tools
- **Interactive Dashboard** -- At-a-glance farm overview with gauge widgets, time-series charts, and health indicators

---

## Screenshots

| Dashboard | Sensor Monitoring | Crop Predictions |
|-----------|-------------------|------------------|
| Farm overview with health scores | Real-time gauge widgets | Growth stage tracking |

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/username/agriwatch.git
cd agriwatch

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at `http://localhost:8003`

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t agriwatch .
docker run -p 8003:8003 agriwatch
```

### Using the start script

```bash
chmod +x start.sh
./start.sh
```

---

## Architecture

```
agriwatch/
├── app.py                  # Flask entry point and application factory
├── config.py               # Configuration constants and thresholds
├── models/
│   ├── database.py         # SQLite/SQLAlchemy setup
│   └── schemas.py          # ORM models (Field, Sensor, Reading, CropPrediction)
├── routes/
│   ├── api.py              # REST API endpoints
│   └── views.py            # HTML-serving routes
├── services/
│   ├── sensors.py          # Sensor simulation and data ingestion
│   └── prediction.py       # Crop yield and growth stage prediction
├── templates/              # Jinja2 HTML templates
├── static/
│   ├── css/style.css       # Earth-tone agricultural theme
│   └── js/main.js          # Charts, gauges, and interactivity
├── tests/                  # Pytest test suite
└── seed_data/data.json     # Sample farm configuration
```

---

## API Reference

### Fields

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/fields` | List all fields |
| GET | `/api/fields/:id` | Get field details |
| POST | `/api/fields` | Create a new field |
| PUT | `/api/fields/:id` | Update a field |
| DELETE | `/api/fields/:id` | Delete a field |

### Sensors

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sensors` | List sensors (filter by `field_id`) |
| GET | `/api/sensors/:id` | Get sensor details |
| POST | `/api/sensors` | Create a new sensor |

### Readings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/readings` | List recent readings |
| POST | `/api/readings/ingest` | Ingest a sensor reading |
| POST | `/api/readings/simulate/:field_id` | Simulate readings for a field |
| GET | `/api/readings/history/:sensor_id` | Get sensor time-series data |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | List active alerts |

### Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/predictions/:field_id` | Get latest prediction |
| POST | `/api/predictions/:field_id/generate` | Generate new prediction |
| GET | `/api/predictions/:field_id/zones` | Get zone health grid |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary` | Aggregated dashboard data |

---

## Sensor Simulation

AgriWatch includes a realistic sensor simulation engine that generates data following natural patterns:

- **Temperature**: Sinusoidal diurnal cycle peaking at ~14:00, minimum at ~05:00
- **Humidity**: Inversely correlated with temperature (higher at night)
- **Soil Moisture**: Gradual decrease over time between watering events, with midday evaporation effects
- **pH**: Minor random fluctuation around a base value
- **Light**: Bell curve during daylight hours (6:00-20:00), near-zero at night

### Sensor Thresholds

| Sensor | Min | Max | Unit |
|--------|-----|-----|------|
| Temperature | 5.0 | 40.0 | C |
| Humidity | 30.0 | 90.0 | % |
| Soil Moisture | 20.0 | 80.0 | % |
| pH | 5.5 | 7.5 | pH |
| Light | 100 | 100,000 | lux |

---

## Crop Prediction Model

### Growing Degree Days (GDD)

GDD = max(0, (T_max + T_min) / 2 - T_base)

Each crop has a base temperature and GDD thresholds for growth stage transitions:

| Crop | Base Temp (C) | Total GDD to Harvest |
|------|---------------|---------------------|
| Corn | 10.0 | 1,600 |
| Wheat | 4.4 | 1,700 |
| Soybean | 10.0 | 1,400 |
| Rice | 10.0 | 1,500 |
| Tomato | 10.0 | 1,300 |
| Potato | 7.0 | 1,150 |

### Growth Stages

1. Germination
2. Seedling
3. Vegetative
4. Flowering
5. Fruit Development
6. Maturity
7. Harvest Ready

### Yield Prediction

```
yield = baseline * (0.6 + 0.4 * health_factor) * (0.7 + 0.3 * growth_factor)
```

Where:
- `health_factor` = normalized health score from recent sensor readings
- `growth_factor` = growth progress (accumulated GDD / total GDD needed)

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_services.py -v
```

---

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGRIWATCH_PORT` | `8003` | Server port |
| `AGRIWATCH_DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///...` | Database connection string |
| `SECRET_KEY` | `agriwatch-dev-key` | Flask secret key |

---

## Technology Stack

- **Backend**: Python 3.10+ / Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: HTML5 Canvas API
- **Containerization**: Docker / Docker Compose
- **CI/CD**: GitHub Actions
- **Testing**: pytest

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Database powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- Inspired by precision agriculture and IoT farming practices

---

*AgriWatch -- Cultivating data-driven agriculture.*

"""Application configuration for AgriWatch."""

import os

# Server
HOST = "0.0.0.0"
PORT = int(os.environ.get("AGRIWATCH_PORT", 8003))
DEBUG = os.environ.get("AGRIWATCH_DEBUG", "false").lower() == "true"

# Database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "instance", "agriwatch.db")
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
)

# Application
APP_NAME = "AgriWatch"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "IoT Agricultural Monitoring Platform"

# Sensor thresholds for alerts
THRESHOLDS = {
    "temperature": {"min": 5.0, "max": 40.0, "unit": "°C"},
    "humidity": {"min": 30.0, "max": 90.0, "unit": "%"},
    "soil_moisture": {"min": 20.0, "max": 80.0, "unit": "%"},
    "ph": {"min": 5.5, "max": 7.5, "unit": "pH"},
    "light": {"min": 100.0, "max": 100000.0, "unit": "lux"},
}

# Crop growth stages
GROWTH_STAGES = [
    "Germination",
    "Seedling",
    "Vegetative",
    "Flowering",
    "Fruit Development",
    "Maturity",
    "Harvest Ready",
]

# Growing degree day base temperatures by crop (°C)
GDD_BASE_TEMPS = {
    "corn": 10.0,
    "wheat": 4.4,
    "soybean": 10.0,
    "rice": 10.0,
    "tomato": 10.0,
    "potato": 7.0,
    "cotton": 15.6,
    "sunflower": 6.0,
}

# GDD thresholds for growth stage transitions (cumulative)
GDD_STAGE_THRESHOLDS = {
    "corn": [50, 200, 500, 800, 1100, 1400, 1600],
    "wheat": [100, 300, 600, 900, 1200, 1500, 1700],
    "soybean": [50, 200, 450, 700, 950, 1200, 1400],
    "rice": [50, 200, 500, 800, 1100, 1350, 1500],
    "tomato": [50, 200, 450, 700, 900, 1100, 1300],
    "potato": [50, 150, 400, 600, 800, 1000, 1150],
    "cotton": [60, 250, 550, 850, 1200, 1500, 1800],
    "sunflower": [50, 200, 450, 700, 950, 1150, 1300],
}

# Yield potential (tonnes/hectare) baseline
YIELD_BASELINES = {
    "corn": 9.5,
    "wheat": 3.5,
    "soybean": 3.0,
    "rice": 4.5,
    "tomato": 60.0,
    "potato": 40.0,
    "cotton": 2.0,
    "sunflower": 2.5,
}

# Seed data
SEED_DATA_PATH = os.path.join(BASE_DIR, "seed_data", "data.json")

# Testing
TESTING = False

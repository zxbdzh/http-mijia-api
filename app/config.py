"""Configuration management for http-mijia-api."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory for storing auth files
DATA_DIR = os.environ.get("MIJIA_DATA_DIR", str(BASE_DIR / "data"))
AUTH_FILE = os.path.join(DATA_DIR, "auth.json")
AUTH_DIR = os.path.join(DATA_DIR, "mijia_auth")

# Server configuration
HOST = os.environ.get("MIJIA_HOST", "0.0.0.0")
PORT = int(os.environ.get("MIJIA_PORT", "8080"))
DEBUG = os.environ.get("MIJIA_DEBUG", "false").lower() == "true"

# Logging
LOG_LEVEL = os.environ.get("MIJIA_LOG_LEVEL", "INFO")

# CORS - allow all origins by default for development
CORS_ORIGINS = os.environ.get("MIJIA_CORS_ORIGINS", "*").split(",")

# Ensure data directory exists
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

"""Load configuration from environment variables."""
from os import getenv

DB_HOST = getenv("DB_HOST", "localhost")
DB_NAME = getenv("DB_NAME", "ai_testing")
DB_USER = getenv("DB_USER", "postgres")
DB_PW = getenv("DB_PW", "postgres")
SERVICE_PORT = int(getenv("SERVICE_PORT", "8080"))
DB_PORT = int(getenv("DB_PORT", "5432"))

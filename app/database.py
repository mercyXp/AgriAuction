"""Database configuration for AgriAuction.

Phase 1 only stores connection settings from environment variables.
The live MySQL connection (get_db / close_db) is added in Phase 7.
Passwords must never be hard-coded; they come from .env or Railway.
"""

import os


def load_db_config():
    """Read MySQL settings from the environment."""
    return {
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": int(os.getenv("DB_PORT", "3306")),
        "DB_NAME": os.getenv("DB_NAME", "agriauction"),
        "DB_USER": os.getenv("DB_USER", "agriauction_app"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
    }

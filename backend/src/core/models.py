# backend/src/core/models.py
from utils.logger import logger

# SQL table creation statement
BIT_EVENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS bit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bit_position TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration REAL NOT NULL
    )
"""

def initialize_tables(cursor):
    """Initialize database tables."""
    cursor.execute(BIT_EVENTS_TABLE)
    logger.info("Table 'bit_events' initialized from models.py")
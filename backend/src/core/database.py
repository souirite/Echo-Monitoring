# backend/src/core/database.py
import sqlite3
from pathlib import Path
from ..utils.logger import logger
from .config import DB_PATH
from .models import initialize_tables  # Import table setup

class Database:
    def __init__(self, db_path=DB_PATH):
        """Initialize SQLite database connection."""
        self.db_path = Path(__file__).parent.parent.parent / db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        initialize_tables(self.cursor)  # Use models.py to create tables
        self.conn.commit()
        logger.info(f"SQLite database initialized at {self.db_path}")

    def save_bit_event(self, bit_position, start_time, end_time, duration):
        """Save a bit event to the database."""
        try:
            self.cursor.execute("""
                INSERT INTO bit_events (bit_position, start_time, end_time, duration)
                VALUES (?, ?, ?, ?)
            """, (bit_position, start_time.isoformat(), end_time.isoformat(), duration))
            self.conn.commit()
            logger.debug(f"Saved event for {bit_position} to database")
        except sqlite3.Error as e:
            logger.error(f"Database error saving event: {str(e)}")
            raise

    def close(self):
        """Close the database connection."""
        self.conn.close()
        logger.info("SQLite connection closed")
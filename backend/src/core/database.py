# backend/src/core/database.py
import sqlite3
from pathlib import Path
from ..utils.logger import logger
from .config import DB_PATH
from .models import initialize_tables

class Database:
    def __init__(self, db_path=DB_PATH):
        """Initialize SQLite database connection."""
        # Resolve path from backend/ directory explicitly
        backend_dir = Path(__file__).parent.parent.parent  # Should be backend/
        self.db_path = backend_dir / db_path  # e.g., backend/data/bit_events.db
        logger.debug(f"Resolved database path: {self.db_path}")
        
        self.db_path.parent.mkdir(exist_ok=True)  # Create data/ if it doesn’t exist
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        initialize_tables(self.cursor)
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
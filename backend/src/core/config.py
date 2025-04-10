import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Root at backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # From src/core/ to backend/
PLC_IP = os.getenv("PLC_IP")
PLC_RACK = int(os.getenv("PLC_RACK"))
PLC_SLOT = int(os.getenv("PLC_SLOT"))
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "data/bit_events.db")  # Resolve relative to backend/
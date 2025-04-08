import os
from dotenv import load_dotenv

load_dotenv()
PLC_IP = os.getenv("PLC_IP")
PLC_RACK = int(os.getenv("PLC_RACK"))
PLC_SLOT = int(os.getenv("PLC_SLOT"))
DB_PATH = os.getenv("DB_PATH", "data/bit_events.db")  # Should be relative to backend/
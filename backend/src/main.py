# backend/src/main.py
import sys
import os

# Get the directory of main.py (backend/src/)
src_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_root)
# backend/src/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from core.plc_connection import PLCConnection
import sqlite3
import json
from core.config import DB_PATH
from utils.logger import logger
import asyncio
from contextlib import asynccontextmanager
from typing import List
from starlette.websockets import WebSocketDisconnect

# Load alarm map
with open("backend/data/alarm_map.json", "r") as f:
    ALARM_MAP = json.load(f)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
            await self.send_plc_state(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_plc_state(self, websocket: WebSocket):
        """Send current PLC state to a specific client"""
        try:
            if plc.monitor and plc.monitor.bit_states:
                bits = [
                    {"position": f"DB{plc.monitor.db_number}.{plc.monitor.start_byte + (idx // 8)}.{idx % 8}", 
                     "state": state["state"],
                     "description": ALARM_MAP.get(f"DB{plc.monitor.db_number}.DBX{plc.monitor.start_byte + (idx // 8)}.{idx % 8}", "Unknown Fault")
                    }
                    for idx, state in plc.monitor.bit_states.items()
                ]
                message = json.dumps({"type": "plc_update", "data": bits})
                logger.debug(f"Sending to client: {message}")
            else:
                message = json.dumps({"type": "plc_update", "data": []})
                logger.debug("Sending empty state to client")
            await websocket.send_text(message)
        except (WebSocketDisconnect, RuntimeError) as e:
            logger.error(f"Error sending to client: {str(e)}")
            await self.disconnect(websocket)

    async def broadcast_plc_state(self):
        """Broadcast current PLC state to all connected clients"""
        async with self._lock:
            if not self.active_connections:
                logger.debug("No active connections to broadcast to")
                return
            disconnected = []
            if plc.monitor and plc.monitor.bit_states:
                bits = [
                    {"position": f"DB{plc.monitor.db_number}.{plc.monitor.start_byte + (idx // 8)}.{idx % 8}", 
                     "state": state["state"],
                     "description": ALARM_MAP.get(f"DB{plc.monitor.db_number}.DBX{plc.monitor.start_byte + (idx // 8)}.{idx % 8}", "Unknown Fault")
                    }
                    for idx, state in plc.monitor.bit_states.items()
                ]
                message = json.dumps({"type": "plc_update", "data": bits})
            else:
                message = json.dumps({"type": "plc_update", "data": []})
            logger.debug(f"Broadcasting: {message}")

            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except (WebSocketDisconnect, RuntimeError) as e:
                    logger.error(f"Broadcast error to client: {str(e)}")
                    disconnected.append(connection)
            
            for connection in disconnected:
                self.active_connections.remove(connection)
                logger.info(f"Removed disconnected client. Total: {len(self.active_connections)}")

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.debug("Lifespan startup initiated")
        plc.connect()
        plc.start_monitoring(db_number=1020, start_byte=0, end_byte=59, poll_interval=1.0)
        logger.info("Application started with monitoring")
        yield
    except Exception as e:
        logger.error(f"Lifespan startup error: {str(e)}")
        raise  # Re-raise to ensure Uvicorn logs the issue
    finally:
        logger.debug("Lifespan shutdown initiated")
        plc.stop_monitoring()
        plc.disconnect()
        logger.info("Application shut down")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

plc = PLCConnection()
@app.get("/records")
async def get_records():
    try:
        logger.debug(f"Attempting to connect to database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        logger.debug("Executing SELECT query on bit_events")
        cursor.execute("SELECT * FROM bit_events ORDER BY end_time DESC")
        rows = cursor.fetchall()
        logger.debug(f"Fetched {len(rows)} rows from bit_events")
        conn.close()
        return [{"id": r[0], 
                 "bit_position": r[1], 
                 "start_time": r[2], 
                 "end_time": r[3], 
                 "duration": r[4],
                 "description": ALARM_MAP.get(r[1], "Unknown Fault")
                 } 
                 for r in rows
                 ]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_records: {str(e)}")
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in get_records: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}
@app.websocket("/ws/bits")
async def websocket_bits(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        logger.debug("Entering WebSocket loop")
        while True:
            await manager.broadcast_plc_state()
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected by client")
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket loop error: {str(e)}")
        await manager.disconnect(websocket)
    finally:
        logger.debug("Exiting WebSocket handler")

@app.get("/test-plc")
async def test_plc():
    try:
        data = plc.read_data(1020, 20, 41)
        bit_states = {}
        for byte_offset in range(41):
            for bit_offset in range(8):
                bit_index = (byte_offset * 8) + bit_offset
                state = (data[byte_offset] >> bit_offset) & 1
                bit_states[f"DB1020.{20 + byte_offset}.{bit_offset}"] = state
        logger.debug(f"Manual PLC read: {bit_states}")
        return bit_states
    except Exception as e:
        logger.error(f"PLC read error: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
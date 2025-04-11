# backend/src/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from core.plc_connection import PLCConnection
import json
from utils.logger import logger
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict
from starlette.websockets import WebSocketDisconnect
import sqlite3
from core.config import DB_PATH
from starlette.exceptions import HTTPException

# Load alarm map
with open("backend/data/All_alarm_map.json", "r") as f:
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

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    def _get_all_station_bits(self) -> List[Dict]:
        all_bits = []
        for db_number, monitor in plc.monitors.items():
            if monitor and monitor.bit_states:
                bits = [
                    {
                        "position": f"DB{db_number}.DBX{monitor.start_byte + (idx // 8)}.{idx % 8}",
                        "state": state["state"],
                        "description": ALARM_MAP.get(f"DB{db_number}.DBX{monitor.start_byte + (idx // 8)}.{idx % 8}", "Unknown Fault")
                    }
                    for idx, state in monitor.bit_states.items()
                ]
                all_bits.extend(bits)
        return all_bits

    async def broadcast_plc_state(self):
        async with self._lock:
            if not self.active_connections:
                print("No active connections to broadcast to")
                return
            all_bits = self._get_all_station_bits()
            message = json.dumps({"type": "plc_update", "data": all_bits})
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except (WebSocketDisconnect, RuntimeError) as e:
                    print(f"Send error: {e}")
                    disconnected.append(connection)
            for connection in disconnected:
                self.active_connections.remove(connection)

manager = ConnectionManager()
plc = PLCConnection()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    return conn

async def broadcast_task():
    while True:
        await manager.broadcast_plc_state()
        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
       plc.connect()
        # Monitor all 11 stations (DB1020 to DB11020)
       for station_num in range(1, 12):  # 1 to 11 inclusive
           db_number = 1020 + (station_num - 1) * 1000
           plc.start_monitoring(db_number=db_number, start_byte=0, end_byte=59, poll_interval=1.0)
       asyncio.create_task(broadcast_task())
       yield
    finally:
        plc.stop_monitoring()
        plc.disconnect()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8080"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/records")
async def get_records():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bit_events ORDER BY timestamp DESC")
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        logger.info(f"Fetched {len(records)} records from database")
        return records
    except Exception as e:
        logger.error(f"Error fetching records: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch records")
    
@app.websocket("/ws/bits")
async def websocket_bits(websocket: WebSocket):
    print("WebSocket endpoint entered")
    try:
        await manager.connect(websocket)
        print("WebSocket connected successfully")
        # Keep connection alive
        while True:
            await websocket.receive_text()  # Wait for client messages (optional)
    except WebSocketDisconnect:
        print("WebSocket disconnected by client")
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        logger.error(f"WebSocket error: {str(e)}")
        await manager.disconnect(websocket)
    finally:
        print("Exiting WebSocket handler")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
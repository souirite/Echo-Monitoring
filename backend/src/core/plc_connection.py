# backend/core/plc_connection.py
import snap7
from snap7.util import *
import asyncio
from typing import Dict
from utils.logger import logger

class PLCMonitor:
    def __init__(self):
        self.bit_states = {}
        self.running = False
        self.db_number = None
        self.start_byte = None
        self.end_byte = None

    async def monitor(self, client, db_number, start_byte, end_byte, poll_interval):
        self.db_number = db_number
        self.start_byte = start_byte
        self.end_byte = end_byte
        while self.running:
            try:
                if not client.get_connected():
                    logger.warning(f"PLC disconnected for DB{db_number}, attempting reconnect...")
                    client.connect('192.168.5.1', 0, 1)
                    if client.get_connected():
                        logger.info(f"Reconnected to PLC for DB{db_number}")
                    else:
                        logger.error(f"Failed to reconnect for DB{db_number}")
                        await asyncio.sleep(5)  # Wait before retry
                        continue
                data = client.db_read(db_number, start_byte, end_byte - start_byte + 1)
                logger.debug(f"Read {len(data)} bytes from DB{db_number}")
                new_bit_states = {}
                for byte_idx, byte in enumerate(data):
                    for bit_idx in range(8):
                        bit_value = bool(byte & (1 << (7 - bit_idx)))  # MSB-first
                        new_bit_states[byte_idx * 8 + bit_idx] = {"state": bit_value}
                self.bit_states = new_bit_states
                await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f"Monitoring error for DB{db_number}: {str(e)}")
                await asyncio.sleep(poll_interval)  # Avoid tight loop on error

class PLCConnection:
    def __init__(self):
        self.client = snap7.client.Client()
        self.monitors: Dict[int, PLCMonitor] = {}

    def connect(self):
        try:
            logger.info("creating snap7 client")
            self.client.connect('192.168.5.1', 0, 1)  # Adjust IP if needed
            if self.client.get_connected():
                logger.info("Connected to PLC")
            else:
                logger.error("Failed to connect to PLC")
        except Exception as e:
            logger.error(f"PLC connection failed: {str(e)}")

    def disconnect(self):
        self.client.disconnect()
        logger.info("Disconnected from PLC")

    def start_monitoring(self, db_number, start_byte, end_byte, poll_interval):
        if db_number not in self.monitors:
            self.monitors[db_number] = PLCMonitor()
            self.monitors[db_number].running = True
            asyncio.create_task(
                self.monitors[db_number].monitor(self.client, db_number, start_byte, end_byte, poll_interval)
            )
            logger.info(f"Started monitoring DB{db_number}")
        else:
            logger.warning(f"Monitor for DB{db_number} already running")

    def stop_monitoring(self):
        for monitor in self.monitors.values():
            monitor.running = False
        self.monitors.clear()
        logger.info("Stopped all monitoring")
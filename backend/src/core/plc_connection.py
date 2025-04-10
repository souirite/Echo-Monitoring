# backend/src/core/plc_connection.py
import snap7
import threading
from utils.logger import logger
from .config import PLC_IP, PLC_RACK, PLC_SLOT
from .monitor import BitMonitor

class PLCConnection:
    def __init__(self, ip_address=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT):
        self.ip_address = ip_address
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.connected = False
        self.monitor = None
        self.monitoring_thread = None
        self._stop_event = threading.Event()

    def connect(self):
        try:
            if not self.connected:
                self.client.connect(self.ip_address, self.rack, self.slot)
                self.connected = True
                logger.info(f"Connected to PLC at {self.ip_address}")
        except Exception as e:
            logger.error(f"Failed to connect to PLC: {str(e)}")
            self.connected = False
            raise

    def disconnect(self):
        try:
            self.stop_monitoring()
            if self.connected:
                self.client.disconnect()
                self.connected = False
                logger.info(f"Disconnected from PLC at {self.ip_address}")
        except Exception as e:
            logger.error(f"Failed to disconnect: {str(e)}")
            raise

    def is_connected(self):
        return self.connected and self.client.get_connected()

    def read_data(self, db_number, start_byte, size):
        try:
            if not self.is_connected():
                self.connect()
            data = self.client.db_read(db_number, start_byte, size)
            logger.debug(f"Read {size} bytes from DB{db_number} at {start_byte}")
            return data
        except Exception as e:
            logger.error(f"Error reading data: {str(e)}")
            raise

    def write_data(self, db_number, start_byte, data):
        try:
            if not self.is_connected():
                self.connect()
            self.client.db_write(db_number, start_byte, data)
            logger.info(f"Data written to DB{db_number} at {start_byte}")
        except Exception as e:
            logger.error(f"Error writing data: {str(e)}")
            raise

    def start_monitoring(self, db_number, start_byte, end_byte, poll_interval=1.0):
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring is already running")
            return
        self.monitor = BitMonitor(self, db_number, start_byte, end_byte, poll_interval)
        self._stop_event.clear()
        self.monitoring_thread = threading.Thread(
            target=self.monitor.monitor_task,
            args=(self._stop_event,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Monitoring thread started")

    def stop_monitoring(self):
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self._stop_event.set()
            self.monitoring_thread.join()
            self.monitor = None
            logger.info("Monitoring thread stopped")
        else:
            logger.info("No active monitoring thread to stop")
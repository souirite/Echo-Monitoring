# backend/src/core/monitor.py
import time
from datetime import datetime
from utils.logger import logger
from .database import Database

class BitMonitor:
    def __init__(self, plc_connection, db_number, start_byte, end_byte, poll_interval=1.0):
        self.plc = plc_connection
        self.db = None
        self.db_number = db_number
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.poll_interval = poll_interval
        self.size = end_byte - start_byte + 1
        self.bit_states = {}
        self._stop_event = None

        for byte_offset in range(self.size):
            for bit_offset in range(8):
                bit_index = (byte_offset * 8) + bit_offset
                self.bit_states[bit_index] = {'state': 0, 'start_time': None}

    def get_bit(self, data, byte_offset, bit_offset):
        byte = data[byte_offset]
        return (byte >> bit_offset) & 1

    def _is_database_ready(self):
        try:
            self.db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bit_events'")
            return self.db.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking database readiness: {str(e)}")
            return False

    def monitor_task(self, stop_event):
        self._stop_event = stop_event
        self.db = Database()
        logger.info(f"Starting bit monitoring on DB{self.db_number}, bytes {self.start_byte}-{self.end_byte} in background")

        if not self._is_database_ready():
            logger.warning("Database table 'bit_events' not found. Proceeding without saving events.")

        while not self._stop_event.is_set():
            try:
                data = self.plc.read_data(self.db_number, self.start_byte, self.size)

                for byte_offset in range(self.size):
                    for bit_offset in range(8):
                        bit_index = (byte_offset * 8) + bit_offset
                        current_state = self.get_bit(data, byte_offset, bit_offset)
                        prev_state = self.bit_states[bit_index]['state']

                        if current_state != prev_state:
                            bit_position = f"DB{self.db_number}.DBX{self.start_byte + byte_offset}.{bit_offset}"
                            if current_state == 1:
                                self.bit_states[bit_index]['state'] = 1
                                self.bit_states[bit_index]['start_time'] = datetime.now()
                                logger.info(f"Bit {bit_position} turned ON at {self.bit_states[bit_index]['start_time']}")
                            else:
                                start_time = self.bit_states[bit_index]['start_time']
                                end_time = datetime.now()
                                duration = (end_time - start_time).total_seconds() if start_time else 0
                                self.bit_states[bit_index]['state'] = 0
                                self.bit_states[bit_index]['start_time'] = None
                                logger.info(f"Bit {bit_position} turned OFF at {end_time}, duration: {duration:.2f}s")
                                if self._is_database_ready():
                                    self.db.save_bit_event(bit_position, start_time, end_time, duration)
                                else:
                                    logger.warning(f"Skipping save for {bit_position} due to database issue")

                logger.debug(f"Current bit states: {self.bit_states}")
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Monitoring error in background task: {str(e)}")
                break
        
        if self.db:
            self.db.close()
        logger.info("Background monitoring stopped")